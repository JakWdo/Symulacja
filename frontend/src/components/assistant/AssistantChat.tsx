/**
 * Assistant Chat Interface
 *
 * In-memory conversation (nie zapisuje w DB).
 * Używa Gemini Flash dla szybkich odpowiedzi.
 * Sugestie generowane przez LLM (inteligentne, kontekstowe).
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useSendAssistantMessage } from '@/hooks/useAssistant';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  onClose: () => void;
}

export const AssistantChat: React.FC<Props> = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Cześć! Jestem Product Assistant. Mogę pomóc Ci w nawigacji po platformie Sight. O co chciałbyś zapytać?',
    },
  ]);
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([
    'Jak wygenerować persony?',
    'Jak utworzyć grupę fokusową?',
    'Jakie są główne funkcje platformy?',
  ]);

  const scrollRef = useRef<HTMLDivElement>(null);
  const sendMessageMutation = useSendAssistantMessage();

  // Auto-scroll do dołu po nowej wiadomości
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();
    setInput('');

    // Dodaj user message
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    // Wywołaj API
    try {
      const response = await sendMessageMutation.mutateAsync({
        message: userMessage,
        conversation_history: messages.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        include_user_context: true,
      });

      // Dodaj assistant response
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.message },
      ]);

      // Aktualizuj sugestie (generowane przez LLM)
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }
    } catch (error) {
      console.error('Assistant error:', error);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Przepraszam, wystąpił błąd. Spróbuj ponownie za chwilę.',
        },
      ]);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-[8px] ${
                  msg.role === 'user'
                    ? 'bg-brand text-white'
                    : 'bg-muted text-foreground'
                }`}
              >
                {msg.role === 'assistant' && (
                  <Sparkles className="w-4 h-4 inline mr-2 text-brand" />
                )}
                <p className="text-sm leading-[20px] whitespace-pre-wrap">
                  {msg.content}
                </p>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {sendMessageMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-muted p-3 rounded-[8px]">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-brand rounded-full animate-bounce" />
                  <div
                    className="w-2 h-2 bg-brand rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                  <div
                    className="w-2 h-2 bg-brand rounded-full animate-bounce"
                    style={{ animationDelay: '0.4s' }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Suggestions (generowane przez LLM) */}
      {suggestions.length > 0 && (
        <div className="px-4 pb-2 space-y-2">
          <p className="text-xs text-muted-foreground">Sugestie:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                onClick={() => handleSuggestionClick(suggestion)}
                className="text-xs h-7 rounded-[6px]"
                disabled={sendMessageMutation.isPending}
              >
                {suggestion}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex items-end gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Zadaj pytanie..."
            className="resize-none rounded-[6px]"
            rows={2}
            disabled={sendMessageMutation.isPending}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || sendMessageMutation.isPending}
            className="bg-brand hover:bg-brand/90 text-white h-10 w-10 p-0 rounded-[6px]"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
