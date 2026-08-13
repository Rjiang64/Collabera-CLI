// Theme -- the app's single source of truth for colors, corners, and shadows.
//
// WHY a separate file: main.jsx only needs to say "use this theme". Keeping the
// design tokens here means a color change happens in ONE place instead of being
// hunted down across every page.
import { createTheme } from "@mui/material";

// The two brand colors everything else is built from.
export const NAVY = "#1f4e79";       // headers, primary buttons, the balance card
export const NAVY_DARK = "#163a5c";  // the darker end of the balance-card gradient
export const GOLD = "#c9a227";       // accents: highlights, the alert strip
export const CREAM = "#fbf3e0";      // background of the gold alert strip
export const PAGE_BG = "#eef2f7";    // the light blue-grey behind every page

// Reusable card look: soft border + a very light shadow, no heavy outlines.
export const cardSx = {
  borderRadius: 3,
  border: "1px solid #e3e9f0",
  boxShadow: "0 1px 3px rgba(16, 42, 67, 0.06)",
};

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: NAVY, dark: NAVY_DARK, light: "#2f6ba3" },
    secondary: { main: GOLD, dark: "#a8871c", light: "#e3c35a" },
    background: { default: PAGE_BG, paper: "#ffffff" },
    text: { primary: "#16334f", secondary: "#5b6b7d" },
    divider: "#e3e9f0",
  },

  shape: { borderRadius: 12 },

  typography: {
    fontFamily: '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", sans-serif',
    h4: { fontWeight: 800, letterSpacing: "-0.5px" },
    h5: { fontWeight: 700, letterSpacing: "-0.3px" },
    h6: { fontWeight: 700 },
    subtitle2: { fontWeight: 600 },
    button: { fontWeight: 700 },
  },

  components: {
    // Every Card in the app picks up the shared look automatically.
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: "1px solid #e3e9f0",
          boxShadow: "0 1px 3px rgba(16, 42, 67, 0.06)",
        },
      },
    },
    // Buttons: no SHOUTING CAPS, slightly rounded, no drop shadow.
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { textTransform: "none", borderRadius: 10, paddingInline: 18 },
      },
    },
    // Rounded, white input fields to match the search box in the design.
    MuiOutlinedInput: {
      styleOverrides: {
        root: { borderRadius: 10, backgroundColor: "#fff" },
      },
    },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 12 } } },
  },
});

export default theme;
