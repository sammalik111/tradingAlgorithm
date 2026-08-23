import { useState } from "react";
import { TradeTable } from "../components/TradeTable";
import { useTrades } from "../hooks/useTrades";

export function Trades() {
  const [ticker, setTicker] = useState("");
  const { data: trades, loading, error } = useTrades({ ticker: ticker || undefined });

  return (
    <div>
      <input
        placeholder="Filter by ticker (e.g. NVDA)"
        value={ticker}
        onChange={(event) => setTicker(event.target.value.toUpperCase())}
      />
      {loading && <p>Loading trades...</p>}
      {error && <p className="error">Failed to load trades: {error.message}</p>}
      {trades && <TradeTable trades={trades} />}
    </div>
  );
}
