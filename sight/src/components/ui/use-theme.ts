import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    // Check localStorage first
    const storedTheme = localStorage.getItem('theme') as Theme;
    if (storedTheme) {
      setTheme(storedTheme);
      updateDocumentClass(storedTheme);
    } else {
      // Check system preference
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const initialTheme = systemPrefersDark ? 'dark' : 'light';
      setTheme(initialTheme);
      updateDocumentClass(initialTheme);
    }
  }, []);

  const updateDocumentClass = (newTheme: Theme) => {
    const root = document.documentElement;
    if (newTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    updateDocumentClass(newTheme);
  };

  const setThemeMode = (newTheme: Theme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    updateDocumentClass(newTheme);
  };

  return {
    theme,
    toggleTheme,
    setTheme: setThemeMode,
  };
}