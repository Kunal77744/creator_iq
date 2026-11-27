// Placeholder page for upcoming CreatorIQ modules not yet implemented.
import { Link, useParams } from "react-router-dom";
import AppLayout from "../components/AppLayout.jsx";

// Renders a formatted section title from the URL slug with a link back to the dashboard
export default function ComingSoon() {
  const { page } = useParams();
  // Convert kebab-case route param (e.g. "brand-deals") into Title Case ("Brand Deals")
  const title = page.split("-").map((w) => w[0].toUpperCase() + w.slice(1)).join(" ");
  return (
    <AppLayout>
      <article className="card soon">
        <h1>{title}</h1>
        <p className="muted">This section is part of a later CreatorIQ module and is not built yet.</p>
        <Link to="/dashboard" className="btn-link">Back to dashboard</Link>
      </article>
    </AppLayout>
  );
}
