import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

const THEME_KEY = "nexovital-theme";
type Theme = "light" | "dark";

function initialTheme(): Theme {
  const saved = window.localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") return saved;
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function ThemeIcon({ theme }: { theme: Theme }) {
  return theme === "dark" ? (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-current"><path d="M16.8 12.7a7.4 7.4 0 0 1-9.5-9.5A7.4 7.4 0 1 0 16.8 12.7Z" /></svg>
  ) : (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="h-4 w-4 fill-current"><path d="M10 2.1a.8.8 0 0 1 .8.8v1.2a.8.8 0 1 1-1.6 0V2.9a.8.8 0 0 1 .8-.8Zm0 13.8a.8.8 0 0 1 .8.8v.4a.8.8 0 1 1-1.6 0v-.4a.8.8 0 0 1 .8-.8ZM17.1 10a.8.8 0 0 1 .8-.8h.4a.8.8 0 1 1 0 1.6h-.4a.8.8 0 0 1-.8-.8ZM1.7 10a.8.8 0 0 1 .8-.8h.4a.8.8 0 1 1 0 1.6h-.4a.8.8 0 0 1-.8-.8Zm13.3-4.4.3-.3a.8.8 0 1 1 1.1 1.1l-.3.3a.8.8 0 1 1-1.1-1.1Zm-10 10 .3-.3a.8.8 0 1 1 1.1 1.1l-.3.3a.8.8 0 1 1-1.1-1.1Zm10 0a.8.8 0 1 1 1.1-1.1l.3.3a.8.8 0 1 1-1.1 1.1l-.3-.3ZM5 5.6a.8.8 0 0 1-1.1 1.1l-.3-.3a.8.8 0 1 1 1.1-1.1l.3.3ZM10 6a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z" /></svg>
  );
}

export default function AppLayout() {
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const nextTheme = theme === "dark" ? "light" : "dark";

  return (
    <div className="min-h-screen bg-[var(--app-bg)] text-[var(--app-text)]">
      <header className="sticky top-0 z-20 border-b app-border bg-[var(--app-surface)]/95 shadow-[0_1px_8px_rgba(15,23,42,0.06)] backdrop-blur">
        <div className="flex min-h-16 items-center gap-8 px-5 lg:px-8">
          <NavLink to="/pacientes" className="flex shrink-0 items-center gap-2.5" aria-label="NexoVital AI, ir para pacientes">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-black text-white">N</span>
            <span className="text-base font-bold tracking-tight text-[var(--app-text)]">NexoVital <span className="text-brand">AI</span></span>
          </NavLink>
          <nav className="flex h-16 items-stretch gap-1" aria-label="Navegação principal">
            <NavLink to="/pacientes" className={({ isActive }) => `relative flex items-center px-4 text-sm font-semibold transition-colors ${isActive ? "text-brand after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-brand" : "app-text-muted hover:text-[var(--app-text)]"}`}>
              Pacientes
            </NavLink>
            <NavLink to="/analise" className={({ isActive }) => `relative flex items-center px-4 text-sm font-semibold transition-colors ${isActive ? "text-brand after:absolute after:inset-x-3 after:bottom-0 after:h-0.5 after:bg-brand" : "app-text-muted hover:text-[var(--app-text)]"}`}>
              Nova análise
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-xs app-text-muted xl:inline">Ambiente demonstrativo</span>
            <button type="button" onClick={() => setTheme(nextTheme)} aria-label={`Ativar tema ${nextTheme === "dark" ? "escuro" : "claro"}`} aria-pressed={theme === "dark"} className="inline-flex items-center gap-2 rounded-lg border app-border app-surface-muted px-3 py-2 text-xs font-semibold app-text-muted transition hover:text-[var(--app-text)]">
              <ThemeIcon theme={theme} />
              <span className="hidden sm:inline">{theme === "dark" ? "Escuro" : "Claro"}</span>
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1800px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Outlet />
      </main>
    </div>
  );
}
