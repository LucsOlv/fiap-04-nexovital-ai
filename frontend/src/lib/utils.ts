// Utilitário padrão do shadcn/ui para compor classes condicionalmente.
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
