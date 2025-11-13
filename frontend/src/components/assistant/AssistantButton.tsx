/**
 * Floating Assistant Button - prawy dolny róg
 *
 * Otwiera chat interface z Product Assistant.
 * Dostępny tylko dla zalogowanych użytkowników.
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AssistantChat } from './AssistantChat';
import { Logo } from '@/components/ui/logo';

export const AssistantButton: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-brand hover:bg-brand/90 text-white shadow-lg z-50 flex items-center justify-center transition-transform hover:scale-105"
          aria-label="Otwórz asystenta AI"
        >
          <Logo transparent className="w-7 h-7" />
        </Button>
      )}

      {/* Chat Interface */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[400px] h-[600px] bg-background border border-border rounded-[12px] shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="bg-brand text-white p-4 rounded-t-[12px] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Logo transparent className="w-5 h-5" />
              <h3 className="font-semibold">Product Assistant</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20 h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Chat Content */}
          <AssistantChat onClose={() => setIsOpen(false)} />
        </div>
      )}
    </>
  );
};
