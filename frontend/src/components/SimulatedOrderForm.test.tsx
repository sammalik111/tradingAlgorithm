import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import * as recommendationsApi from "../api/recommendations";
import type { SimulatedOrder } from "../api/types";
import { SimulatedOrderForm } from "./SimulatedOrderForm";

describe("SimulatedOrderForm", () => {
  it("submits the entered quantity and price and reports the placed order", async () => {
    const placedOrder: SimulatedOrder = {
      id: "order-1",
      recommendation_id: "rec-1",
      ticker: "NVDA",
      side: "buy",
      quantity: 10,
      price: 120,
      notional_value: 1200,
      created_at: "2026-08-24T00:00:00Z",
    };
    const submitSpy = vi
      .spyOn(recommendationsApi, "submitSimulatedOrder")
      .mockResolvedValue(placedOrder);
    const onOrderPlaced = vi.fn();

    render(
      <SimulatedOrderForm recommendationId="rec-1" direction="buy" onOrderPlaced={onOrderPlaced} />,
    );

    fireEvent.change(screen.getByPlaceholderText("Shares"), { target: { value: "10" } });
    fireEvent.change(screen.getByPlaceholderText("Price per share"), {
      target: { value: "120" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log simulated order/i }));

    await waitFor(() => expect(onOrderPlaced).toHaveBeenCalledWith(placedOrder));
    expect(submitSpy).toHaveBeenCalledWith("rec-1", { side: "buy", quantity: 10, price: 120 });
  });

  it("rejects a zero quantity without calling the API", () => {
    const submitSpy = vi.spyOn(recommendationsApi, "submitSimulatedOrder");

    render(
      <SimulatedOrderForm recommendationId="rec-1" direction="buy" onOrderPlaced={vi.fn()} />,
    );

    fireEvent.change(screen.getByPlaceholderText("Shares"), { target: { value: "0" } });
    fireEvent.change(screen.getByPlaceholderText("Price per share"), {
      target: { value: "120" },
    });
    fireEvent.click(screen.getByRole("button", { name: /log simulated order/i }));

    expect(screen.getByText(/must both be greater than zero/i)).toBeInTheDocument();
    expect(submitSpy).not.toHaveBeenCalled();
  });
});
