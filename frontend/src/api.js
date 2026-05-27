// Where the Python backend lives.
// Locally during dev it's localhost:8000.
// Later, when we deploy on JarvisLabs, we just change this one line
// to the JarvisLabs URL and the whole frontend points at the GPU box.
export const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";
