---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022100e9dc56d4581e5b9c3b4552c819f9a845022f7b91f92a3398076434171b25133a02202aea27d332d02ee0be4b0ffaf89fe305c733c9c73aa0d6a904aeb7f048bc992b
    ReservedCode2: 30460221008aa69bfb257aabe51578d759e8893ba324190d0dc295e7ade10b035cf15b4ed2022100eff6980d461e3d4278f4e0efe2c42cdf4a3887454052ba723859bf45d8b97e4a
---

# =============================================================================
# Security Configuration
# =============================================================================

## Security Configuration

### Generate Secure Keys:

#### JWT Secret (minimum 32 characters):
\`\`\`
JWT_SECRET=$(openssl rand -base64 32)
\`\`\`

#### Encryption Key (exactly 32 characters):
\`\`\`
ENCRYPTION_KEY=$(openssl rand -hex 16)
\`\`\`

#### Admin API Key:
\`\`\`
ADMIN_API_KEY=$(openssl rand -base64 24)
\`\`\`

### Generate All Keys at Once:
\`\`\`bash
# JWT Secret
JWT_SECRET=$(openssl rand -base64 32)

# Encryption Key
ENCRYPTION_KEY=$(openssl rand -hex 16)

# Admin API Key
ADMIN_API_KEY=$(openssl rand -base64 24)

echo "JWT_SECRET=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo "ADMIN_API_KEY=$ADMIN_API_KEY"
\`\`\`
