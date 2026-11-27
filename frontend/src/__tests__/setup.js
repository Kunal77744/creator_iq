// Vitest global setup: registers jest-dom matchers and stubs ResizeObserver for jsdom.
import "@testing-library/jest-dom";

// Provide a no-op ResizeObserver since Recharts ResponsiveContainer relies on it in tests.
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
