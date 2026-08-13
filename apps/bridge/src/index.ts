/**
 * bl1nk-agent-builder Cloudflare Worker
 * Edge proxy for request routing, authentication, and rate limiting
 */

import { v4 as uuidv4 } from 'uuid';

interface Env {
  BACKEND_URL: string;
  JWT_SECRET: string;
  RATE_LIMIT_WINDOW: number;
  RATE_LIMIT_MAX_REQUESTS: number;
  RATE_LIMITS: KVNamespace;
  CACHE: KVNamespace;
}

/**
 * Check rate limit using KV
 */
async function checkRateLimit(
  kv: KVNamespace,
  clientId: string,
  window: number,
  maxRequests: number
): Promise<boolean> {
  const key = `rate_limit:${clientId}`;
  const data = await kv.get(key, 'json') as { count: number; resetTime: number } | null;
  const now = Date.now();

  if (!data || now > data.resetTime) {
    await kv.put(key, JSON.stringify({ count: 1, resetTime: now + window * 1000 }), {
      expirationTtl: window,
    });
    return true;
  }

  if (data.count < maxRequests) {
    data.count++;
    await kv.put(key, JSON.stringify(data), { expirationTtl: window });
    return true;
  }

  return false;
}

/**
 * Add request ID and trace headers
 */
function addTraceHeaders(request: Request): Headers {
  const headers = new Headers(request.headers);
  headers.set('X-Request-ID', uuidv4());
  headers.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP') || 'unknown');
  return headers;
}

/**
 * Handle requests
 */
async function handleRequest(request: Request, env: Env): Promise<Response> {
  // Verify authorization
  const authHeader = request.headers.get('Authorization');
  if (!authHeader) {
    return new Response(JSON.stringify({ error: 'Missing authorization header' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Check rate limit
  const clientId = request.headers.get('CF-Connecting-IP') || 'unknown';
  const allowed = await checkRateLimit(
    env.RATE_LIMITS,
    clientId,
    env.RATE_LIMIT_WINDOW || 60,
    env.RATE_LIMIT_MAX_REQUESTS || 100
  );

  if (!allowed) {
    return new Response(JSON.stringify({ error: 'Rate limit exceeded' }), {
      status: 429,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Proxy to backend
  const url = new URL(request.url);
  const backendUrl = new URL(url.pathname + url.search, env.BACKEND_URL);
  const headers = addTraceHeaders(request);

  try {
    const response = await fetch(backendUrl.toString(), {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Backend service unavailable' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export default {
  fetch: (request: Request, env: Env) => handleRequest(request, env),
};
