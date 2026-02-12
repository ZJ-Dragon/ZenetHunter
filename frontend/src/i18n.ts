import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en/translation.json';
import zhCN from './locales/zh-CN/translation.json';
import jaJP from './locales/ja-JP/translation.json';
import koKR from './locales/ko-KR/translation.json';
import ruRU from './locales/ru-RU/translation.json';

const resources = {
  en: { translation: en },
  'zh-CN': { translation: zhCN },
  'ja-JP': { translation: jaJP },
  'ko-KR': { translation: koKR },
  'ru-RU': { translation: ruRU },
};

const saved = localStorage.getItem('locale') || 'en';

i18n.use(initReactI18next).init({
  resources,
  lng: saved,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
