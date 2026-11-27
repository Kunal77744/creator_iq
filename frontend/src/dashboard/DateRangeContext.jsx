// Context for sharing the selected dashboard date window (7, 30, or 90 days) across pages.
import { createContext, useContext, useEffect, useState } from "react";

const DateRangeContext = createContext({ days: 30, setDays: () => {} });
const KEY = "creatoriq_days";

// Provider that initializes the date range from localStorage and persists changes.
export function DateRangeProvider({ children }) {
  const [days, setDays] = useState(() => {
    try {
      const v = Number(localStorage.getItem(KEY));
      return [7, 30, 90].includes(v) ? v : 30;
    } catch {
      return 30;
    }
  });

  // Sync the selected day count to localStorage whenever it changes.
  useEffect(() => {
    try { localStorage.setItem(KEY, String(days)); } catch { /* ignore */ }
  }, [days]);

  return <DateRangeContext.Provider value={{ days, setDays }}>{children}</DateRangeContext.Provider>;
}

// Hook to read or update the active dashboard date range.
export const useDateRange = () => useContext(DateRangeContext);
