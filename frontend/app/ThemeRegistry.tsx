"use client";

import { AppRouterCacheProvider } from "@mui/material-nextjs/v14-appRouter";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { useMemo } from "react";
import { createAppTheme } from "@/lib/theme";
import ColorModeProvider, { useColorMode } from "./ColorModeContext";

function MuiThemeBridge({ children }: { children: React.ReactNode }) {
  const { mode } = useColorMode();
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  return (
    <AppRouterCacheProvider options={{ key: "mui" }}>
      <ColorModeProvider>
        <MuiThemeBridge>{children}</MuiThemeBridge>
      </ColorModeProvider>
    </AppRouterCacheProvider>
  );
}
