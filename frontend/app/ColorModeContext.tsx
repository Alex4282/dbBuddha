"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { ColorMode } from "@/lib/theme";

const STORAGE_KEY = "nexusmind_color_mode";

interface ColorModeContextValue {
  mode: ColorMode;
  toggle: () => void;
}

const ColorModeContext = createContext<ColorModeContextValue>({ mode: "dark", toggle: () => {} });

export function useColorMode() {
  return useContext(ColorModeContext);
}

export default function ColorModeProvider({ children }: { children: React.ReactNode }) {
  // Server and first client render must match, so start with the fixed
  // default and only read localStorage/system preference after mount.
  const [mode, setMode] = useState<ColorMode>("dark");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as ColorMode | null;
    if (stored === "light" || stored === "dark") {
      setMode(stored);
    } else if (window.matchMedia("(prefers-color-scheme: light)").matches) {
      setMode("light");
    }
  }, []);

  const value = useMemo(
    () => ({
      mode,
      toggle: () =>
        setMode((prev) => {
          const next = prev === "dark" ? "light" : "dark";
          window.localStorage.setItem(STORAGE_KEY, next);
          return next;
        }),
    }),
    [mode]
  );

  return <ColorModeContext.Provider value={value}>{children}</ColorModeContext.Provider>;
}
