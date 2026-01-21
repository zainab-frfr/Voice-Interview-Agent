import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import ur from './ur.json';
import roman from './roman.json';

console.log('i18n file loaded');
console.log('Translations:', { en, ur, roman });

i18n.use(initReactI18next).init({
    resources: {
        en: { translation: en },
        ur: { translation: ur },
        roman: { translation: roman }
    },
    lng: "ur",
    fallbackLng: "en",
    interpolation: {
        escapeValue: false
    }
});

console.log('i18n initialized');

const root = document.documentElement;
root.classList.add('lang-urdu', 'urdu', 'light-mode', 'font-medium');

export default i18n;
