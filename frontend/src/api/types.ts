export type Chamber = "house" | "senate" | "executive";
export type TransactionType = "buy" | "sell" | "exchange";
export type RecommendationDirection = "buy" | "sell" | "hold";
export type ConvictionLevel = "low" | "medium" | "high";

export interface Politician {
  id: string;
  full_name: string;
  chamber: Chamber;
  party: string | null;
  state: string | null;
  is_active: boolean;
}

export interface CanonicalTrade {
  id: string;
  politician_id: string;
  ticker: string;
  asset_name: string;
  transaction_type: TransactionType;
  transaction_date: string;
  disclosure_date: string;
  amount_min: number;
  amount_max: number;
  amount_mid: number;
  source_count: number;
  first_seen_at: string;
  last_seen_at: string;
}

export interface Recommendation {
  id: string;
  ticker: string;
  generated_at: string;
  signal_score: number;
  conviction: ConvictionLevel;
  direction: RecommendationDirection;
  rationale_text: string | null;
  model_version: string;
}
