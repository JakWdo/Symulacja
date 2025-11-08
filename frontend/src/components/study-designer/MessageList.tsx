/**
 * MessageList - Wyświetla listę wiadomości w konwersacji
 *
 * Renderuje wiadomości user/assistant z markdown support.
 */

import React, { useRef, useEffect } from 'react';
import { Card } from '../ui/card';
import { Avatar, AvatarFallback } from '../ui/avatar';
import ReactMarkdown from 'react-markdown';
import { User, Bot, Loader2 } from 'lucide-react';
import type { Message } from '../../api/studyDesigner';

interface Props {
  messages: Message[];
  isLoading?: boolean;
}

export const MessageList: React.FC<Props> = ({ messages, isLoading = false }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <div className="space-y-4">
      {messages.map((message) => {
        const isUser = message.role === 'user';
        const isSystem = message.role === 'system';

        // System messages (małe, szare)
        if (isSystem) {
          return (
            <div key={message.id} className="flex justify-center">
              <div className="bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
                {message.content}
              </div>
            </div>
          );
        }

        return (
          <div
            key={message.id}
            className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
          >
            {/* Avatar (assistant) */}
            {!isUser && (
              <Avatar className="w-10 h-10 flex-shrink-0">
                <AvatarFallback className="bg-blue-100 text-blue-600">
                  <Bot className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
            )}

            {/* Message Card */}
            <Card
              className={`p-4 max-w-[80%] ${
                isUser
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white border-gray-200'
              }`}
            >
              {isUser ? (
                // User messages - plain text
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                // Assistant messages - markdown
                <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              {/* Timestamp */}
              <p
                className={`text-xs mt-2 ${
                  isUser ? 'text-blue-100' : 'text-gray-400'
                }`}
              >
                {new Date(message.created_at).toLocaleTimeString('pl-PL', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </Card>

            {/* Avatar (user) */}
            {isUser && (
              <Avatar className="w-10 h-10 flex-shrink-0">
                <AvatarFallback className="bg-blue-600 text-white">
                  <User className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        );
      })}

      {/* Loading indicator */}
      {isLoading && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-10 h-10 flex-shrink-0">
            <AvatarFallback className="bg-blue-100 text-blue-600">
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>

          <Card className="p-4 bg-white border-gray-200">
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm">AI analizuje Twoją odpowiedź...</span>
            </div>
          </Card>
        </div>
      )}

      {/* Auto-scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
};
