import { fetchTrades } from "../api/trades";
import { useAsyncData } from "./useAsyncData";

export function useTrades(params?: { ticker?: string; politicianId?: string }) {
  return useAsyncData(() => fetchTrades(params), [params?.ticker, params?.politicianId]);
}
