// Main entry point for bl1nk-agent-bridge Cloudflare Worker
// This Worker acts as an edge proxy for webhook and API requests

import { verifySignature } from './signature';
import { mapPayload } from './map_payload';

// Environment type definitions
interface Env {
  CORE_API_URL: string;
  JWT_SECRET: string;
  SLACK_SIGNING_SECRET: string;
  GITHUB_WEBHOOK_SECRET: string;
  RATE_LIMITS: KVNamespace;
  CACHE: KVNamespace;
}

// Request context
interface RequestContext {
  url: URL;
  method: string;
  headers: Headers;
  body: string;
  traceId: string;
  source: string;
}

// Response types
interface AckResponse {
  status: 'accepted' | 'rejected';
  task_id?: number;
  trace_id: string;
  message: string;
}

interface ErrorResponse {
  error: string;
  message: string;
  trace_id: string;
}

// Rate limiting interface
interface RateLimitInfo {
  requests: number;
  windowStart: number;
  maxRequests: number;
  windowMinutes: number;
}

// Default configuration
const CONFIG = {
  RATE_LIMIT_REQUESTS_PER_MINUTE: 100,
  RATE_LIMIT_WINDOW_MINUTES: 1,
  CORE_API_TIMEOUT_MS: 30000,
  MAX_PAYLOAD_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_ORIGINS: ['https://bl1nk.site'],
  CORS_HEADERS: {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Slack-Signature, X-Hub-Signature-256',
    'Access-Control-Max-Age': '86400'
  }
};

/**
 * Main worker entry point
 */
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const startTime = Date.now();
    const traceId = generateTraceId();
    
    try {
      // Create request context
      const ctx = await createRequestContext(request, traceId);
      
      // Log incoming request
      await logRequest(ctx, env);
      
      // Handle CORS preflight
      if (ctx.method === 'OPTIONS') {
        return handleCors(request, ctx);
      }
      
      // Rate limiting
      await checkRateLimit(ctx, env);
      
      // Route handling
      const response = await handleRoute(ctx, env);
      
      // Log response
      await logResponse(ctx, response, env, Date.now() - startTime);
      
      return response;
      
    } catch (error) {
      console.error('Worker error:', error);
      return handleError(error as Error, traceId);
    }
  },
  
  // Scheduled event handler (optional)
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    console.log('Scheduled event:', event.cron);
    
    // Cleanup old rate limit entries
    await cleanupRateLimits(env);
    
    // Update provider health checks
    await updateProviderHealth(env);
  }
};

/**
 * Create request context from incoming request
 */
async function createRequestContext(request: Request, traceId: string): Promise<RequestContext> {
  const url = new URL(request.url);
  const method = request.method;
  const headers = request.headers;
  
  // Read request body
  let body = '';
  if (method !== 'GET' && method !== 'HEAD') {
    const contentLength = headers.get('content-length');
    if (contentLength && parseInt(contentLength) > CONFIG.MAX_PAYLOAD_SIZE) {
      throw new Error('Payload too large');
    }
    body = await request.text();
  }
  
  // Determine source from path
  const pathSegments = url.pathname.split('/').filter(Boolean);
  const source = determineSource(pathSegments);
  
  return {
    url,
    method,
    headers,
    body,
    traceId,
    source
  };
}

/**
 * Determine source from URL path
 */
function determineSource(pathSegments: string[]): string {
  if (pathSegments.length < 2) return 'unknown';
  
  const webhookSegment = pathSegments[0];
  if (webhookSegment === 'webhook') {
    return pathSegments[1];
  }
  
  return 'unknown';
}

/**
 * Handle CORS preflight requests
 */
function handleCors(request: Request, ctx: RequestContext): Response {
  const corsHeaders = {
    ...CONFIG.CORS_HEADERS,
    'Access-Control-Allow-Origin': request.headers.get('Origin') || '*'
  };
  
  return new Response(null, {
    status: 204,
    headers: corsHeaders
  });
}

/**
 * Handle different routes
 */
async function handleRoute(ctx: RequestContext, env: Env): Promise<Response> {
  const { url, method, body, headers } = ctx;
  const pathSegments = url.pathname.split('/').filter(Boolean);
  
  // Webhook routes
  if (pathSegments[0] === 'webhook') {
    return await handleWebhook(pathSegments[1], method, body, headers, ctx, env);
  }
  
  // Health check
  if (pathSegments[0] === 'health') {
    return handleHealth();
  }
  
  // MCP tools routes
  if (pathSegments[0] === 'mcp') {
    return await handleMcpRoute(pathSegments, method, body, headers, ctx, env);
  }
  
  // Skills routes
  if (pathSegments[0] === 'skills') {
    return await handleSkillsRoute(pathSegments, method, body, headers, ctx, env);
  }
  
  // Tasks routes
  if (pathSegments[0] === 'tasks') {
    return await handleTasksRoute(pathSegments, method, body, headers, ctx, env);
  }
  
  // Unknown route
  return new Response(JSON.stringify({
    error: 'NotFound',
    message: 'Route not found',
    trace_id: ctx.traceId
  }), {
    status: 404,
    headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
  });
}

/**
 * Handle webhook routes
 */
async function handleWebhook(
  source: string,
  method: string,
  body: string,
  headers: Headers,
  ctx: RequestContext,
  env: Env
): Promise<Response> {
  if (method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'MethodNotAllowed',
      message: 'Only POST method allowed for webhooks',
      trace_id: ctx.traceId
    }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
    });
  }
  
  // Verify signature based on source
  let isValidSignature = true;
  try {
    if (source === 'slack') {
      isValidSignature = await verifySlackSignature(body, headers, env.SLACK_SIGNING_SECRET);
    } else if (source === 'github') {
      isValidSignature = await verifyGitHubSignature(body, headers, env.GITHUB_WEBHOOK_SECRET);
    } else {
      // For other sources, use general JWT verification if needed
      isValidSignature = true;
    }
  } catch (error) {
    console.error('Signature verification failed:', error);
    isValidSignature = false;
  }
  
  if (!isValidSignature) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Invalid signature',
      trace_id: ctx.traceId
    }), {
      status: 401,
      headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
    });
  }
  
  // Map payload to standard format
  const mappedPayload = await mapPayload(source, body, headers);
  
  // Forward to core API
  const coreResponse = await forwardToCore('/webhook/' + source, mappedPayload, ctx, env);
  
  return coreResponse;
}

/**
 * Handle MCP routes
 */
async function handleMcpRoute(
  pathSegments: string[],
  method: string,
  body: string,
  headers: Headers,
  ctx: RequestContext,
  env: Env
): Promise<Response> {
  const mcpPath = '/' + pathSegments.slice(1).join('/');
  
  // Add trace ID to headers
  headers.set('X-Trace-Id', ctx.traceId);
  
  // Forward to core API
  const coreResponse = await forwardToCore('/mcp' + mcpPath, body, ctx, env);
  
  return coreResponse;
}

/**
 * Handle skills routes
 */
async function handleSkillsRoute(
  pathSegments: string[],
  method: string,
  body: string,
  headers: Headers,
  ctx: RequestContext,
  env: Env
): Promise<Response> {
  const skillsPath = '/' + pathSegments.slice(1).join('/');
  
  // Add trace ID to headers
  headers.set('X-Trace-Id', ctx.traceId);
  
  // Forward to core API
  const coreResponse = await forwardToCore('/skills' + skillsPath, body, ctx, env);
  
  return coreResponse;
}

/**
 * Handle tasks routes
 */
async function handleTasksRoute(
  pathSegments: string[],
  method: string,
  body: string,
  headers: Headers,
  ctx: RequestContext,
  env: Env
): Promise<Response> {
  const tasksPath = '/' + pathSegments.slice(1).join('/');
  
  // Add trace ID to headers
  headers.set('X-Trace-Id', ctx.traceId);
  
  // Forward to core API
  const coreResponse = await forwardToCore('/tasks' + tasksPath, body, ctx, env);
  
  return coreResponse;
}

/**
 * Handle health check
 */
function handleHealth(): Response {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'bl1nk-agent-bridge',
    version: '0.1.0'
  };
  
  return new Response(JSON.stringify(health), {
    status: 200,
    headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
  });
}

/**
 * Forward request to core API
 */
async function forwardToCore(
  path: string,
  body: string,
  ctx: RequestContext,
  env: Env
): Promise<Response> {
  const coreUrl = new URL(path, env.CORE_API_URL);
  
  const coreRequest = new Request(coreUrl.toString(), {
    method: ctx.method,
    headers: {
      'Content-Type': 'application/json',
      'X-Trace-Id': ctx.traceId,
      'X-Source': ctx.source,
      'X-Forwarded-For': ctx.headers.get('CF-Connecting-IP') || 'unknown',
      'User-Agent': 'bl1nk-agent-bridge/0.1.0'
    },
    body: body || undefined
  });
  
  try {
    const response = await fetch(coreRequest, {
      signal: AbortSignal.timeout(CONFIG.CORE_API_TIMEOUT_MS)
    });
    
    // Create response with CORS headers
    const responseHeaders = new Headers(response.headers);
    Object.entries(CONFIG.CORS_HEADERS).forEach(([key, value]) => {
      responseHeaders.set(key, value);
    });
    
    return new Response(response.body, {
      status: response.status,
      headers: responseHeaders
    });
    
  } catch (error) {
    console.error('Core API error:', error);
    
    return new Response(JSON.stringify({
      error: 'ServiceUnavailable',
      message: 'Core service temporarily unavailable',
      trace_id: ctx.traceId
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
    });
  }
}

/**
 * Check rate limiting
 */
async function checkRateLimit(ctx: RequestContext, env: Env): Promise<void> {
  const clientIp = ctx.headers.get('CF-Connecting-IP') || 'unknown';
  const key = `rate_limit:${clientIp}:${ctx.source}`;
  
  try {
    const stored = await env.RATE_LIMITS.get(key, 'json') as RateLimitInfo;
    const now = Date.now();
    const windowStart = Math.floor(now / (CONFIG.RATE_LIMIT_WINDOW_MINUTES * 60 * 1000)) * CONFIG.RATE_LIMIT_WINDOW_MINUTES * 60 * 1000;
    
    if (!stored || stored.windowStart !== windowStart) {
      // New window
      const rateLimitInfo: RateLimitInfo = {
        requests: 1,
        windowStart,
        maxRequests: CONFIG.RATE_LIMIT_REQUESTS_PER_MINUTE,
        windowMinutes: CONFIG.RATE_LIMIT_WINDOW_MINUTES
      };
      
      await env.RATE_LIMITS.put(key, JSON.stringify(rateLimitInfo), {
        expirationTtl: CONFIG.RATE_LIMIT_WINDOW_MINUTES * 60
      });
    } else {
      // Existing window
      if (stored.requests >= stored.maxRequests) {
        throw new Error('Rate limit exceeded');
      }
      
      stored.requests++;
      await env.RATE_LIMITS.put(key, JSON.stringify(stored), {
        expirationTtl: CONFIG.RATE_LIMIT_WINDOW_MINUTES * 60
      });
    }
  } catch (error) {
    throw new Error('Rate limit check failed');
  }
}

/**
 * Verify Slack signature
 */
async function verifySlackSignature(body: string, headers: Headers, secret: string): Promise<boolean> {
  const signature = headers.get('X-Slack-Signature');
  const timestamp = headers.get('X-Slack-Request-Timestamp');
  
  if (!signature || !timestamp) {
    return false;
  }
  
  // Check timestamp (prevent replay attacks)
  const ts = parseInt(timestamp);
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - ts) > 300) { // 5 minutes
    return false;
  }
  
  // Verify signature
  const hmac = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signatureBaseString = `v0:${timestamp}:${body}`;
  const signatureBytes = await crypto.subtle.sign(
    'HMAC',
    hmac,
    new TextEncoder().encode(signatureBaseString)
  );
  
  const expectedSignature = 'v0=' + Array.from(new Uint8Array(signatureBytes))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  return crypto.timingSafeEqual(
    new TextEncoder().encode(signature),
    new TextEncoder().encode(expectedSignature)
  );
}

/**
 * Verify GitHub signature
 */
async function verifyGitHubSignature(body: string, headers: Headers, secret: string): Promise<boolean> {
  const signature = headers.get('X-Hub-Signature-256');
  
  if (!signature) {
    return false;
  }
  
  const hmac = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  
  const signatureBytes = await crypto.subtle.sign(
    'HMAC',
    hmac,
    new TextEncoder().encode(body)
  );
  
  const expectedSignature = 'sha256=' + Array.from(new Uint8Array(signatureBytes))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  
  return crypto.timingSafeEqual(
    new TextEncoder().encode(signature),
    new TextEncoder().encode(expectedSignature)
  );
}

/**
 * Generate unique trace ID
 */
function generateTraceId(): string {
  return 'tr_' + crypto.randomUUID().replace(/-/g, '').substring(0, 16);
}

/**
 * Handle errors
 */
function handleError(error: Error, traceId: string): Response {
  console.error('Worker error:', error);
  
  const errorResponse: ErrorResponse = {
    error: 'InternalServerError',
    message: 'An unexpected error occurred',
    trace_id: traceId
  };
  
  return new Response(JSON.stringify(errorResponse), {
    status: 500,
    headers: { 'Content-Type': 'application/json', ...CONFIG.CORS_HEADERS }
  });
}

/**
 * Log request (for monitoring)
 */
async function logRequest(ctx: RequestContext, env: Env): Promise<void> {
  const logEntry = {
    timestamp: Date.now(),
    trace_id: ctx.traceId,
    source: ctx.source,
    method: ctx.method,
    path: ctx.url.pathname,
    user_agent: ctx.headers.get('User-Agent'),
    ip: ctx.headers.get('CF-Connecting-IP')
  };
  
  // Store in cache for debugging
  await env.CACHE.put(`request:${ctx.traceId}`, JSON.stringify(logEntry), {
    expirationTtl: 3600
  });
  
  console.log('Request:', JSON.stringify(logEntry));
}

/**
 * Log response (for monitoring)
 */
async function logResponse(
  ctx: RequestContext,
  response: Response,
  env: Env,
  duration: number
): Promise<void> {
  const logEntry = {
    timestamp: Date.now(),
    trace_id: ctx.traceId,
    status: response.status,
    duration_ms: duration,
    content_length: response.headers.get('content-length')
  };
  
  console.log('Response:', JSON.stringify(logEntry));
}

/**
 * Cleanup old rate limit entries
 */
async function cleanupRateLimits(env: Env): Promise<void> {
  // Implementation for cleaning up old rate limit entries
  // This would typically iterate through keys and delete expired ones
  console.log('Cleaning up rate limit entries');
}

/**
 * Update provider health checks
 */
async function updateProviderHealth(env: Env): Promise<void> {
  // Implementation for checking provider health
  console.log('Updating provider health checks');
}