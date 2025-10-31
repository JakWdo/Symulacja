/**
 * i18n Custom Hooks
 *
 * Custom React hooks for internationalization with type safety and convenience.
 */

import { useTranslation as useI18nextTranslation } from 'react-i18next';
import { useCallback } from 'react';
import type { Language, Namespace } from './types';

/**
 * Enhanced useTranslation hook with namespace support
 *
 * Usage:
 * ```tsx
 * const { t } = useTranslation('auth');
 * const title = t('login.title');
 * ```
 */
export function useTranslation(namespace: Namespace = 'common') {
  return useI18nextTranslation(namespace);
}

/**
 * Hook for language switching
 *
 * Usage:
 * ```tsx
 * const { language, changeLanguage } = useLanguage();
 * changeLanguage('en');
 * ```
 */
export function useLanguage() {
  const { i18n } = useI18nextTranslation();

  const changeLanguage = useCallback(
    async (lang: Language) => {
      await i18n.changeLanguage(lang);
    },
    [i18n]
  );

  return {
    language: i18n.language as Language,
    changeLanguage,
    languages: i18n.languages,
  };
}

/**
 * Hook for checking current language
 *
 * Usage:
 * ```tsx
 * const isPolish = useIsLanguage('pl');
 * ```
 */
export function useIsLanguage(lang: Language): boolean {
  const { language } = useLanguage();
  return language === lang;
}

/**
 * Hook for namespace-aware translations
 *
 * Usage:
 * ```tsx
 * const { t, tCommon } = useNamespacedTranslation('auth');
 * const title = t('login.title'); // From auth namespace
 * const saveButton = tCommon('button.save'); // From common namespace
 * ```
 */
export function useNamespacedTranslation(namespace: Namespace) {
  const { t } = useI18nextTranslation(namespace);
  const { t: tCommon } = useI18nextTranslation('common');

  return {
    t,
    tCommon,
  };
}
