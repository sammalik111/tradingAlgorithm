import { apiGet } from "./client";
import type { Recommendation } from "./types";

export function fetchRecommendations(ticker?: string): Promise<Recommendation[]> {
  return apiGet<Recommendation[]>("/recommendations", ticker ? { ticker } : undefined);
}
