import { RecommendationCard } from "../components/RecommendationCard";
import { useRecommendations } from "../hooks/useRecommendations";

export function Dashboard() {
  const { data: recommendations, loading, error } = useRecommendations();

  if (loading) return <p>Loading recommendations...</p>;
  if (error) return <p className="error">Failed to load recommendations: {error.message}</p>;
  if (!recommendations?.length) return <p>No recommendations generated yet.</p>;

  return (
    <div className="recommendation-grid">
      {recommendations.map((recommendation) => (
        <RecommendationCard key={recommendation.id} recommendation={recommendation} />
      ))}
    </div>
  );
}
