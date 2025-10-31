import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translations - Common
import commonPL from './locales/pl/common.json';
import commonEN from './locales/en/common.json';

// Import translations - Auth
import authPL from './locales/pl/auth.json';
import authEN from './locales/en/auth.json';

// Import translations - Settings
import settingsPL from './locales/pl/settings.json';
import settingsEN from './locales/en/settings.json';

// Import translations - Dashboard
import dashboardPL from './locales/pl/dashboard.json';
import dashboardEN from './locales/en/dashboard.json';

// Import translations - Projects
import projectsPL from './locales/pl/projects.json';
import projectsEN from './locales/en/projects.json';

// Import translations - Personas
import personasPL from './locales/pl/personas.json';
import personasEN from './locales/en/personas.json';

// Import translations - Surveys
import surveysPL from './locales/pl/surveys.json';
import surveysEN from './locales/en/surveys.json';

// Import translations - Focus Groups
import focusGroupsPL from './locales/pl/focus-groups.json';
import focusGroupsEN from './locales/en/focus-groups.json';

/**
 * i18next Configuration
 *
 * Configures internationalization for the Sight application with support for Polish and English.
 * Uses browser language detection and localStorage for persistence.
 */
i18n
  .use(LanguageDetector) // Automatically detect user language
  .use(initReactI18next) // Pass i18n instance to react-i18next
  .init({
    resources: {
      pl: {
        common: commonPL,
        auth: authPL,
        settings: settingsPL,
        dashboard: dashboardPL,
        projects: projectsPL,
        personas: personasPL,
        surveys: surveysPL,
        focusGroups: focusGroupsPL,
      },
      en: {
        common: commonEN,
        auth: authEN,
        settings: settingsEN,
        dashboard: dashboardEN,
        projects: projectsEN,
        personas: personasEN,
        surveys: surveysEN,
        focusGroups: focusGroupsEN,
      },
    },

    // Default language if detection fails
    fallbackLng: 'pl',

    // Default namespace to use
    defaultNS: 'common',

    // Available namespaces
    ns: [
      'common',
      'auth',
      'settings',
      'dashboard',
      'projects',
      'personas',
      'surveys',
      'focusGroups',
    ],

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Language detection configuration
    detection: {
      // Order of detection methods
      order: ['localStorage', 'navigator'],

      // Cache user language in localStorage
      caches: ['localStorage'],

      // LocalStorage key name
      lookupLocalStorage: 'i18nextLng',
    },

    // Development options
    debug: import.meta.env.DEV, // Enable debug logs in development

    // Missing translation handling
    saveMissing: true,
    missingKeyHandler: (lng, ns, key) => {
      if (import.meta.env.DEV) {
        console.warn(`Missing translation: [${lng}][${ns}] ${key}`);
      }
    },

    // Return empty string for missing keys instead of the key itself
    returnEmptyString: false,

    // Support for plural forms
    pluralSeparator: '_',

    // Context separator for variations (e.g., key_male, key_female)
    contextSeparator: '_',
  });

export default i18n;
