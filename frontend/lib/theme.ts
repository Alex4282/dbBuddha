import { createTheme, Theme } from "@mui/material/styles";

export type ColorMode = "light" | "dark";

// Design tokens — the "need-to-know / clearance badge" system, one set per
// color scheme. Same hues (brass "clearance" gold, brick "denied" red, the
// four role colors) carried across light/dark so badges/citations read the
// same regardless of theme; only backgrounds/text/borders invert.
const darkTokens = {
  ink: "#10151C",
  panel: "#171E27",
  hairline: "#2A3341",
  textPrimary: "#E8EDF2",
  textMuted: "#8A96A3",
  clearance: "#C9A15C",
  denied: "#B85C5C",
  role: { dev: "#5B8DBE", management: "#C9A15C", hr: "#8B7CB5", admin: "#6FA287" },
};

const lightTokens = {
  ink: "#F4F2EC", // page background — warm ivory, not stark white
  panel: "#FFFFFF",
  hairline: "#DCD6C8",
  textPrimary: "#1A1F26",
  textMuted: "#5B6472",
  clearance: "#9C6F2E", // darkened for contrast against light surfaces
  denied: "#A6433F",
  role: { dev: "#3E6690", management: "#9C6F2E", hr: "#6C5A9E", admin: "#4F8065" },
};

export function getTokens(mode: ColorMode) {
  return mode === "dark" ? darkTokens : lightTokens;
}

declare module "@mui/material/styles" {
  interface Palette {
    clearance: Palette["primary"];
    roleColors: { dev: string; management: string; hr: string; admin: string };
  }
  interface PaletteOptions {
    clearance?: PaletteOptions["primary"];
    roleColors?: { dev: string; management: string; hr: string; admin: string };
  }
}

export function createAppTheme(mode: ColorMode): Theme {
  const tokens = getTokens(mode);

  return createTheme({
    palette: {
      mode,
      background: { default: tokens.ink, paper: tokens.panel },
      divider: tokens.hairline,
      primary: { main: tokens.clearance, contrastText: mode === "dark" ? tokens.ink : "#FFFFFF" },
      error: { main: tokens.denied },
      text: { primary: tokens.textPrimary, secondary: tokens.textMuted },
      clearance: { main: tokens.clearance, contrastText: mode === "dark" ? tokens.ink : "#FFFFFF" },
      roleColors: tokens.role,
    },
    shape: { borderRadius: 8 },
    typography: {
      fontFamily: "var(--font-body), sans-serif",
      h1: { fontFamily: "var(--font-display), sans-serif" },
      h2: { fontFamily: "var(--font-display), sans-serif" },
      h3: { fontFamily: "var(--font-display), sans-serif" },
      h4: { fontFamily: "var(--font-display), sans-serif" },
      h5: { fontFamily: "var(--font-display), sans-serif", fontWeight: 600 },
      h6: { fontFamily: "var(--font-display), sans-serif", fontWeight: 600 },
      subtitle1: { fontFamily: "var(--font-display), sans-serif", fontWeight: 600 },
      subtitle2: { fontFamily: "var(--font-display), sans-serif", fontWeight: 600 },
      button: { textTransform: "none", fontWeight: 600 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: { backgroundColor: tokens.ink, color: tokens.textPrimary },
        },
      },
      MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: {
          root: { backgroundImage: "none", border: `1px solid ${tokens.hairline}` },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: { borderRadius: 6 },
          contained: { boxShadow: "none", "&:hover": { boxShadow: "none" } },
        },
      },
      MuiTextField: {
        defaultProps: { size: "small" },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: { backgroundColor: tokens.panel },
          notchedOutline: { borderColor: tokens.hairline },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { borderRadius: 6, fontFamily: "var(--font-mono), monospace", fontSize: 10 },
        },
      },
      MuiDivider: {
        styleOverrides: { root: { borderColor: tokens.hairline } },
      },
    },
  });
}
