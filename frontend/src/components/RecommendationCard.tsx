import { Link } from "react-router-dom";
import type { Recommendation } from "../api/types";

export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  return (
    <article className={`recommendation-card direction-${recommendation.direction}`}>
      <header>
        <h3>
          <Link to={`/recommendations/${recommendation.id}`}>{recommendation.ticker}</Link>
        </h3>
        <span className={`badge conviction-${recommendation.conviction}`}>
          {recommendation.direction.toUpperCase()} &middot; {recommendation.conviction} conviction
        </span>
      </header>
      <p className="signal-score">Signal score: {recommendation.signal_score.toFixed(2)}</p>
      {recommendation.rationale_text && <p className="rationale">{recommendation.rationale_text}</p>}
      <footer>
        <time dateTime={recommendation.generated_at}>
          {new Date(recommendation.generated_at).toLocaleDateString()}
        </time>
        <Link to={`/recommendations/${recommendation.id}`} className="detail-link">
          View details &amp; simulate trade &rarr;
        </Link>
      </footer>
    </article>
  );
}
