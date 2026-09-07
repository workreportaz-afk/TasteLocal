import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import zh from "./locales/zh.json";
import ms from "./locales/ms.json";

i18n
  .use(LanguageDetector) // picks up a previously-saved choice or the browser's language
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      zh: { translation: zh },
      ms: { translation: ms },
    },
    fallbackLng: "en",
    interpolation: {
      escapeValue: false, // React already escapes output, so this isn't needed here
    },
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"], // remembers the user's choice across visits
    },
  });

// Keep <html lang="..."> in sync with the selected language. This doesn't
// change browser-chrome text (file picker buttons, native date pickers --
// those follow the OS/browser's own locale, not the page), but it's still
// correct practice: screen readers use it for pronunciation, and CSS
// :lang() selectors and hyphenation rely on it.
function syncHtmlLang(lng) {
  document.documentElement.lang = lng;
}
syncHtmlLang(i18n.language);
i18n.on("languageChanged", syncHtmlLang);

export default i18n;
