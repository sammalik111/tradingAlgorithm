import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { Recommendation } from "../api/types";
import { RecommendationCard } from "./RecommendationCard";

const BASE_RECOMMENDATION: Recommendation = {
  id: "11111111-1111-1111-1111-111111111111",
  ticker: "NVDA",
  generated_at: "2026-08-23T00:00:00Z",
  signal_score: 0.62,
  conviction: "high",
  direction: "buy",
  rationale_text: "Multiple politicians disclosed recent purchases.",
  model_version: "claude-sonnet-5",
};

describe("RecommendationCard", () => {
  it("renders the ticker, direction, and rationale", () => {
    render(
      <MemoryRouter>
        <RecommendationCard recommendation={BASE_RECOMMENDATION} />
      </MemoryRouter>,
    );

    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText(/BUY/)).toBeInTheDocument();
    expect(screen.getByText(/Multiple politicians disclosed/)).toBeInTheDocument();
  });

  it("omits the rationale paragraph when none is available", () => {
    render(
      <MemoryRouter>
        <RecommendationCard recommendation={{ ...BASE_RECOMMENDATION, rationale_text: null }} />
      </MemoryRouter>,
    );

    expect(screen.queryByText(/Multiple politicians disclosed/)).not.toBeInTheDocument();
  });

  it("links to the recommendation detail page", () => {
    render(
      <MemoryRouter>
        <RecommendationCard recommendation={BASE_RECOMMENDATION} />
      </MemoryRouter>,
    );

    const links = screen.getAllByRole("link");
    expect(links.every((link) => link.getAttribute("href") === "/recommendations/11111111-1111-1111-1111-111111111111")).toBe(true);
  });
});
