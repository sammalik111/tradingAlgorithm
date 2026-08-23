import { fetchPoliticians } from "../api/politicians";
import { useAsyncData } from "./useAsyncData";

export function usePoliticians() {
  return useAsyncData(() => fetchPoliticians(), []);
}
