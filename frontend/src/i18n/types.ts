/**
 * i18n Type Definitions
 *
 * Type-safe internationalization utilities for the Sight application.
 */

/**
 * Available language codes
 */
export type Language = 'pl' | 'en';

/**
 * Language configuration with metadata
 */
export interface LanguageConfig {
  code: Language;
  name: string;
  nativeName: string;
  flag: string;
  dir: 'ltr' | 'rtl';
}

/**
 * Available languages with metadata
 */
export const LANGUAGES: Record<Language, LanguageConfig> = {
  pl: {
    code: 'pl',
    name: 'Polish',
    nativeName: 'Polski',
    flag: '🇵🇱',
    dir: 'ltr',
  },
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇬🇧',
    dir: 'ltr',
  },
} as const;

/**
 * Available translation namespaces
 */
export type Namespace =
  | 'common'
  | 'auth'
  | 'settings'
  | 'dashboard'
  | 'projects'
  | 'personas'
  | 'surveys'
  | 'focusGroups';

/**
 * Translation key paths for type-safe translations
 * Usage: t('common:button.save') or t('auth:login.title')
 */
export type TranslationKey = `${Namespace}:${string}`;

/**
 * Helper function to get language configuration
 */
export function getLanguageConfig(code: Language): LanguageConfig {
  return LANGUAGES[code];
}

/**
 * Helper function to get all available languages
 */
export function getAvailableLanguages(): LanguageConfig[] {
  return Object.values(LANGUAGES);
}

/**
 * Check if a language code is valid
 */
export function isValidLanguage(code: string): code is Language {
  return code === 'pl' || code === 'en';
}

/**
 * Get language name in its native form
 */
export function getLanguageNativeName(code: Language): string {
  return LANGUAGES[code].nativeName;
}

/**
 * Get language flag emoji
 */
export function getLanguageFlag(code: Language): string {
  return LANGUAGES[code].flag;
}
