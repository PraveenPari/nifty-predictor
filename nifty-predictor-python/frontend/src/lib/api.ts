/**
 * Central API configuration.
 *
 * - Local dev (vite proxy): leave VITE_API_URL unset -> same-origin '/api'.
 * - Hosted API (Render/Railway): set VITE_API_URL=https://<your-app>.onrender.com
 *   via .env.production or the Vercel dashboard.
 */
export const API_BASE: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') ?? '';

export const apiUrl = (path: string): string =>
  `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;

/** Socket.IO server URL: explicit API host, else same-origin. */
export const SOCKET_URL: string | undefined = API_BASE || undefined;
