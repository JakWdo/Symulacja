/**
 * Language Toggle Component
 *
 * Dropdown menu for switching between available languages (PL/EN).
 * Syncs language preference with localStorage and persists across sessions.
 */

import { Languages } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useLanguage } from '@/i18n/hooks';
import { LANGUAGES, type Language } from '@/i18n/types';

export function LanguageToggle() {
  const { language, changeLanguage } = useLanguage();

  const handleLanguageChange = async (newLanguage: Language) => {
    await changeLanguage(newLanguage);
    // Optional: Sync with backend (PUT /settings/profile)
    // This can be done later when user is logged in
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9">
          <Languages className="h-4 w-4" />
          <span className="sr-only">Toggle language</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {Object.entries(LANGUAGES).map(([code, config]) => (
          <DropdownMenuItem
            key={code}
            onClick={() => handleLanguageChange(code as Language)}
            className={language === code ? 'bg-accent' : ''}
          >
            <span className="mr-2">{config.flag}</span>
            <span>{config.nativeName}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
