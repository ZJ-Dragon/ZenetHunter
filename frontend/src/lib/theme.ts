export type ThemeMode = 'light' | 'dark' | 'system';

export const THEME_STORAGE_KEY = 'theme';

const THEME_QUERY = '(prefers-color-scheme: dark)';

const isThemeMode = (value: string | null): value is ThemeMode =>
  value === 'light' || value === 'dark' || value === 'system';

const resolveTheme = (mode: ThemeMode): 'light' | 'dark' => {
  if (mode === 'system') {
    return window.matchMedia(THEME_QUERY).matches ? 'dark' : 'light';
  }

  return mode;
};

export const getStoredTheme = (): ThemeMode => {
  const value = localStorage.getItem(THEME_STORAGE_KEY);
  return isThemeMode(value) ? value : 'system';
};

export const applyTheme = (mode: ThemeMode) => {
  const resolved = resolveTheme(mode);
  const root = document.documentElement;

  root.dataset.themeMode = mode;
  root.dataset.theme = resolved;
  root.classList.toggle('dark', resolved === 'dark');
};

export const applyStoredTheme = () => {
  applyTheme(getStoredTheme());
};

export const subscribeToSystemTheme = (listener: () => void) => {
  const mediaQuery = window.matchMedia(THEME_QUERY);
  const handler = () => listener();

  mediaQuery.addEventListener('change', handler);

  return () => {
    mediaQuery.removeEventListener('change', handler);
  };
};
