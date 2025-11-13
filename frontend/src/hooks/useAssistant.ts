/**
 * Assistant React Hooks
 *
 * TanStack Query hooks dla Product Assistant API.
 */

import { useMutation } from '@tanstack/react-query';
import { sendAssistantMessage, type ChatRequest } from '@/api/assistant';

/**
 * Hook do wysyłania wiadomości do Product Assistant
 *
 * @returns Mutation object z metodą mutateAsync do wysyłania wiadomości
 *
 * @example
 * const sendMessage = useSendAssistantMessage();
 *
 * const response = await sendMessage.mutateAsync({
 *   message: "Jak wygenerować persony?",
 *   conversation_history: [],
 *   include_user_context: true
 * });
 */
export function useSendAssistantMessage() {
  return useMutation({
    mutationFn: (request: ChatRequest) => sendAssistantMessage(request),
  });
}
