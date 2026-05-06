# Realtime Voice Calls

This module relays browser WebSocket audio to ElevenLabs Conversational AI while reusing the existing memory layer.

## Endpoint

Connect clients to:

```text
wss://<api-host>/api/realtime-voice/ws?character_id=<character_id>&session_id=<optional>&token=<firebase_id_token>
```

The client may also pass `Authorization: Bearer <firebase_id_token>` if its WebSocket stack supports custom headers.

## Audio Protocol

Client to backend:

- Binary WebSocket frames are treated as microphone audio chunks and forwarded to ElevenLabs as `user_audio_chunk` base64.
- Text JSON frames are forwarded to ElevenLabs for supported events such as `contextual_update`, `user_message`, `user_activity`, or `client_tool_result`.
- `{ "type": "stop" }` closes the upstream conversation.

Backend to client:

- ElevenLabs `audio` events are decoded and sent as binary WebSocket frames for playback.
- Transcript, agent response, VAD, interruption, metadata, and error events are sent as JSON text frames.

## Configuration

Required:

```env
ELEVENLABS_CONVAI_BASE_AGENT_ID=agent_xxx
ELEVENLABS_API_KEY=sk_xxx
```

Optional:

```env
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1
ELEVENLABS_CONVAI_USE_SIGNED_URL=false
ELEVENLABS_REALTIME_CONNECT_RETRIES=1
REALTIME_MEMORY_READ_TIMEOUT_SECONDS=3.0
```

Character-to-voice mapping can be maintained in the existing `characters.voice_id` column. If a character stores an internal `voices.id`, the manager resolves it to `voices.provider_voice_id` before sending the ElevenLabs override.

For emergency overrides without editing character rows, set `REALTIME_CHARACTER_VOICE_MAP` to a JSON object:

```json
{
  "char_001": "21m00Tcm4TlvDq8ikWAM",
  "char_002": "EXAVITQu4vr4xnSDxMaL"
}
```

The runtime priority is:

1. `REALTIME_CHARACTER_VOICE_MAP[character_id]`
2. `characters.voice_id`, resolving through the `voices` table when needed

## ElevenLabs Agent Setup

On the single Base Agent, enable override permissions for:

- System prompt
- First message
- Voice ID

The first message sent upstream is `conversation_initiation_client_data` with `conversation_config_override.agent.prompt.prompt`, `conversation_config_override.agent.first_message`, and `conversation_config_override.tts.voice_id`.
