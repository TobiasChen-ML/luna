import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, ArrowLeft, Settings, Loader2, Users } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAuth } from '@/contexts/AuthContext';
import { groupChatService } from '@/services/groupChatService';
import { characterService } from '@/services/characterService';
import { GroupMessageBubble } from '@/components/chat/GroupMessageBubble';
import { ParticipantSelector } from '@/components/chat/ParticipantSelector';
import type { Message, GroupChatSession } from '@/types/chat';
import { getSafeAvatarUrl } from '@/utils/avatarUrlGuard';

export function GroupChatPage() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [session, setSession] = useState<GroupChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [loading, setLoading] = useState(!!sessionId);
  const [showParticipantSelector, setShowParticipantSelector] = useState(!sessionId);
  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([]);
  const [characterData, setCharacterData] = useState<Record<string, { name: string; avatar_url?: string }>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    selectedParticipants.forEach((id) => {
      if (!characterData[id]) {
        loadCharacterData(id);
      }
    });
  }, [selectedParticipants]);

  const loadSession = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      const sessionData = await groupChatService.getSession(sessionId);
      setSession(sessionData);
      setSelectedParticipants(sessionData.participants);

      const { messages: msgs } = await groupChatService.getMessages(sessionId);
      setMessages(msgs.map(normalizeMessage));

      sessionData.participants.forEach((id) => loadCharacterData(id));
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCharacterData = async (characterId: string) => {
    try {
      const char = await characterService.getCharacterById(characterId);
      const raw = char as unknown as Record<string, unknown>;
      const name =
        (typeof raw.name === 'string' && raw.name) ||
        (typeof raw.first_name === 'string' && raw.first_name) ||
        'Unknown';
      const avatarUrl =
        (typeof raw.avatar_url === 'string' && raw.avatar_url) ||
        (typeof raw.profile_image_url === 'string' && raw.profile_image_url) ||
        undefined;
      setCharacterData((prev) => ({
        ...prev,
        [characterId]: {
          name,
          avatar_url: avatarUrl,
        },
      }));
    } catch (error) {
      console.error('Failed to load character:', error);
    }
  };

  const normalizeMessage = (msg: any): Message => ({
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: msg.created_at || msg.timestamp,
    character_id: msg.character_id,
    speaker_id: msg.speaker_id,
  });

  const handleStartSession = async () => {
    if (selectedParticipants.length < 2 || !user) return;

    try {
      setLoading(true);
      const newSession = await groupChatService.createSession(selectedParticipants);
      setSession(newSession);
      navigate(`/chat/group/${newSession.id}`);
      setShowParticipantSelector(false);
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming || !session) return;

    const messageText = inputValue.trim();
    setInputValue('');
    setIsStreaming(true);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/chat/group/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          session_id: session.id,
          participants: selectedParticipants,
          message: messageText,
        }),
        signal: abortControllerRef.current.signal,
      });

      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = '';

      const userMessage: Message = {
        id: `user_${Date.now()}`,
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      const pendingResponses: Record<string, { content: string; speaker_name?: string }> = {};

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);

              if (parsed.speaker_id) {
                if (!pendingResponses[parsed.speaker_id]) {
                  pendingResponses[parsed.speaker_id] = { content: '' };
                }

                if (parsed.content) {
                  pendingResponses[parsed.speaker_id].content += parsed.content;
                  pendingResponses[parsed.speaker_id].speaker_name = parsed.speaker_name;
                }
              }
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      Object.entries(pendingResponses).forEach(([speakerId, response]) => {
        if (response.content) {
          const aiMessage: Message = {
            id: `ai_${speakerId}_${Date.now()}`,
            role: 'assistant',
            content: response.content,
            speaker_id: speakerId,
            speaker_name: response.speaker_name || characterData[speakerId]?.name,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, aiMessage]);
        }
      });
    } catch (error: any) {
      if (error.name === 'AbortError') return;
      console.error('Stream error:', error);
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (loading && sessionId) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-zinc-900/90 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <ArrowLeft size={20} className="text-zinc-400" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-white">
              {session ? 'Group Chat' : 'New Group Chat'}
            </h1>
            {selectedParticipants.length > 0 && (
              <p className="text-xs text-zinc-400">
                {selectedParticipants.length} participants
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex -space-x-2">
            {selectedParticipants.slice(0, 5).map((id) => {
              const char = characterData[id];
              return (
                <div
                  key={id}
                  className="w-8 h-8 rounded-full bg-zinc-700 border-2 border-zinc-900 overflow-hidden"
                >
                  {char?.avatar_url ? (
                    <img
                      src={getSafeAvatarUrl(char.avatar_url)}
                      alt={char?.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-zinc-400">
                      {char?.name?.charAt(0) || '?'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button
            onClick={() => setShowParticipantSelector(!showParticipantSelector)}
            className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <Users size={20} className="text-zinc-400" />
          </button>
        </div>
      </header>

      {/* Participant Selector Modal */}
      {showParticipantSelector && (
        <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-zinc-900 rounded-xl p-6 border border-zinc-800">
            <ParticipantSelector
              selectedIds={selectedParticipants}
              onSelectionChange={setSelectedParticipants}
              maxParticipants={5}
            />
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowParticipantSelector(false)}
                className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (session) {
                    setShowParticipantSelector(false);
                  } else {
                    handleStartSession();
                  }
                }}
                disabled={selectedParticipants.length < 2}
                className="px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {session ? 'Apply' : 'Start Chat'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-zinc-500">
            <Users size={48} className="mb-4 opacity-50" />
            <p>Select participants and start a group conversation</p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <GroupMessageBubble
                key={msg.id}
                message={msg}
                characterAvatars={Object.fromEntries(
                  Object.entries(characterData).map(([id, data]) => [id, data.avatar_url || ''])
                )}
                characterNames={Object.fromEntries(
                  Object.entries(characterData).map(([id, data]) => [id, data.name])
                )}
              />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-zinc-400 text-sm px-4">
                <Loader2 size={16} className="animate-spin" />
                <span>Generating responses...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-3 bg-zinc-900/90 border-t border-zinc-800">
        <div className="flex items-center gap-3">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isStreaming || selectedParticipants.length < 2}
            rows={1}
            className="flex-1 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder:text-zinc-500 focus:outline-none focus:border-purple-500 resize-none disabled:opacity-50"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isStreaming || selectedParticipants.length < 2}
            className={cn(
              'p-3 rounded-xl transition-all',
              inputValue.trim() && !isStreaming
                ? 'bg-gradient-primary text-white hover:opacity-90'
                : 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
            )}
          >
            {isStreaming ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
}
