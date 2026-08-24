import { fetchRecommendationDetail } from "../api/recommendations";
import { useAsyncData } from "./useAsyncData";

/** `refreshKey` lets a caller force a refetch (e.g. after submitting a
 * simulated order) by bumping it -- `useAsyncData` re-runs whenever any dep
 * changes.
 */
export function useRecommendationDetail(id: string, refreshKey = 0) {
  return useAsyncData(() => fetchRecommendationDetail(id), [id, refreshKey]);
}
