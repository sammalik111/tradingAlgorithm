import { fetchRecommendations } from "../api/recommendations";
import { useAsyncData } from "./useAsyncData";

export function useRecommendations(ticker?: string) {
  return useAsyncData(() => fetchRecommendations(ticker), [ticker]);
}
