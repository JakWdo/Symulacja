/**
 * Language Selector Component
 *
 * Button-based language selector for Settings page.
 * Displays language options as clickable buttons with flag and native name.
 */

import { Button } from '@/components/ui/button';
import { useLanguage } from '@/i18n/hooks';
import { LANGUAGES, type Language } from '@/i18n/types';

export function LanguageSelector() {
  const { language, changeLanguage } = useLanguage();

  const handleLanguageChange = async (newLanguage: Language) => {
    await changeLanguage(newLanguage);
    // Optional: Sync with backend (PUT /settings/profile)
    // This will be handled by the Settings component
  };

  return (
    <div className="flex gap-2">
      {Object.entries(LANGUAGES).map(([code, config]) => (
        <Button
          key={code}
          variant={language === code ? 'default' : 'outline'}
          onClick={() => handleLanguageChange(code as Language)}
          className="flex items-center gap-2"
        >
          <span>{config.flag}</span>
          <span>{config.nativeName}</span>
        </Button>
      ))}
    </div>
  );
}
