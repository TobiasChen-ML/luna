import type { NavigateFunction } from 'react-router-dom';

import { api } from '@/services/api';

export const CHAT_LIST_REFRESH_EVENT = 'roxy:chat-list-refresh';

export async function startOfficialChat(
  navigate: NavigateFunction,
  options: {
    isAuthenticated: boolean;
    characterId: string;
  }
) {
  const { isAuthenticated, characterId } = options;
  if (!isAuthenticated) {
    navigate('/register');
    return;
  }

  const response = await api.post(`/chat/chat_now_official/${characterId}`);
  const userCharacterId = response.data?.character_id;

  if (!userCharacterId) {
    throw new Error('Missing character_id in chat_now_official response');
  }

  window.dispatchEvent(
    new CustomEvent(CHAT_LIST_REFRESH_EVENT, {
      detail: { characterId: userCharacterId },
    })
  );

  navigate(`/chat?character=${userCharacterId}&ready=1`);
}
