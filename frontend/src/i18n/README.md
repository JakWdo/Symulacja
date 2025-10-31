# i18n - Internationalization

Comprehensive internationalization setup for the Sight Market Research SaaS platform with support for Polish (PL) and English (EN).

## Structure

```
i18n/
├── index.ts              # i18next configuration
├── types.ts              # TypeScript type definitions
├── hooks.ts              # Custom React hooks
├── README.md             # This file
└── locales/
    ├── pl/               # Polish translations
    │   ├── common.json
    │   ├── auth.json
    │   ├── settings.json
    │   ├── dashboard.json
    │   ├── projects.json
    │   ├── personas.json
    │   ├── surveys.json
    │   └── focus-groups.json
    └── en/               # English translations
        ├── common.json
        ├── auth.json
        ├── settings.json
        ├── dashboard.json
        ├── projects.json
        ├── personas.json
        ├── surveys.json
        └── focus-groups.json
```

## Namespaces

- **common**: Shared UI elements (buttons, labels, navigation)
- **auth**: Authentication pages (login, register)
- **settings**: Settings page
- **dashboard**: Dashboard page
- **projects**: Projects module
- **personas**: Personas module
- **surveys**: Surveys module
- **focusGroups**: Focus groups module

## Usage

### Basic Translation

```tsx
import { useTranslation } from '@/i18n/hooks';

function MyComponent() {
  const { t } = useTranslation('common');

  return <button>{t('button.save')}</button>;
}
```

### Multiple Namespaces

```tsx
import { useNamespacedTranslation } from '@/i18n/hooks';

function AuthPage() {
  const { t, tCommon } = useNamespacedTranslation('auth');

  return (
    <>
      <h1>{t('login.title')}</h1>
      <button>{tCommon('button.submit')}</button>
    </>
  );
}
```

### Language Switching

```tsx
import { useLanguage } from '@/i18n/hooks';

function LanguageSwitcher() {
  const { language, changeLanguage } = useLanguage();

  return (
    <select value={language} onChange={(e) => changeLanguage(e.target.value)}>
      <option value="pl">Polski</option>
      <option value="en">English</option>
    </select>
  );
}
```

### Check Current Language

```tsx
import { useIsLanguage } from '@/i18n/hooks';

function LocalizedContent() {
  const isPolish = useIsLanguage('pl');

  return <div>{isPolish ? 'Treść PL' : 'EN Content'}</div>;
}
```

## Adding New Translations

### 1. Add to JSON files

Add the key-value pair to both `pl` and `en` JSON files:

**pl/common.json**:
```json
{
  "button": {
    "save": "Zapisz",
    "cancel": "Anuluj",
    "delete": "Usuń"
  }
}
```

**en/common.json**:
```json
{
  "button": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete"
  }
}
```

### 2. Use in components

```tsx
const { t } = useTranslation('common');
<button>{t('button.save')}</button>
```

## Best Practices

1. **Consistent Keys**: Keep the same structure in both PL and EN files
2. **Namespaces**: Use appropriate namespaces for better organization
3. **Nested Keys**: Use nested objects for related translations
4. **No Hardcoded Strings**: Always use translations, never hardcode text
5. **Common First**: Put shared translations in `common.json`
6. **Placeholders**: Use interpolation for dynamic values

### Interpolation Example

**JSON**:
```json
{
  "welcome": "Witaj, {{name}}!"
}
```

**Component**:
```tsx
t('welcome', { name: 'Jan' }) // "Witaj, Jan!"
```

### Pluralization Example

**JSON**:
```json
{
  "items": "{{count}} element",
  "items_plural": "{{count}} elementów"
}
```

**Component**:
```tsx
t('items', { count: 1 }) // "1 element"
t('items', { count: 5 }) // "5 elementów"
```

## Language Detection

The application automatically detects the user's language preference:

1. **localStorage** - Previously selected language
2. **Browser** - Browser's language setting
3. **Fallback** - Polish (pl) as default

The selected language is persisted in `localStorage` under the key `i18nextLng`.

## Type Safety

TypeScript types are provided for:

- `Language`: 'pl' | 'en'
- `Namespace`: Available translation namespaces
- `LanguageConfig`: Language metadata

Use helper functions from `types.ts`:

```tsx
import { getLanguageConfig, isValidLanguage } from '@/i18n/types';

const config = getLanguageConfig('pl');
console.log(config.nativeName); // "Polski"

if (isValidLanguage('pl')) {
  // Type-safe language code
}
```

## Troubleshooting

### Missing translations

If you see a translation key instead of text:

1. Check if the key exists in the JSON file
2. Verify the namespace is correct
3. Ensure the i18n instance is initialized (see main.tsx)
4. Check browser console for warnings (DEV mode only)

### Language not changing

1. Clear localStorage: `localStorage.removeItem('i18nextLng')`
2. Hard refresh the browser (Cmd+Shift+R / Ctrl+Shift+R)
3. Check if the language switch function is called correctly

### TypeScript errors

1. Ensure JSON files are properly formatted
2. Check imports in `index.ts`
3. Rebuild TypeScript: `npm run build`

## Contributing

When adding new features:

1. Add translations to **both** PL and EN JSON files
2. Use descriptive, hierarchical keys
3. Test language switching
4. Update this README if adding new namespaces

## Resources

- [i18next Documentation](https://www.i18next.com/)
- [react-i18next Documentation](https://react.i18next.com/)
- [i18next Browser Language Detector](https://github.com/i18next/i18next-browser-languageDetector)
