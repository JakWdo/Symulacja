/**
 * MessageList - Wyświetla listę wiadomości w konwersacji
 *
 * Redesigned zgodnie z Sight Design System:
 * - Brand colors zamiast hardcoded blue
 * - Consistent rounded corners (rounded-[8px])
 * - Icons z lucide-react
 * - Proper text colors (foreground, muted-foreground)
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
  streamingMessage?: string; // NEW: Partial message being streamed
}

export const MessageList: React.FC<Props> = ({
  messages,
  isLoading = false,
  streamingMessage = '',
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingMessage]);

  return (
    <div className="space-y-4">
      {messages.map((message) => {
        const isUser = message.role === 'user';
        const isSystem = message.role === 'system';

        // System messages (małe, subtle)
        if (isSystem) {
          return (
            <div key={message.id} className="flex justify-center">
              <div className="bg-muted/50 text-muted-foreground text-sm px-4 py-2 rounded-full border border-border">
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
                <AvatarFallback className="bg-brand/10 text-brand">
                  <Bot className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
            )}

            {/* Message Card */}
            <Card
              className={`p-4 max-w-[80%] rounded-[8px] ${
                isUser
                  ? 'bg-brand text-white border-brand'
                  : 'bg-background border-border'
              }`}
            >
              {isUser ? (
                // User messages - plain text
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
              ) : (
                // Assistant messages - markdown
                <div className="prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-li:text-foreground">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              )}

              {/* Timestamp */}
              <p
                className={`text-xs mt-2 ${
                  isUser ? 'text-white/70' : 'text-muted-foreground'
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
                <AvatarFallback className="bg-brand text-white">
                  <User className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        );
      })}

      {/* Streaming message (partial response) */}
      {isLoading && streamingMessage && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-10 h-10 flex-shrink-0">
            <AvatarFallback className="bg-brand/10 text-brand">
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>

          <Card className="p-4 bg-background border-border rounded-[8px]">
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{streamingMessage}</ReactMarkdown>
              {/* Blinking cursor */}
              <span className="inline-block w-2 h-4 bg-brand animate-pulse ml-1" />
            </div>
          </Card>
        </div>
      )}

      {/* Loading indicator (gdy streaming message pusty) */}
      {isLoading && !streamingMessage && (
        <div className="flex gap-3 justify-start">
          <Avatar className="w-10 h-10 flex-shrink-0">
            <AvatarFallback className="bg-brand/10 text-brand">
              <Bot className="w-5 h-5" />
            </AvatarFallback>
          </Avatar>

          <Card className="p-4 bg-background border-border rounded-[8px]">
            <div className="flex items-center gap-2 text-muted-foreground">
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
