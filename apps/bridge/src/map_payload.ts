// Payload mapping utilities for webhook data transformation
// Converts platform-specific webhook payloads to standard format

/**
 * Standard webhook payload interface
 */
export interface StandardWebhookPayload {
  source: string;
  external_id: string;
  user_id: string;
  workspace_id?: string;
  message: string;
  metadata: Record<string, any>;
}

/**
 * Map platform-specific payload to standard format
 */
export async function mapPayload(
  source: string,
  body: string,
  headers: Headers
): Promise<StandardWebhookPayload> {
  let payload: any;
  
  try {
    payload = JSON.parse(body);
  } catch (error) {
    throw new Error('Invalid JSON payload');
  }
  
  switch (source.toLowerCase()) {
    case 'poe':
      return mapPoePayload(payload, headers);
      
    case 'manus':
      return mapManusPayload(payload, headers);
      
    case 'slack':
      return mapSlackPayload(payload, headers);
      
    case 'github':
      return mapGitHubPayload(payload, headers);
      
    default:
      throw new Error(`Unsupported source: ${source}`);
  }
}

/**
 * Map Poe webhook payload to standard format
 */
function mapPoePayload(payload: any, headersWebhookPayload {
  // Poe: Headers): Standard webhook payload structure
  // Expected format based on Poe bot API
  if (!payload.query || !payload.user_id) {
    throw new Error('Invalid Poe payload: missing query or user_id');
  }
  
  const externalId = payload.message_id || payload.query_id || generateExternalId('poe');
  const message = payload.query || payload.message || '';
  
  return {
    source: 'poe',
    external_id: externalId,
    user_id: payload.user_id,
    workspace_id: payload.workspace_id || null,
    message: message,
    metadata: {
      context: payload.context || 'conversation',
      user_agent: headers.get('User-Agent') || 'Poe/Unknown',
      bot_id: payload.bot_id,
      is_final: payload.is_final || true,
      timestamp: payload.timestamp || new Date().toISOString(),
      // Include any additional Poe-specific data
      raw_payload: payload
    }
  };
}

/**
 * Map Manus webhook payload to standard format
 */
function mapManusPayload(payload: any, headers: Headers): StandardWebhookPayload {
  // Manus webhook payload structure
  // Expected format based on Manus platform
  if (!payload.content && !payload.request) {
    throw new Error('Invalid Manus payload: missing content or request');
  }
  
  const externalId = payload.request_id || payload.id || generateExternalId('manus');
  const message = payload.content || payload.request || '';
  
  return {
    source: 'manus',
    external_id: externalId,
    user_id: payload.user_id || 'unknown',
    workspace_id: payload.workspace_id || null,
    message: message,
    metadata: {
      context: payload.context || 'document',
      user_agent: headers.get('User-Agent') || 'Manus/Unknown',
      document_id: payload.document_id,
      priority: payload.priority || 'normal',
      language: payload.language || 'en',
      timestamp: payload.timestamp || new Date().toISOString(),
      // Include any additional Manus-specific data
      raw_payload: payload
    }
  };
}

/**
 * Map Slack webhook payload to standard format
 */
function mapSlackPayload(payload: any, headers: Headers): StandardWebhookPayload {
  // Slack webhook payload structure
  // Expected format: { type: "event_callback", event: {...} }
  if (!payload.event) {
    throw new Error('Invalid Slack payload: missing event');
  }
  
  const event = payload.event;
  const teamId = payload.team_id;
  const userId = event.user;
  const channelId = event.channel;
  const messageTs = event.ts;
  
  // Extract message text (handle app mentions)
  let message = event.text || '';
  if (event.type === 'app_mention') {
    // Remove bot mention from message
    message = message.replace(/<@[A-Z0-9]+>/g, '').trim();
  }
  
  if (!message) {
    throw new Error('Invalid Slack payload: empty message');
  }
  
  const externalId = `${teamId}-${channelId}-${messageTs}`;
  
  return {
    source: 'slack',
    external_id: externalId,
    user_id: userId,
    workspace_id: teamId,
    message: message,
    metadata: {
      context: 'slack_conversation',
      user_agent: headers.get('User-Agent') || 'Slack/Unknown',
      event_type: event.type,
      channel_id: channelId,
      message_ts: messageTs,
      thread_ts: event.thread_ts,
      channel_type: event.channel_type || 'channel',
      // Include Slack-specific event data
      raw_event: event,
      team_id: teamId,
      api_app_id: payload.api_app_id,
      timestamp: new Date(parseFloat(messageTs) * 1000).toISOString()
    }
  };
}

/**
 * Map GitHub webhook payload to standard format
 */
function mapGitHubPayload(payload: any, headers: Headers): StandardWebhookPayload {
  // GitHub webhook payload structure
  // Handle different event types: pull_request, issue, push, etc.
  const action = payload.action;
  const repository = payload.repository;
  const installation = payload.installation;
  
  let message = '';
  let externalId = '';
  let userId = '';
  
  if (payload.pull_request) {
    // Pull request event
    const pr = payload.pull_request;
    message = `PR: ${pr.title}\n\n${pr.body || ''}`;
    externalId = `pr_${repository.full_name}_${pr.number}_${action}`;
    userId = pr.user?.login || 'unknown';
    
  } else if (payload.issue) {
    // Issue event
    const issue = payload.issue;
    message = `Issue: ${issue.title}\n\n${issue.body || ''}`;
    externalId = `issue_${repository.full_name}_${issue.number}_${action}`;
    userId = issue.user?.login || 'unknown';
    
  } else if (payload.commits && payload.commits.length > 0) {
    // Push event
    const commitMessages = payload.commits
      .map((commit: any) => commit.message)
      .join('\n\n');
    message = `Push: ${commitMessages}`;
    externalId = `push_${repository.full_name}_${payload.after}_${action}`;
    userId = payload.pusher?.name || 'unknown';
    
  } else if (payload.ref) {
    // Other GitHub events
    message = `GitHub event: ${payload.ref}`;
    externalId = `github_${repository.full_name}_${Date.now()}_${action}`;
    userId = payload.sender?.login || 'unknown';
    
  } else {
    throw new Error('Unsupported GitHub webhook event type');
  }
  
  return {
    source: 'github',
    external_id: externalId,
    user_id: userId,
    workspace_id: installation?.id?.toString() || null,
    message: message,
    metadata: {
      context: 'github_repository',
      user_agent: headers.get('User-Agent') || 'GitHub/Unknown',
      repository: repository.full_name,
      repository_id: repository.id,
      action: action,
      installation_id: installation?.id,
      sender: payload.sender?.login,
      event_type: getGitHubEventType(headers),
      // Include GitHub-specific data
      raw_payload: payload,
      timestamp: new Date().toISOString()
    }
  };
}

/**
 * Get GitHub event type from headers
 */
function getGitHubEventType(headers: Headers): string {
  return headers.get('X-GitHub-Event') || 'unknown';
}

/**
 * Generate external ID for platforms that don't provide one
 */
function generateExternalId(source: string): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `${source}_${timestamp}_${random}`;
}

/**
 * Validate required fields in standard payload
 */
export function validateStandardPayload(payload: StandardWebhookPayload): void {
  const requiredFields = ['source', 'external_id', 'user_id', 'message'];
  
  for (const field of requiredFields) {
    if (!payload[field as keyof StandardWebhookPayload]) {
      throw new Error(`Missing required field: ${field}`);
    }
  }
  
  // Validate source
  const validSources = ['poe', 'manus', 'slack', 'github'];
  if (!validSources.includes(payload.source)) {
    throw new Error(`Invalid source: ${payload.source}`);
  }
  
  // Validate external_id is not empty
  if (!payload.external_id || payload.external_id.trim() === '') {
    throw new Error('External ID cannot be empty');
  }
  
  // Validate user_id format (basic UUID check)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(payload.user_id)) {
    console.warn('User ID is not in UUID format:', payload.user_id);
  }
}

/**
 * Enrich payload with additional context
 */
export function enrichPayload(
  payload: StandardWebhookPayload,
  additionalContext: Record<string, any> = {}
): StandardWebhookPayload {
  return {
    ...payload,
    metadata: {
      ...payload.metadata,
      ...additionalContext,
      enriched_at: new Date().toISOString()
    }
  };
}

/**
 * Extract user information from different platforms
 */
export function extractUserInfo(source: string, payload: any): {
  user_id: string;
  display_name?: string;
  email?: string;
} {
  switch (source.toLowerCase()) {
    case 'poe':
      return {
        user_id: payload.user_id,
        display_name: payload.display_name
      };
      
    case 'manus':
      return {
        user_id: payload.user_id || 'unknown',
        display_name: payload.display_name,
        email: payload.email
      };
      
    case 'slack':
      return {
        user_id: payload.event?.user,
        display_name: payload.event?.user || 'Slack User'
      };
      
    case 'github':
      return {
        user_id: payload.sender?.login || 'unknown',
        display_name: payload.sender?.login,
        email: payload.sender?.email
      };
      
    default:
      return {
        user_id: 'unknown',
        display_name: 'Unknown User'
      };
  }
}

/**
 * Normalize message content across platforms
 */
export function normalizeMessage(source: string, message: string): string {
  switch (source.toLowerCase()) {
    case 'slack':
      // Remove Slack-specific formatting
      return message
        .replace(/<@[A-Z0-9]+>/g, '') // Remove user mentions
        .replace(/<#[A-Z0-9]+\|[^>]+>/g, '') // Remove channel mentions
        .replace(/<[^>]+>/g, '') // Remove other Slack formatting
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .trim();
        
    case 'github':
      // Remove GitHub-specific formatting
      return message
        .replace(/#[0-9]+/g, '') // Remove issue/PR references
        .replace(/@[a-zA-Z0-9-_]+/g, '') // Remove user mentions
        .trim();
        
    default:
      return message.trim();
  }
}