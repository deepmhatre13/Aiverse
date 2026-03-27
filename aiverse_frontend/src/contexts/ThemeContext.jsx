import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext(undefined);

export function ThemeProvider({ children }) {
  const storageKey = 'aiverse-theme';
  const explicitKey = 'aiverse-theme-explicit';

  const [isExplicit, setIsExplicit] = useState(() => {
    try {
      return localStorage.getItem(explicitKey) === '1';
    } catch {
      return false;
    }
  });

  const [theme, setThemeState] = useState(() => {
    try {
      // Check localStorage first
      const stored = localStorage.getItem(storageKey);
      if (stored === 'dark' || stored === 'light') {
        return stored;
      }
    } catch {
      // ignore storage access issues
    }

    // Check system preference
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    
    // Remove both classes first
    root.classList.remove('light', 'dark');
    
    // Add the current theme class
    root.classList.add(theme);
    
    // Store in localStorage
    try {
      localStorage.setItem(storageKey, theme);
    } catch {
      // ignore storage access issues
    }
  }, [theme]);

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      // Only update if user hasn't manually set a preference
      if (!isExplicit) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [isExplicit]);

  const setTheme = (nextTheme) => {
    setIsExplicit(true);
    try {
      localStorage.setItem(explicitKey, '1');
    } catch {
      // ignore storage access issues
    }
    setThemeState(nextTheme);
  };

  const toggleTheme = () => {
    setIsExplicit(true);
    try {
      localStorage.setItem(explicitKey, '1');
    } catch {
      // ignore storage access issues
    }
    setThemeState(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
