// Where the Python backend lives (running on the JarvisLabs GPU).
// This is the public proxy URL for port 8000 on the instance.
// If the instance changes, update this one line (no trailing slash).
export const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ||
  "https://d698814168740.notebooksn.jarvislabs.net/proxy/8000";
