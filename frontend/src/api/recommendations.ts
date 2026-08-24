import { apiGet, apiPost } from "./client";
import type { OrderSide, Recommendation, RecommendationDetail, SimulatedOrder } from "./types";

export function fetchRecommendations(ticker?: string): Promise<Recommendation[]> {
  return apiGet<Recommendation[]>("/recommendations", ticker ? { ticker } : undefined);
}

export function fetchRecommendationDetail(id: string): Promise<RecommendationDetail> {
  return apiGet<RecommendationDetail>(`/recommendations/${id}`);
}

export interface SimulatedOrderInput {
  side: OrderSide;
  quantity: number;
  price: number;
}

export function submitSimulatedOrder(
  recommendationId: string,
  order: SimulatedOrderInput,
): Promise<SimulatedOrder> {
  return apiPost<SimulatedOrder>(`/recommendations/${recommendationId}/simulated-orders`, order);
}
