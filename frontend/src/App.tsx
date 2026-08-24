import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { RecommendationDetail } from "./pages/RecommendationDetail";
import { Trades } from "./pages/Trades";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/recommendations/:id" element={<RecommendationDetail />} />
        <Route path="/trades" element={<Trades />} />
      </Routes>
    </Layout>
  );
}
