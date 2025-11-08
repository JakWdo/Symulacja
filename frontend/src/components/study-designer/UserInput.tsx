/**
 * UserInput - Input field + Send button
 *
 * Textarea z auto-resize i Enter to send (Shift+Enter dla newline).
 */

import React from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Send, Loader2 } from 'lucide-react';

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onKeyPress?: (e: React.KeyboardEvent) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
}

export const UserInput: React.FC<Props> = ({
  value,
  onChange,
  onSend,
  onKeyPress,
  disabled = false,
  isLoading = false,
  placeholder = 'Wpisz swoją odpowiedź...',
}) => {
  return (
    <div className="flex gap-3 items-end">
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        className="flex-1 min-h-[60px] max-h-[200px] resize-none"
        rows={2}
      />

      <Button
        onClick={onSend}
        disabled={disabled || !value.trim() || isLoading}
        className="flex-shrink-0"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Wysyłanie...
          </>
        ) : (
          <>
            <Send className="w-4 h-4 mr-2" />
            Wyślij
          </>
        )}
      </Button>
    </div>
  );
};
