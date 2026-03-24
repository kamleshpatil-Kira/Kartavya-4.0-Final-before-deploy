import { NextRequest } from "next/server";

const BACKEND_BASE = process.env.NEXT_API_BASE_URL || "http://127.0.0.1:8000";

async function handler(
  req: NextRequest,
  context: { params: { path?: string[] } } | { params: Promise<{ path?: string[] }> }
) {
  const { path } = await context.params;
  const fullPath = path ? path.join("/") : "";
  const search = req.nextUrl.search || "";
  const url = `${BACKEND_BASE}/api/${fullPath}${search}`;

  const headers = new Headers(req.headers);
  headers.delete("host");

  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer();

  const response = await fetch(url, {
    method: req.method,
    headers,
    body,
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");

  let responseBody: any = response.body;
  const contentType = response.headers.get("content-type") || "";
  const isBinary =
    contentType.includes("application/zip") ||
    contentType.includes("application/pdf") ||
    contentType.includes("audio/") ||
    contentType.includes("image/") ||
    contentType.includes("application/octet-stream");

  if (isBinary && response.ok) {
    responseBody = await response.arrayBuffer();
  }

  return new Response(responseBody, {
    status: response.status,
    headers: responseHeaders,
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
export const dynamic = "force-dynamic";
