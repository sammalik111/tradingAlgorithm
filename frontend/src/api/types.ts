export type Chamber = "house" | "senate" | "executive";
export type TransactionType = "buy" | "sell" | "exchange";
export type RecommendationDirection = "buy" | "sell" | "hold";
export type ConvictionLevel = "low" | "medium" | "high";
export type OrderSide = "buy" | "sell";

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

export interface ScoringBreakdownTrade {
  canonical_trade_id: string;
  politician_name: string;
  transaction_type: TransactionType;
  transaction_date: string;
  amount_mid: number;
  recency_weight: number;
  size_weight: number;
  signal_contribution: number;
}

export interface ScoringBreakdown {
  raw_total: number;
  agreeing_politicians: number;
  total_politicians: number;
  consensus_multiplier: number;
}

export interface SimulatedOrder {
  id: string;
  recommendation_id: string;
  ticker: string;
  side: OrderSide;
  quantity: number;
  price: number;
  notional_value: number;
  created_at: string;
}

export interface RecommendationDetail extends Recommendation {
  scoring_breakdown: ScoringBreakdown;
  supporting_trades: ScoringBreakdownTrade[];
  simulated_orders: SimulatedOrder[];
}
