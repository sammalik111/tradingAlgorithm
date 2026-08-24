import { useState } from "react";
import type { FormEvent } from "react";
import { submitSimulatedOrder } from "../api/recommendations";
import type { OrderSide, RecommendationDirection, SimulatedOrder } from "../api/types";

function defaultSide(direction: RecommendationDirection): OrderSide {
  return direction === "sell" ? "sell" : "buy";
}

export function SimulatedOrderForm({
  recommendationId,
  direction,
  onOrderPlaced,
}: {
  recommendationId: string;
  direction: RecommendationDirection;
  onOrderPlaced: (order: SimulatedOrder) => void;
}) {
  const [side, setSide] = useState<OrderSide>(defaultSide(direction));
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const quantityValue = Number(quantity);
    const priceValue = Number(price);
    if (!(quantityValue > 0) || !(priceValue > 0)) {
      setError("Quantity and price must both be greater than zero.");
      return;
    }

    setSubmitting(true);
    try {
      const order = await submitSimulatedOrder(recommendationId, {
        side,
        quantity: quantityValue,
        price: priceValue,
      });
      onOrderPlaced(order);
      setQuantity("");
      setPrice("");
    } catch {
      setError("Failed to log the simulated order. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="order-form" onSubmit={handleSubmit}>
      <p className="order-form-disclaimer">
        Simulated order &mdash; this logs a paper trade only. No brokerage is connected and no
        real order is placed.
      </p>
      <div className="order-form-row">
        <label>
          Side
          <select value={side} onChange={(e) => setSide(e.target.value as OrderSide)}>
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
          </select>
        </label>
        <label>
          Quantity
          <input
            type="number"
            min="0"
            step="any"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Shares"
            required
          />
        </label>
        <label>
          Price
          <input
            type="number"
            min="0"
            step="any"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="Price per share"
            required
          />
        </label>
      </div>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Logging order..." : "Log simulated order"}
      </button>
    </form>
  );
}
