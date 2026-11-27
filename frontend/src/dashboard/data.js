// Dashboard color palettes and role-based sidebar navigation definitions.

// Brand colors for supported social platforms and audience chart segments.
export const PLATFORM_COLORS = { YouTube: "#ef4444", Instagram: "#d946a8", LinkedIn: "#2563eb" };
export const AUDIENCE_SHADES = ["#5b3fd6", "#7c63ee", "#a396f5", "#c8bff9", "#e2dcfc"];

// Nav items. `to` is a real page; everything else opens a "coming soon" page (/m/<slug>).
const slug = (t) => t.toLowerCase().replace(/[^a-z0-9]+/g, "-");
// Helper to build a sidebar navigation entry with an automatic fallback route.
const N = (label, icon, to, chevron = false) => ({ label, icon, to: to || `/m/${slug(label)}`, chevron });

// Sidebar menu items grouped by user role.
export const NAV_BY_ROLE = {
  creator: [
    N("Dashboard", "dash", "/dashboard"), N("AI Copilot", "crown", "/ai-copilot"), N("My Profile", "user", "/profile"), N("Social Accounts", "link", "/social-accounts"),
    N("Content", "content", "/content"), N("Analytics", "analytics", "/analytics", true), N("Audience", "audience", "/audience", true),
    N("Revenue", "revenue", "/revenue", true), N("Reports", "reports", "/reports"), N("Notifications", "bell", "/notifications"), N("Settings", "settings", "/settings"),
  ],
  agency: [
    N("Dashboard", "dash", "/dashboard"), N("AI Copilot", "crown", "/ai-copilot"), N("Agency Profile", "user", "/profile"), N("Creators", "audience", "/audience"),
    N("Campaigns", "campaign", "/content"), N("Analytics", "analytics", "/analytics", true), N("Content Library", "library", "/content"),
    N("Reports", "reports", "/reports"), N("Notifications", "bell", "/notifications"), N("Settings", "settings", "/settings"),
  ],
  marketing_team: [
    N("Dashboard", "dash", "/dashboard"), N("AI Copilot", "crown", "/ai-copilot"), N("Campaigns", "campaign", "/content"), N("Content", "content", "/content"),
    N("Analytics", "analytics", "/analytics", true), N("Audience", "audience", "/audience", true), N("Reports", "reports", "/reports"),
    N("Notifications", "bell", "/notifications"), N("Settings", "settings", "/settings"),
  ],
  admin: [
    N("Dashboard", "dash", "/dashboard"), N("AI Copilot", "crown", "/ai-copilot"), N("User Management", "shield", "/admin/users"), N("Content Moderation", "moderation", "/content"),
    N("Platform Integrations", "plug", "/social-accounts"), N("Analytics Overview", "analytics", "/analytics"), N("Reports", "reports", "/reports"),
    N("Activity Logs", "activity", "/notifications"), N("System Settings", "settings", "/settings"), N("Account Settings", "user", "/settings"),
  ],
};
