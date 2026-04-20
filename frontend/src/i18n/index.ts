import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enAuth from './locales/en/auth.json';
import enCommon from './locales/en/common.json';
import enChat from './locales/en/chat.json';
import enCharacter from './locales/en/character.json';
import enLanding from './locales/en/landing.json';
import enSettings from './locales/en/settings.json';
import enBilling from './locales/en/billing.json';
import enNavigation from './locales/en/navigation.json';
import enProfile from './locales/en/profile.json';
import enValidation from './locales/en/validation.json';
import enErrors from './locales/en/errors.json';

import deAuth from './locales/de/auth.json';
import deCommon from './locales/de/common.json';
import deChat from './locales/de/chat.json';
import deCharacter from './locales/de/character.json';
import deLanding from './locales/de/landing.json';
import deSettings from './locales/de/settings.json';
import deBilling from './locales/de/billing.json';
import deNavigation from './locales/de/navigation.json';
import deProfile from './locales/de/profile.json';
import deValidation from './locales/de/validation.json';
import deErrors from './locales/de/errors.json';

import esAuth from './locales/es/auth.json';
import esCommon from './locales/es/common.json';
import esChat from './locales/es/chat.json';
import esCharacter from './locales/es/character.json';
import esLanding from './locales/es/landing.json';
import esSettings from './locales/es/settings.json';
import esBilling from './locales/es/billing.json';
import esNavigation from './locales/es/navigation.json';
import esProfile from './locales/es/profile.json';
import esValidation from './locales/es/validation.json';
import esErrors from './locales/es/errors.json';

import frAuth from './locales/fr/auth.json';
import frCommon from './locales/fr/common.json';
import frChat from './locales/fr/chat.json';
import frCharacter from './locales/fr/character.json';
import frLanding from './locales/fr/landing.json';
import frSettings from './locales/fr/settings.json';
import frBilling from './locales/fr/billing.json';
import frNavigation from './locales/fr/navigation.json';
import frProfile from './locales/fr/profile.json';
import frValidation from './locales/fr/validation.json';
import frErrors from './locales/fr/errors.json';

export const SUPPORTED_LANGUAGES = ['en', 'de', 'es', 'fr'] as const;
export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number];
export const DEFAULT_LANGUAGE: SupportedLanguage = 'en';
export const LANGUAGE_NAMES: Record<SupportedLanguage, string> = {
  en: 'English',
  de: 'Deutsch',
  es: 'Español',
  fr: 'Français',
};

const resources = {
  en: {
    auth: enAuth,
    common: enCommon,
    chat: enChat,
    character: enCharacter,
    landing: enLanding,
    settings: enSettings,
    billing: enBilling,
    navigation: enNavigation,
    profile: enProfile,
    validation: enValidation,
    errors: enErrors,
  },
  de: {
    auth: deAuth,
    common: deCommon,
    chat: deChat,
    character: deCharacter,
    landing: deLanding,
    settings: deSettings,
    billing: deBilling,
    navigation: deNavigation,
    profile: deProfile,
    validation: deValidation,
    errors: deErrors,
  },
  es: {
    auth: esAuth,
    common: esCommon,
    chat: esChat,
    character: esCharacter,
    landing: esLanding,
    settings: esSettings,
    billing: esBilling,
    navigation: esNavigation,
    profile: esProfile,
    validation: esValidation,
    errors: esErrors,
  },
  fr: {
    auth: frAuth,
    common: frCommon,
    chat: frChat,
    character: frCharacter,
    landing: frLanding,
    settings: frSettings,
    billing: frBilling,
    navigation: frNavigation,
    profile: frProfile,
    validation: frValidation,
    errors: frErrors,
  },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES,
    defaultNS: 'common',
    react: {
      useSuspense: false,
    },
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export { LanguageSwitcher } from './LanguageSwitcher';
export { LanguageDetector, useLanguagePrefix, useLocalizedNavigate, LocalizedLink } from './LanguageDetector';
