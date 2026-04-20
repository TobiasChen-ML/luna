/**
 * @deprecated Legacy realtime voice-call client.
 *
 * This module is kept for `legacy_voice_call` fallback only.
 * Primary chat voice path is async voice-note generation, not realtime websocket calling.
 *
 * VoiceStreamClient
 * Custom WebSocket client for real-time voice streaming
 * Uses Deepgram Voice Agent API (unified STT + LLM + TTS)
 *
 * Audio Flow:
 * - Input: Capture at native sample rate, resample to 16000Hz Linear16 PCM
 * - Output: Receive 24000Hz Linear16 PCM, play via AudioContext
 */

export interface VoiceStreamConfig {
  sessionId: string;
  token: string;
  onTranscript: (role: string, text: string, isFinal: boolean) => void;
  onAudioChunk: (audioData: ArrayBuffer) => void;
  onCallStarted: (voiceId: string, language: string) => void;
  onCallEnded: (duration: number, cost: number, newBalance: number) => void;
  onError: (error: string, errorCode?: string) => void;
  onUserSpeech?: (event: string) => void;
  onAgentSpeaking?: (isSpeaking: boolean) => void;
}

// Target sample rate for Deepgram Voice Agent
const TARGET_SAMPLE_RATE = 16000;
// Output sample rate from Deepgram TTS
const OUTPUT_SAMPLE_RATE = 24000;

export class VoiceStreamClient {
  private ws: WebSocket | null = null;
  private audioContext: AudioContext | null = null;
  private processor: ScriptProcessorNode | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private config: VoiceStreamConfig;
  private isCapturing: boolean = false;
  private stream: MediaStream | null = null;

  // Audio playback via AudioContext (for PCM)
  private playbackContext: AudioContext | null = null;
  private nextPlayTime: number = 0;
  private isPlaying: boolean = false;
  private audioQueue: Float32Array[] = [];

  constructor(config: VoiceStreamConfig) {
    this.config = config;
  }

  async connect(characterId: string): Promise<void> {
    // Get backend URL from environment variable
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8999/api';

    // Convert http/https to ws/wss
    const wsUrl = apiBaseUrl
      .replace(/^http/, 'ws')
      .replace(/\/api$/, '') + `/api/voice/ws/${this.config.sessionId}?token=${encodeURIComponent(this.config.token)}`;

    console.log('[VoiceStreamClient] Connecting to:', wsUrl);

    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('[VoiceStreamClient] WebSocket connected');

        // Send start message with character_id
        this.ws!.send(JSON.stringify({
          type: "start",
          character_id: characterId
        }));

        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[VoiceStreamClient] Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[VoiceStreamClient] WebSocket error:', error);
        this.config.onError("WebSocket connection error");
        reject(error);
      };

      this.ws.onclose = (event) => {
        console.log('[VoiceStreamClient] WebSocket closed:', event.code, event.reason);
        this.cleanup();
      };
    });
  }

  async startAudioCapture(): Promise<void> {
    try {
      // 1. Get microphone stream
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1
        }
      });

      // 2. Initialize AudioContext
      // @ts-ignore - Handle vendor prefixes
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioContextClass();

      const nativeSampleRate = this.audioContext.sampleRate;
      console.log('[VoiceStreamClient] Native sample rate:', nativeSampleRate);

      // 3. Create media stream source
      this.source = this.audioContext.createMediaStreamSource(this.stream);

      // 4. Create ScriptProcessorNode for processing
      // Buffer size determines latency: 4096 samples at 44100Hz = ~93ms
      const bufferSize = 4096;
      this.processor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);

      // 5. Handle audio processing - resample and send
      this.processor.onaudioprocess = (e) => {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !this.isCapturing) return;

        const inputData = e.inputBuffer.getChannelData(0);

        // Resample from native sample rate to 16000Hz
        const resampledData = this.resample(inputData, nativeSampleRate, TARGET_SAMPLE_RATE);

        // Convert Float32 to Int16 PCM
        const pcmData = this.float32ToInt16(resampledData);

        // Send as base64 encoded binary
        const base64Audio = this.arrayBufferToBase64(pcmData.buffer as ArrayBuffer);

        this.ws.send(JSON.stringify({
          type: "audio",
          data: base64Audio
        }));
      };

      // 6. Connect nodes
      // We need to connect to destination to keep the graph active
      const gainNode = this.audioContext.createGain();
      gainNode.gain.value = 0; // Mute local playback

      this.source.connect(this.processor);
      this.processor.connect(gainNode);
      gainNode.connect(this.audioContext.destination);

      this.isCapturing = true;
      console.log('[VoiceStreamClient] Audio capture started (resampling to 16000Hz)');

      // 7. Initialize playback context for receiving audio
      await this.initPlaybackContext();

    } catch (error) {
      console.error('[VoiceStreamClient] Error starting audio capture:', error);
      this.config.onError("Failed to access microphone. Please check permissions.");
      throw error;
    }
  }

  private async initPlaybackContext(): Promise<void> {
    try {
      // @ts-ignore
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.playbackContext = new AudioContextClass({ sampleRate: OUTPUT_SAMPLE_RATE });
      this.nextPlayTime = 0;
      console.log('[VoiceStreamClient] Playback context initialized at', OUTPUT_SAMPLE_RATE, 'Hz');
    } catch (error) {
      console.error('[VoiceStreamClient] Error initializing playback context:', error);
    }
  }

  /**
   * Resample audio from source sample rate to target sample rate
   * Using linear interpolation for simplicity
   */
  private resample(inputData: Float32Array, sourceSampleRate: number, targetSampleRate: number): Float32Array {
    if (sourceSampleRate === targetSampleRate) {
      return inputData;
    }

    const ratio = sourceSampleRate / targetSampleRate;
    const outputLength = Math.floor(inputData.length / ratio);
    const output = new Float32Array(outputLength);

    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i * ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, inputData.length - 1);
      const fraction = srcIndex - srcIndexFloor;

      // Linear interpolation
      output[i] = inputData[srcIndexFloor] * (1 - fraction) + inputData[srcIndexCeil] * fraction;
    }

    return output;
  }

  /**
   * Convert Float32 samples to Int16 PCM
   */
  private float32ToInt16(float32Array: Float32Array): Int16Array {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      // Clamp to [-1, 1]
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      // Scale to 16-bit integer range
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
  }

  /**
   * Convert Int16 PCM to Float32 samples
   */
  private int16ToFloat32(int16Array: Int16Array): Float32Array {
    const float32Array = new Float32Array(int16Array.length);
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7FFF);
    }
    return float32Array;
  }

  private handleMessage(message: any): void {
    switch (message.type) {
      case "call_started":
        console.log('[VoiceStreamClient] Call started:', message);
        this.config.onCallStarted(message.voice_id, message.language);
        break;

      case "transcript":
        // Real-time transcript from Deepgram Voice Agent
        this.config.onTranscript(message.role, message.content, message.is_final);
        break;

      case "user_speech":
        // User speech detection event (started/stopped)
        console.log('[VoiceStreamClient] User speech event:', message.event);
        if (this.config.onUserSpeech) {
          this.config.onUserSpeech(message.event);
        }
        break;

      case "audio_chunk":
        // Audio chunk from Deepgram Aura TTS (Linear16 PCM at 24000Hz)
        const audioData = this.base64ToArrayBuffer(message.data);
        this.config.onAudioChunk(audioData);
        this.playPCMAudio(audioData);

        // Notify that agent is speaking
        if (this.config.onAgentSpeaking) {
          this.config.onAgentSpeaking(true);
        }
        break;

      case "call_ended":
        console.log('[VoiceStreamClient] Call ended:', message);
        this.config.onCallEnded(
          message.duration_seconds,
          message.cost,
          message.new_balance
        );
        break;

      case "error":
        console.error('[VoiceStreamClient] Server error:', message);
        this.config.onError(message.message, message.error_code);
        break;

      default:
        console.log('[VoiceStreamClient] Message type:', message.type);
    }
  }

  /**
   * Play Linear16 PCM audio using AudioContext
   */
  private playPCMAudio(audioData: ArrayBuffer): void {
    if (!this.playbackContext) {
      console.warn('[VoiceStreamClient] No playback context available');
      return;
    }

    try {
      // Convert ArrayBuffer to Int16Array
      const int16Data = new Int16Array(audioData);

      // Convert Int16 to Float32
      const float32Data = this.int16ToFloat32(int16Data);

      // Add to queue
      this.audioQueue.push(float32Data);

      // Start playback if not already playing
      if (!this.isPlaying) {
        this.playNextChunk();
      }
    } catch (error) {
      console.error('[VoiceStreamClient] Error processing audio chunk:', error);
    }
  }

  private playNextChunk(): void {
    if (this.audioQueue.length === 0 || !this.playbackContext) {
      this.isPlaying = false;
      if (this.config.onAgentSpeaking) {
        this.config.onAgentSpeaking(false);
      }
      return;
    }

    this.isPlaying = true;
    const float32Data = this.audioQueue.shift()!;

    try {
      // Create audio buffer
      const audioBuffer = this.playbackContext.createBuffer(
        1, // mono
        float32Data.length,
        OUTPUT_SAMPLE_RATE
      );

      // Copy data to buffer
      audioBuffer.copyToChannel(new Float32Array(float32Data.buffer as ArrayBuffer), 0);

      // Create buffer source
      const source = this.playbackContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.playbackContext.destination);

      // Schedule playback
      const currentTime = this.playbackContext.currentTime;
      const startTime = Math.max(currentTime, this.nextPlayTime);

      source.start(startTime);

      // Update next play time
      this.nextPlayTime = startTime + audioBuffer.duration;

      // When this chunk ends, play next
      source.onended = () => {
        this.playNextChunk();
      };

    } catch (error) {
      console.error('[VoiceStreamClient] Error playing audio:', error);
      // Try next chunk
      this.playNextChunk();
    }
  }

  stop(): void {
    console.log('[VoiceStreamClient] Stopping voice stream');

    this.isCapturing = false;

    // Send stop message to server
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "stop" }));
    }

    // Stop microphone
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    // Cleanup will be called by WebSocket onclose
  }

  private cleanup(): void {
    console.log('[VoiceStreamClient] Cleaning up resources');

    this.isCapturing = false;
    this.isPlaying = false;
    this.audioQueue = [];

    // Stop microphone
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    // Clean up audio nodes
    if (this.processor) {
      this.processor.disconnect();
      this.processor.onaudioprocess = null;
      this.processor = null;
    }

    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }

    // Close audio contexts
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close().catch(console.error);
      this.audioContext = null;
    }

    if (this.playbackContext && this.playbackContext.state !== 'closed') {
      this.playbackContext.close().catch(console.error);
      this.playbackContext = null;
    }

    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  private base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  // Public getters for connection status
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  isRecording(): boolean {
    return this.isCapturing;
  }
}
