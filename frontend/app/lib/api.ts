const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

const PROVIDER_LABEL_REDACTIONS: Array<[RegExp, string]> = [
  [/google ai studio/gi, "provider dashboard"],
  [/google cloud text[- ]to[- ]speech/gi, "speech service"],
  [/google cloud/gi, "cloud service"],
  [/google tts/gi, "speech service"],
  [/gtts/gi, "speech fallback service"],
  [/gemini/gi, "AI service"],
  [/google/gi, "provider"],
];

export function redactBackendProviderDetails(value: string): string {
  let text = String(value || "");
  for (const [pattern, replacement] of PROVIDER_LABEL_REDACTIONS) {
    text = text.replace(pattern, replacement);
  }
  return text;
}

function extractApiErrorMessage(raw: string): string {
  const text = String(raw || "").trim();
  if (!text) return "";
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed?.detail === "string") return parsed.detail;
    if (typeof parsed?.message === "string") return parsed.message;
    if (Array.isArray(parsed?.detail)) {
      const details = parsed.detail
        .map((item: any) => {
          if (typeof item === "string") return item;
          if (typeof item?.msg === "string") return item.msg;
          return "";
        })
        .filter(Boolean);
      if (details.length > 0) return details.join("; ");
    }
  } catch {
    // Non-JSON payloads fall back to plain text.
  }
  return text;
}

export async function readApiErrorMessage(res: Response): Promise<string> {
  const raw = await res.text();
  const extracted = extractApiErrorMessage(raw);
  const fallback = `Request failed: ${res.status}`;
  return redactBackendProviderDetails(extracted || fallback);
}

export function apiUrl(path: string) {
  if (API_BASE) {
    return `${API_BASE}${path}`;
  }
  return path;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const targetUrl = apiUrl(path);
  try {
    const res = await fetch(targetUrl, options);
    if (!res.ok) {
      const message = await readApiErrorMessage(res);
      const err = new Error(message || `Request failed: ${res.status}`);
      (err as any).status = res.status;
      throw err;
    }
    return res.json();
  } catch (err: any) {
    const isNetworkError =
      err instanceof TypeError || /Failed to fetch/i.test(err?.message || "");

    if (!isNetworkError) {
      throw err;
    }

    if (API_BASE) {
      try {
        const res = await fetch(path, options);
        if (!res.ok) {
          const message = await readApiErrorMessage(res);
          const fallbackErr = new Error(message || `Request failed: ${res.status}`);
          (fallbackErr as any).status = res.status;
          throw fallbackErr;
        }
        return res.json();
      } catch (fallbackErr: any) {
        const hint = `Failed to reach backend at ${API_BASE} (and proxy). Is it running?`;
        if (fallbackErr?.message) {
          throw new Error(`${redactBackendProviderDetails(fallbackErr.message)}\n${hint}`);
        }
        throw new Error(hint);
      }
    }
    const hint = `Failed to reach backend. Is it running?`;
    if (err?.message) {
      throw new Error(`${redactBackendProviderDetails(err.message)}\n${hint}`);
    }
    throw new Error(hint);
  }
}

export async function apiFetchBlob(path: string, options?: RequestInit): Promise<Blob> {
  const targetUrl = apiUrl(path);
  try {
    const res = await fetch(targetUrl, options);
    if (!res.ok) {
      const message = await readApiErrorMessage(res);
      const err = new Error(message || `Request failed: ${res.status}`);
      (err as any).status = res.status;
      throw err;
    }
    return res.blob();
  } catch (err: any) {
    const isNetworkError =
      err instanceof TypeError || /Failed to fetch/i.test(err?.message || "");

    if (!isNetworkError) {
      throw err;
    }

    if (API_BASE) {
      try {
        const res = await fetch(path, options);
        if (!res.ok) {
          const message = await readApiErrorMessage(res);
          const fallbackErr = new Error(message || `Request failed: ${res.status}`);
          (fallbackErr as any).status = res.status;
          throw fallbackErr;
        }
        return res.blob();
      } catch (fallbackErr: any) {
        const hint = `Failed to reach backend at ${API_BASE} (and proxy). Is it running?`;
        if (fallbackErr?.message) {
          throw new Error(`${redactBackendProviderDetails(fallbackErr.message)}\n${hint}`);
        }
        throw new Error(hint);
      }
    }

    const hint = `Failed to reach backend. Is it running?`;
    if (err?.message) {
      throw new Error(`${redactBackendProviderDetails(err.message)}\n${hint}`);
    }
    throw new Error(hint);
  }
}
