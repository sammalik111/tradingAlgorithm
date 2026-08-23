import { apiGet } from "./client";
import type { Politician } from "./types";

export function fetchPoliticians(): Promise<Politician[]> {
  return apiGet<Politician[]>("/politicians");
}
