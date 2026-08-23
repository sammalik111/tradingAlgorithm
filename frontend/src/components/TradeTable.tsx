import type { CanonicalTrade } from "../api/types";

export function TradeTable({ trades }: { trades: CanonicalTrade[] }) {
  return (
    <table className="trade-table">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Type</th>
          <th>Transaction date</th>
          <th>Amount range</th>
          <th>Sources</th>
        </tr>
      </thead>
      <tbody>
        {trades.map((trade) => (
          <tr key={trade.id}>
            <td>{trade.ticker}</td>
            <td className={`transaction-${trade.transaction_type}`}>{trade.transaction_type}</td>
            <td>{trade.transaction_date}</td>
            <td>
              ${trade.amount_min.toLocaleString()} - ${trade.amount_max.toLocaleString()}
            </td>
            <td>{trade.source_count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
