import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, beforeEach } from "vitest";

import AppLayout from "@/components/AppLayout";

describe("AppLayout theme toggle", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("toggles and persists dark theme", async () => {
    render(<MemoryRouter><AppLayout /></MemoryRouter>);
    const toggle = screen.getByRole("button", { name: /ativar tema escuro/i });

    fireEvent.click(toggle);

    await waitFor(() => expect(document.documentElement).toHaveClass("dark"));
    expect(window.localStorage.getItem("nexovital-theme")).toBe("dark");
    expect(screen.getByRole("button", { name: /ativar tema claro/i })).toBeInTheDocument();
  });
});
