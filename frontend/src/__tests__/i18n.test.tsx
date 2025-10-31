import { describe, it, expect } from 'vitest';
import i18n from '../i18n';

import plCommon from '../i18n/locales/pl/common.json';
import enCommon from '../i18n/locales/en/common.json';
import plDashboard from '../i18n/locales/pl/dashboard.json';
import enDashboard from '../i18n/locales/en/dashboard.json';
import plPersonas from '../i18n/locales/pl/personas.json';
import enPersonas from '../i18n/locales/en/personas.json';
import plProjects from '../i18n/locales/pl/projects.json';
import enProjects from '../i18n/locales/en/projects.json';
import plFocusGroups from '../i18n/locales/pl/focus-groups.json';
import enFocusGroups from '../i18n/locales/en/focus-groups.json';
import plSurveys from '../i18n/locales/pl/surveys.json';
import enSurveys from '../i18n/locales/en/surveys.json';
import plSettings from '../i18n/locales/pl/settings.json';
import enSettings from '../i18n/locales/en/settings.json';
import plAuth from '../i18n/locales/pl/auth.json';
import enAuth from '../i18n/locales/en/auth.json';
import plAnalysis from '../i18n/locales/pl/analysis.json';
import enAnalysis from '../i18n/locales/en/analysis.json';
import plRag from '../i18n/locales/pl/rag.json';
import enRag from '../i18n/locales/en/rag.json';

describe('i18n Configuration', () => {
  it('should initialize i18n properly', () => {
    expect(i18n).toBeDefined();
    expect(i18n.isInitialized).toBe(true);
  });

  it('should have correct default language', () => {
    expect(i18n.language).toBe('pl');
  });

  it('should have both pl and en languages available', () => {
    const languages = i18n.languages;
    expect(languages).toContain('pl');
    expect(languages).toContain('en');
  });

  it('should have all required namespaces', () => {
    const requiredNamespaces = [
      'common',
      'dashboard',
      'personas',
      'projects',
      'focus-groups',
      'surveys',
      'settings',
      'auth',
      'analysis',
      'rag',
      'charts',
    ];

    requiredNamespaces.forEach((ns) => {
      expect(i18n.hasResourceBundle('pl', ns)).toBe(true);
      expect(i18n.hasResourceBundle('en', ns)).toBe(true);
    });
  });
});

describe('Translation Keys Parity', () => {
  /**
   * Helper function to recursively get all keys from a nested object
   */
  function getAllKeys(obj: any, prefix = ''): string[] {
    let keys: string[] = [];

    for (const key in obj) {
      const fullKey = prefix ? `${prefix}.${key}` : key;

      if (typeof obj[key] === 'object' && obj[key] !== null && !Array.isArray(obj[key])) {
        keys = keys.concat(getAllKeys(obj[key], fullKey));
      } else {
        keys.push(fullKey);
      }
    }

    return keys;
  }

  /**
   * Helper to find missing keys between two translation objects
   */
  function findMissingKeys(source: any, target: any, namespace: string): string[] {
    const sourceKeys = getAllKeys(source).sort();
    const targetKeys = getAllKeys(target).sort();

    const missingInTarget = sourceKeys.filter(key => !targetKeys.includes(key));

    return missingInTarget.map(key => `${namespace}:${key}`);
  }

  it('should have matching keys in common namespace', () => {
    const missingInEn = findMissingKeys(plCommon, enCommon, 'common');
    const missingInPl = findMissingKeys(enCommon, plCommon, 'common');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in dashboard namespace', () => {
    const missingInEn = findMissingKeys(plDashboard, enDashboard, 'dashboard');
    const missingInPl = findMissingKeys(enDashboard, plDashboard, 'dashboard');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in personas namespace', () => {
    const missingInEn = findMissingKeys(plPersonas, enPersonas, 'personas');
    const missingInPl = findMissingKeys(enPersonas, plPersonas, 'personas');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in projects namespace', () => {
    const missingInEn = findMissingKeys(plProjects, enProjects, 'projects');
    const missingInPl = findMissingKeys(enProjects, plProjects, 'projects');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in focus-groups namespace', () => {
    const missingInEn = findMissingKeys(plFocusGroups, enFocusGroups, 'focus-groups');
    const missingInPl = findMissingKeys(enFocusGroups, plFocusGroups, 'focus-groups');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in surveys namespace', () => {
    const missingInEn = findMissingKeys(plSurveys, enSurveys, 'surveys');
    const missingInPl = findMissingKeys(enSurveys, plSurveys, 'surveys');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in settings namespace', () => {
    const missingInEn = findMissingKeys(plSettings, enSettings, 'settings');
    const missingInPl = findMissingKeys(enSettings, plSettings, 'settings');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in auth namespace', () => {
    const missingInEn = findMissingKeys(plAuth, enAuth, 'auth');
    const missingInPl = findMissingKeys(enAuth, plAuth, 'auth');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in analysis namespace', () => {
    const missingInEn = findMissingKeys(plAnalysis, enAnalysis, 'analysis');
    const missingInPl = findMissingKeys(enAnalysis, plAnalysis, 'analysis');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });

  it('should have matching keys in rag namespace', () => {
    const missingInEn = findMissingKeys(plRag, enRag, 'rag');
    const missingInPl = findMissingKeys(enRag, plRag, 'rag');

    expect(missingInEn, `Missing in EN: ${missingInEn.join(', ')}`).toHaveLength(0);
    expect(missingInPl, `Missing in PL: ${missingInPl.join(', ')}`).toHaveLength(0);
  });
});

describe('Translation Quality', () => {
  it('should not have empty translation strings in PL', () => {
    const checkEmpty = (obj: any, path = ''): string[] => {
      let emptyKeys: string[] = [];

      for (const key in obj) {
        const fullPath = path ? `${path}.${key}` : key;

        if (typeof obj[key] === 'string') {
          if (obj[key].trim() === '') {
            emptyKeys.push(fullPath);
          }
        } else if (typeof obj[key] === 'object' && obj[key] !== null) {
          emptyKeys = emptyKeys.concat(checkEmpty(obj[key], fullPath));
        }
      }

      return emptyKeys;
    };

    const allPL = {
      common: plCommon,
      dashboard: plDashboard,
      personas: plPersonas,
      projects: plProjects,
      'focus-groups': plFocusGroups,
      surveys: plSurveys,
      settings: plSettings,
      auth: plAuth,
      analysis: plAnalysis,
      rag: plRag,
    };

    Object.entries(allPL).forEach(([namespace, translations]) => {
      const emptyKeys = checkEmpty(translations);
      expect(emptyKeys, `Empty translations in ${namespace}: ${emptyKeys.join(', ')}`).toHaveLength(0);
    });
  });

  it('should not have placeholder values like "TODO" in translations', () => {
    const checkPlaceholders = (obj: any, path = ''): string[] => {
      let placeholderKeys: string[] = [];

      for (const key in obj) {
        const fullPath = path ? `${path}.${key}` : key;

        if (typeof obj[key] === 'string') {
          if (obj[key].includes('TODO') || obj[key].includes('FIXME') || obj[key].includes('XXX')) {
            placeholderKeys.push(`${fullPath}: "${obj[key]}"`);
          }
        } else if (typeof obj[key] === 'object' && obj[key] !== null) {
          placeholderKeys = placeholderKeys.concat(checkPlaceholders(obj[key], fullPath));
        }
      }

      return placeholderKeys;
    };

    const allTranslations = {
      'pl.common': plCommon,
      'en.common': enCommon,
      'pl.dashboard': plDashboard,
      'en.dashboard': enDashboard,
      'pl.focus-groups': plFocusGroups,
      'en.focus-groups': enFocusGroups,
    };

    Object.entries(allTranslations).forEach(([namespace, translations]) => {
      const placeholders = checkPlaceholders(translations);
      expect(placeholders, `Placeholders found in ${namespace}: ${placeholders.join(', ')}`).toHaveLength(0);
    });
  });
});
