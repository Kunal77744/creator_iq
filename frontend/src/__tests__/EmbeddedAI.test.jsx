import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";

// Mock axios-based api client
vi.mock("../api", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
  errorMessage: (e) => e?.message || "Error",
}));

import api from "../api";
import AIGrowthBrief from "../components/AIGrowthBrief.jsx";
import AIDrawer from "../components/AIDrawer.jsx";
import RevenuePage from "../pages/RevenuePage.jsx";
import ContentAnalytics from "../pages/ContentAnalytics.jsx";

vi.mock("../AuthContext.jsx", () => ({
  useAuth: () => ({
    user: { user_id: 1, name: "Kunal", role: "creator", role_label: "Creator" },
    logout: vi.fn(),
  }),
}));

describe("Embedded AI & UI Integration (TDD RED)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders AI Growth Brief on Dashboard from /api/v1/ai/insights", async () => {
    api.get.mockResolvedValueOnce({
      data: {
        has_data: true,
        summary: "Your YouTube channel grew 12% this month.",
        insights: ["Recommended sponsorship rate: ₹25,000", "Top engagement on tutorials"],
      },
    });

    render(<AIGrowthBrief onOpenCopilot={vi.fn()} />);
    expect(await screen.findByText(/Your YouTube channel grew 12% this month/i)).toBeInTheDocument();
    expect(screen.getByText(/Recommended sponsorship rate/i)).toBeInTheDocument();
  });

  it("opens Global AI Copilot Drawer and sends agent-chat prompt", async () => {
    api.post.mockResolvedValueOnce({
      data: {
        reply: "Your recommended sponsorship rate is ₹28,000.",
        tools_used: ["calculate_sponsorship_rate"],
        citations: [],
      },
    });

    render(<AIDrawer open={true} onClose={vi.fn()} />);
    const input = screen.getByPlaceholderText(/Ask CreatorIQ AI/i);
    fireEvent.change(input, { target: { value: "What is my sponsorship rate?" } });
    fireEvent.submit(input.closest("form"));

    expect(await screen.findByText(/₹28,000/i)).toBeInTheDocument();
    expect(screen.getByText(/calculate_sponsorship_rate/i)).toBeInTheDocument();
  });

  it("pre-fills Revenue form using AI Deal Estimator", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/v1/revenue")) {
        return Promise.resolve({ data: { summary: { total: 50000, paid: 50000, pending: 0 }, breakdown: [], entries: [] } });
      }
      if (url.includes("/api/v1/ai/sponsorship-estimate")) {
        return Promise.resolve({ data: { recommended_rate_inr: 32500, range_min_inr: 26000, range_max_inr: 40625, basis: "120,000 followers" } });
      }
      return Promise.resolve({ data: {} });
    });

    render(
      <MemoryRouter>
        <RevenuePage />
      </MemoryRouter>
    );

    const estBtn = await screen.findByRole("button", { name: /AI Deal Estimator/i });
    fireEvent.click(estBtn);

    await waitFor(() => {
      const amtInput = screen.getByPlaceholderText(/Amount \(INR\)/i);
      expect(amtInput.value).toBe("32500");
    });
  });

  it("analyzes a post with RAG from ContentAnalytics page", async () => {
    api.get.mockImplementation((url) => {
      if (url.includes("/api/v1/analytics/posts")) {
        return Promise.resolve({
          data: [{ post_id: 10, title: "FastAPI RAG Guide", platform: "YouTube", views: 95000, likes: 7200, comments: 480, engagement_rate: 8.4 }],
        });
      }
      return Promise.resolve({ data: { Views: [] } });
    });
    api.post.mockResolvedValueOnce({
      data: {
        post_id: 10,
        title: "FastAPI RAG Guide",
        analysis: "Strong hook and tutorial retention drove 8.4% engagement.",
        next_ideas: ["Part 2: Production pgvector", "RAG Eval Checklist"],
      },
    });

    render(
      <MemoryRouter>
        <ContentAnalytics />
      </MemoryRouter>
    );

    const analyzeBtn = await screen.findByRole("button", { name: /Analyze with AI/i });
    fireEvent.click(analyzeBtn);

    expect(await screen.findByText(/Strong hook and tutorial retention/i)).toBeInTheDocument();
  });
});
