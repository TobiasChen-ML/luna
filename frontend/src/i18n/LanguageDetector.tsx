import { useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, SupportedLanguage } from '.';

export function LanguageDetector() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { lang } = useParams<{ lang?: string }>();

  useEffect(() => {
    const langInPath = lang as SupportedLanguage | undefined;
    const isValidLang = langInPath && SUPPORTED_LANGUAGES.includes(langInPath);

    if (isValidLang) {
      if (i18n.language !== langInPath) {
        i18n.changeLanguage(langInPath);
      }
    } else if (!langInPath) {
      const browserLang = navigator.language.split('-')[0];
      const detectedLang = SUPPORTED_LANGUAGES.includes(browserLang as SupportedLanguage)
        ? browserLang
        : DEFAULT_LANGUAGE;

      if (detectedLang !== DEFAULT_LANGUAGE) {
        navigate('/' + detectedLang + location.pathname + location.search, { replace: true });
      }
    }
  }, [lang, i18n, navigate, location]);

  return null;
}

export function useLanguagePrefix() {
  const { lang } = useParams<{ lang?: string }>();
  const isValidLang = lang && SUPPORTED_LANGUAGES.includes(lang as SupportedLanguage);
  return isValidLang ? `/${lang}` : '';
}

export function useLocalizedNavigate() {
  const navigate = useNavigate();
  const { lang } = useParams<{ lang?: string }>();
  const isValidLang = lang && SUPPORTED_LANGUAGES.includes(lang as SupportedLanguage);
  const prefix = isValidLang ? `/${lang}` : '';

  return (path: string, options?: { replace?: boolean }) => {
    const fullPath = prefix + path;
    navigate(fullPath, options);
  };
}

export function LocalizedLink({ to, children, ...props }: { to: string; children: React.ReactNode; [key: string]: any }) {
  const { lang } = useParams<{ lang?: string }>();
  const isValidLang = lang && SUPPORTED_LANGUAGES.includes(lang as SupportedLanguage);
  const prefix = isValidLang ? `/${lang}` : '';
  const localizedTo = prefix + to;

  return (
    <a href={localizedTo} {...props}>
      {children}
    </a>
  );
}
