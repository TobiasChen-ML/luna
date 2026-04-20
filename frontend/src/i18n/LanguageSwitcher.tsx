import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Globe } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { SUPPORTED_LANGUAGES, LANGUAGE_NAMES, SupportedLanguage } from '.';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const currentLang = i18n.language as SupportedLanguage;

  const changeLanguage = (lang: SupportedLanguage) => {
    if (lang === currentLang) return;

    const pathParts = location.pathname.split('/').filter(Boolean);
    const currentLangInPath = SUPPORTED_LANGUAGES.includes(pathParts[0] as SupportedLanguage);

    let newPath: string;
    if (currentLangInPath) {
      pathParts[0] = lang;
      newPath = '/' + pathParts.join('/');
    } else {
      if (lang === 'en') {
        newPath = location.pathname;
      } else {
        newPath = '/' + lang + location.pathname;
      }
    }

    i18n.changeLanguage(lang);
    navigate(newPath + location.search);
  };

  return (
    <Menu as="div" className="relative inline-block text-left">
      <Menu.Button className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm text-zinc-300 hover:text-white">
        <Globe className="w-4 h-4" />
        <span>{LANGUAGE_NAMES[currentLang] || 'English'}</span>
      </Menu.Button>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-40 origin-top-right rounded-lg bg-zinc-900 border border-white/10 shadow-lg focus:outline-none z-50">
          <div className="py-1">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <Menu.Item key={lang}>
                {({ active }) => (
                  <button
                    onClick={() => changeLanguage(lang)}
                    className={`w-full text-left px-4 py-2 text-sm ${
                      active ? 'bg-white/10 text-white' : 'text-zinc-300'
                    } ${lang === currentLang ? 'text-primary-500' : ''}`}
                  >
                    {LANGUAGE_NAMES[lang]}
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}
