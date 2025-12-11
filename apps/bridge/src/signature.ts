// Signature verification utilities for webhook security
// Supports Slack, GitHub, and general JWT verification

/**
 * Verify Slack webhook signature
 */
export async function verifySlackSignature(
  body: string,
  headers: Headers,
  signingSecret: string
): Promise<boolean> {
  const signature = headers.get('X-Slack-Signature');
  const timestamp = headers.get('X-Slack-Request-Timestamp');
  
  if (!signature || !timestamp) {
    console.warn('Missing Slack signature or timestamp headers');
    return false;
  }
  
  // Check timestamp to prevent replay attacks (5 minutes tolerance)
  const ts = parseInt(timestamp);
  const now = Math.floor(Date.now() / 1000);
  const timeDiff = Math.abs(now - ts);
  
  if (timeDiff > 300) {
    console.warn(`Slack timestamp too old: ${timeDiff}s`);
    return false;
  }
  
  try {
    // Create signature base string
    const signatureBaseString = `v0:${timestamp}:${body}`;
    
    // Import signing secret as HMAC key
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(signingSecret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    
    // Generate signature
    const signatureBytes = await crypto.subtle.sign(
      'HMAC',
      key,
      new TextEncoder().encode(signatureBaseString)
    );
    
    // Format expected signature
    const expectedSignature = 'v0=' + Array.from(new Uint8Array(signatureBytes))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    // Compare signatures using timing-safe comparison
    const isValid = crypto.timingSafeEqual(
      new TextEncoder().encode(signature),
      new TextEncoder().encode(expectedSignature)
    );
    
    if (!isValid) {
      console.warn('Invalid Slack signature');
    }
    
    return isValid;
    
  } catch (error) {
    console.error('Slack signature verification error:', error);
    return false;
  }
}

/**
 * Verify GitHub webhook signature
 */
export async function verifyGitHubSignature(
  body: string,
  headers: Headers,
  secret: string
): Promise<boolean> {
  const signature = headers.get('X-Hub-Signature-256');
  
  if (!signature) {
    console.warn('Missing GitHub signature header');
    return false;
  }
  
  try {
    // Import secret as HMAC key
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );
    
    // Generate signature
    const signatureBytes = await crypto.subtle.sign(
      'HMAC',
      key,
      new TextEncoder().encode(body)
    );
    
    // Format expected signature
    const expectedSignature = 'sha256=' + Array.from(new Uint8Array(signatureBytes))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    
    // Compare signatures using timing-safe comparison
    const isValid = crypto.timingSafeEqual(
      new TextEncoder().encode(signature),
      new TextEncoder().encode(expectedSignature)
    );
    
    if (!isValid) {
      console.warn('Invalid GitHub signature');
    }
    
    return isValid;
    
  } catch (error) {
    console.error('GitHub signature verification error:', error);
    return false;
  }
}

/**
 * Verify JWT token (for general API authentication)
 */
export async function verifyJWT(
  token: string,
  secret: string,
  algorithms: string[] = ['HS256']
): Promise<any | null> {
  try {
    // Split JWT into parts
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.warn('Invalid JWT format');
      return null;
    }
    
    const [headerB64, payloadB64, signatureB64] = parts;
    
    // Decode header and payload
    const header = JSON.parse(atob(headerB64.replace(/-/g, '+').replace(/_/g, '/')));
    const payload = JSON.parse(atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/')));
    
    // Check algorithm
    if (!algorithms.includes(header.alg)) {
      console.warn(`Unsupported JWT algorithm: ${header.alg}`);
      return null;
    }
    
    // Import secret as HMAC key
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(secret),
      { name: 'HMAC', hash: header.alg === 'HS256' ? 'SHA-256' : 'SHA-512' },
      false,
      ['sign']
    );
    
    // Create signature input
    const signatureInput = `${headerB64}.${payloadB64}`;
    
    // Generate signature
    const signatureBytes = await crypto.subtle.sign(
      'HMAC',
      key,
      new TextEncoder().encode(signatureInput)
    );
    
    // Format generated signature
    const generatedSignature = btoa(String.fromCharCode(...new Uint8Array(signatureBytes)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    
    // Compare signatures using timing-safe comparison
    const isValid = crypto.timingSafeEqual(
      new TextEncoder().encode(signatureB64),
      new TextEncoder().encode(generatedSignature)
    );
    
    if (!isValid) {
      console.warn('Invalid JWT signature');
      return null;
    }
    
    // Check expiration
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      console.warn('JWT expired');
      return null;
    }
    
    // Check not before
    if (payload.nbf && Date.now() / 1000 < payload.nbf) {
      console.warn('JWT not yet valid');
      return null;
    }
    
    return payload;
    
  } catch (error) {
    console.error('JWT verification error:', error);
    return null;
  }
}

/**
 * Generate JWT token
 */
export async function generateJWT(
  payload: any,
  secret: string,
  algorithm: string = 'HS256',
  expiresIn: number = 3600
): Promise<string> {
  try {
    const header = {
      alg: algorithm,
      typ: 'JWT'
    };
    
    const now = Math.floor(Date.now() / 1000);
    const jwtPayload = {
      ...payload,
      iat: now,
      exp: now + expiresIn
    };
    
    // Base64 encode header and payload
    const headerB64 = btoa(JSON.stringify(header))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
      
    const payloadB64 = btoa(JSON.stringify(jwtPayload))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    
    // Create signature input
    const signatureInput = `${headerB64}.${payloadB64}`;
    
    // Import secret as HMAC key
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(secret),
      { name: 'HMAC', hash: algorithm === 'HS256' ? 'SHA-256' : 'SHA-512' },
      false,
      ['sign']
    );
    
    // Generate signature
    const signatureBytes = await crypto.subtle.sign(
      'HMAC',
      key,
      new TextEncoder().encode(signatureInput)
    );
    
    // Base64 encode signature
    const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signatureBytes)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
    
    return `${signatureInput}.${signatureB64}`;
    
  } catch (error) {
    console.error('JWT generation error:', error);
    throw error;
  }
}

/**
 * Verify Poe webhook signature (if needed)
 */
export async function verifyPoeSignature(
  body: string,
  headers: Headers,
  secret: string
): Promise<boolean> {
  // Poe webhook verification logic
  // This would depend on Poe's specific signature format
  const signature = headers.get('X-Poe-Signature');
  
  if (!signature) {
    console.warn('Missing Poe signature header');
    return false;
  }
  
  try {
    // Implementation depends on Poe's specific requirements
    // For now, return true as placeholder
    return true;
  } catch (error) {
    console.error('Poe signature verification error:', error);
    return false;
  }
}

/**
 * Verify Manus webhook signature (if needed)
 */
export async function verifyManusSignature(
  body: string,
  headers: Headers,
  secret: string
): Promise<boolean> {
  // Manus webhook verification logic
  // This would depend on Manus's specific signature format
  const signature = headers.get('X-Manus-Signature');
  
  if (!signature) {
    console.warn('Missing Manus signature header');
    return false;
  }
  
  try {
    // Implementation depends on Manus's specific requirements
    // For now, return true as placeholder
    return true;
  } catch (error) {
    console.error('Manus signature verification error:', error);
    return false;
  }
}

/**
 * Common signature verification interface
 */
export interface SignatureVerificationOptions {
  required?: boolean;
  tolerance?: number; // seconds
  algorithms?: string[];
}

/**
 * Verify any signature based on source
 */
export async function verifySignature(
  source: string,
  body: string,
  headers: Headers,
  secrets: Record<string, string>,
  options: SignatureVerificationOptions = {}
): Promise<boolean> {
  const { required = true, tolerance = 300 } = options;
  
  switch (source.toLowerCase()) {
    case 'slack':
      return verifySlackSignature(body, headers, secrets.slack || '');
      
    case 'github':
      return verifyGitHubSignature(body, headers, secrets.github || '');
      
    case 'poe':
      return verifyPoeSignature(body, headers, secrets.poe || '');
      
    case 'manus':
      return verifyManusSignature(body, headers, secrets.manus || '');
      
    default:
      if (required) {
        console.warn(`No signature verification implemented for source: ${source}`);
        return false;
      }
      return true;
  }
}

/**
 * Extract signature secrets from environment
 */
export function getSignatureSecrets(env: any): Record<string, string> {
  return {
    slack: env.SLACK_SIGNING_SECRET || '',
    github: env.GITHUB_WEBHOOK_SECRET || '',
    poe: env.POE_WEBHOOK_SECRET || '',
    manus: env.MANUS_WEBHOOK_SECRET || ''
  };
}