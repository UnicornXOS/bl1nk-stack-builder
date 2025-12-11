---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3046022100a75232b8cfb216b3bc6081146fd1dfd32e1497f58d461255ad6917a2d7bbe995022100a4b4232c3224603e7a4f291e790a52b738b8ca37057d42c2398eb8b90fa37964
    ReservedCode2: 3045022031d748a70e2146d4d4eeca7b3a93f32c976fb7bc7d54bba0b1a67c8b5559efea022100e88df975ca1502fe687433d196f4d9b4e684feac2f9c1d233e3a3a69b8bcb41a
---

# 🏥 bl1nk Admin Dashboard

## Overview

The bl1nk Admin Dashboard provides comprehensive monitoring and management capabilities for your AI agent platform. Track costs, monitor system health, manage users, and configure alerts all from a single interface.

## 🚀 Quick Start

### Access the Dashboard

```bash
# Start the admin dashboard
cd ui/admin
npm run dev

# Or use Docker
docker-compose up admin-dashboard
```

**Dashboard URL**: `http://localhost:3000/admin`

### Default Admin Credentials

```
Username: admin
Password: (set via ADMIN_PASSWORD env variable)
```

## 📊 Dashboard Features

### 💰 Cost Monitoring

- **Real-time Cost Tracking** - Monitor usage across all AI providers
- **Budget Alerts** - Set custom thresholds and receive notifications
- **Cost Analytics** - Historical trends and forecasting
- **Provider Comparison** - Compare costs across different AI providers

### 📈 System Health

- **API Performance** - Response times and success rates
- **Resource Usage** - Database, Redis, and compute metrics
- **Error Tracking** - Monitor and troubleshoot issues
- **Uptime Monitoring** - Service availability tracking

### 👥 User Management

- **User Directory** - View and manage platform users
- **Usage Analytics** - Per-user cost and activity tracking
- **Access Control** - Manage permissions and roles
- **Activity Logs** - Audit trail for user actions

### ⚙️ Configuration Management

- **Environment Variables** - Manage application settings
- **Provider Configuration** - Configure AI provider settings
- **Alert Settings** - Customize notification preferences
- **Feature Flags** - Enable/disable platform features

## 🔧 Dashboard Configuration

### Environment Variables

```bash
# Admin Dashboard Configuration
ADMIN_DASHBOARD_PORT=3000
ADMIN_PASSWORD=your-secure-password
ADMIN_SECRET_KEY=your-secret-key

# Database Connection
ADMIN_DB_URL=postgresql://user:pass@localhost:5432/bl1nk

# Redis Connection
ADMIN_REDIS_URL=redis://localhost:6379

# Notification Settings
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Database Setup

```sql
-- Create admin dashboard tables
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(100) NOT NULL,
    usage_date DATE NOT NULL,
    credits_used DECIMAL(10,2),
    cost_usd DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Insert default admin user (password: admin123)
INSERT INTO admin_users (username, password_hash) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewfhP3Xw0L2LrM4G');
```

## 📱 API Endpoints

### Cost Management

```bash
# Get cost summary
GET /api/admin/costs/summary

# Get daily costs
GET /api/admin/costs/daily?start_date=2024-01-01&end_date=2024-01-31

# Get provider breakdown
GET /api/admin/costs/providers

# Set budget alert
POST /api/admin/budgets/alerts
{
  "provider": "openrouter",
  "threshold": 80,
  "email": "admin@company.com"
}
```

### System Monitoring

```bash
# Get system health
GET /api/admin/health

# Get performance metrics
GET /api/admin/metrics?period=24h

# Get error logs
GET /api/admin/logs/errors?limit=100

# Get usage statistics
GET /api/admin/usage/stats
```

### User Management

```bash
# Get users list
GET /api/admin/users

# Get user details
GET /api/admin/users/{user_id}

# Update user permissions
PUT /api/admin/users/{user_id}
{
  "role": "admin",
  "is_active": true
}
```

## 🎨 UI Components

### Cost Charts

```typescript
// Cost trend chart
import { CostChart } from '@/components/charts/CostChart'

<CostChart
  data={costData}
  timeframe="30d"
  providers={['openrouter', 'cloudflare', 'anthropic']}
  showBudgetLine={true}
  currency="USD"
/>
```

### Alert Configuration

```typescript
// Alert settings modal
import { AlertSettings } from '@/components/alerts/AlertSettings'

<AlertSettings
  providers={['openrouter', 'cloudflare']}
  thresholds={{
    warning: 80,
    critical: 90
  }}
  onSave={handleSaveAlerts}
/>
```

### System Status

```typescript
// System health indicator
import { SystemHealth } from '@/components/status/SystemHealth'

<SystemHealth
  services={[
    { name: 'FastAPI Core', status: 'healthy', latency: 120 },
    { name: 'PostgreSQL', status: 'healthy', latency: 15 },
    { name: 'Redis', status: 'healthy', latency: 2 },
    { name: 'OpenRouter', status: 'degraded', latency: 2500 }
  ]}
/>
```

## 🔔 Notification System

### Email Notifications

```javascript
// Email notification service
const sendCostAlert = async (alertData) => {
  const email = {
    to: alertData.email,
    subject: `🚨 Cost Alert: ${alertData.provider}`,
    html: `
      <h2>Cost Alert for ${alertData.provider}</h2>
      <p>Usage has reached ${alertData.percentage}% of threshold</p>
      <p><strong>Provider:</strong> ${alertData.provider}</p>
      <p><strong>Current Usage:</strong> ${alertData.used} credits</p>
      <p><strong>Threshold:</strong> ${alertData.threshold}%</p>
      <a href="http://localhost:3000/admin/costs">View Dashboard</a>
    `
  }
  
  await emailService.send(email)
}
```

### Slack Integration

```javascript
// Slack webhook notifications
const sendSlackAlert = async (alertData) => {
  const slackMessage = {
    channel: '#billing-alerts',
    text: `🚨 Cost Alert: ${alertData.provider}`,
    attachments: [
      {
        color: alertData.level === 'critical' ? 'danger' : 'warning',
        fields: [
          { title: 'Provider', value: alertData.provider, short: true },
          { title: 'Usage', value: `${alertData.percentage}%`, short: true },
          { title: 'Credits Used', value: alertData.used.toString(), short: true }
        ]
      }
    ]
  }
  
  await fetch(process.env.SLACK_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(slackMessage)
  })
}
```

## 🛠️ Development

### Local Development

```bash
# Clone and setup
git clone <repo-url>
cd bl1nk-agent-builder/ui/admin
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

### Adding New Metrics

```typescript
// Add custom metric collection
import { MetricCollector } from '@/lib/metrics/MetricCollector'

const collector = new MetricCollector()

// Register custom metric
collector.register('custom_api_calls', {
  type: 'counter',
  help: 'Number of custom API calls'
})

// Record metric
collector.increment('custom_api_calls', { endpoint: '/api/v1/chat' })
```

### Custom Dashboards

```typescript
// Create custom dashboard widget
import { BaseWidget } from '@/components/widgets/BaseWidget'

export class CustomWidget extends BaseWidget {
  async fetchData() {
    const response = await fetch('/api/admin/custom/metrics')
    return response.json()
  }
  
  render(data) {
    return (
      <div className="custom-widget">
        <h3>Custom Metrics</h3>
        <MetricDisplay data={data} />
      </div>
    )
  }
}
```

## 📚 Troubleshooting

### Common Issues

**Dashboard not loading**
```bash
# Check if port is available
netstat -an | grep 3000

# Check environment variables
npm run env-check

# Check database connection
npm run db-test
```

**Cost data not updating**
```bash
# Check billing monitor status
./scripts/billing_monitor.sh status

# Manual cost check
./scripts/billing_monitor.sh check

# Check logs
tail -f logs/billing_monitor.log
```

**Notifications not working**
```bash
# Test email configuration
npm run test-email

# Test Slack webhook
npm run test-slack

# Check notification logs
tail -f logs/notifications.log
```

### Performance Optimization

```typescript
// Enable caching for dashboard
import { CacheProvider } from '@/lib/cache/CacheProvider'

const cache = new CacheProvider({
  ttl: 300, // 5 minutes
  maxSize: 1000
})

// Use cached data
const costData = await cache.get('daily_costs', () => 
  fetchCostData()
)
```

## 🔒 Security

### Authentication

- **JWT Tokens** - Secure session management
- **Role-based Access** - Admin, operator, viewer roles
- **Session Timeout** - Automatic logout after inactivity
- **CSRF Protection** - Cross-site request forgery prevention

### Authorization

```typescript
// Role-based middleware
const requireRole = (roles: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    const userRole = req.user?.role
    if (!roles.includes(userRole)) {
      return res.status(403).json({ error: 'Insufficient permissions' })
    }
    next()
  }
}

// Usage
router.get('/admin/users', requireRole(['admin']), getUsers)
```

### Data Protection

- **Encryption at Rest** - Sensitive data encrypted in database
- **Audit Logging** - All admin actions logged
- **Rate Limiting** - API endpoint protection
- **Input Validation** - Sanitized user inputs

## 📞 Support

For admin dashboard support:
- 📧 Email: admin-support@bl1nk.dev
- 💬 Slack: #admin-support
- 📖 Documentation: [docs.bl1nk.dev/admin](https://docs.bl1nk.dev/admin)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/bl1nk-agent-builder/issues)

---

**Happy monitoring! 📊✨**