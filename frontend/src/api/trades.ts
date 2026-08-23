import { apiGet } from "./client";
import type { CanonicalTrade } from "./types";

export function fetchTrades(params?: { ticker?: string; politicianId?: string }): Promise<CanonicalTrade[]> {
  return apiGet<CanonicalTrade[]>("/trades", {
    ...(params?.ticker ? { ticker: params.ticker } : {}),
    ...(params?.politicianId ? { politician_id: params.politicianId } : {}),
  });
}
