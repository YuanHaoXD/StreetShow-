"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { type Lang, type TranslationKey, translations } from "../lib/i18n";

type LangContextType = {
  lang: Lang;
  toggle: () => void;
  t: (key: TranslationKey) => string;
};

const LangContext = createContext<LangContextType>({
  lang: "zh",
  toggle: () => {},
  t: (key) => translations.zh[key],
});

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>("zh");

  useEffect(() => {
    const saved = localStorage.getItem("streetshow_lang") as Lang | null;
    if (saved === "en" || saved === "zh") setLang(saved);
  }, []);

  const toggle = () => {
    setLang((prev) => {
      const next = prev === "zh" ? "en" : "zh";
      localStorage.setItem("streetshow_lang", next);
      return next;
    });
  };

  const t = (key: TranslationKey): string => translations[lang][key];

  return (
    <LangContext.Provider value={{ lang, toggle, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
