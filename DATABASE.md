---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 304402205eb6edb1beefb68f1d45d96b4a7e413b734cdb0eb9ee8c9cb9c97ae9338cb9f20220266ef054dcabc2803195a08ab743447a2bae021df53bd5be4fc9d09c7252df12
    ReservedCode2: 3045022060c5809cb8672d9acfd196696727da75641bf01b1b2e1a9b556f29ee01430811022100aa2eaa6525372021d32388223f0be42a494e5096e3f36b7893d861c2f0fd1b6e
---

# =============================================================================
# Database Configuration
# =============================================================================

## Database Setup

### Neon Postgres:
1. Go to [Neon](https://neon.tech/)
2. Sign up / Log in
3. Create new project
4. Get connection string from Settings → Database

### Your Connection String:
\`\`\`
DB_DSN=postgresql://user:password@ep-example.us-east-1.aws.neon.tech:5432/bl1nk
\`\`\`

### Upstash Redis:
1. Go to [Upstash](https://upstash.com/)
2. Sign up / Log in
3. Create Redis database
4. Copy REST URL

### Your Redis URL:
\`\`\`
UPSTASH_REDISURL=rediss://:abc123@us1-some-id.upstash.io:6379
\`\`\`
