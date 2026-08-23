import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">Trading Recommendation Platform</span>
        <nav>
          <NavLink to="/" end>
            Recommendations
          </NavLink>
          <NavLink to="/trades">Trades</NavLink>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
