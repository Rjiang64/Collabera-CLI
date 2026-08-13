// Entry point -- the first code that runs. Wraps the whole app in the "providers"
// every component depends on, in the right nesting order.
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { AuthProvider } from "./context/AuthContext";
import App from "./App";

// A Material-UI theme -- sets the app's primary color and design tokens.
const theme = createTheme({
  palette: { mode: "light", primary: { main: "#1f4e79" } },
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {/* ThemeProvider makes the MUI theme available to all components */}
    <ThemeProvider theme={theme}>
      {/* CssBaseline resets browser default styles for a consistent look */}
      <CssBaseline />
      {/* BrowserRouter enables client-side navigation (URLs without page reloads) */}
      <BrowserRouter>
        {/* AuthProvider exposes login state to the whole app */}
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>
);
