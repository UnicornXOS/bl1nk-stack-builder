# Cloudflare Gateway Setup

## Cloudflare Gateway Setup

### Steps:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **AI Gateway**
3. Create new Gateway
4. Go to Settings → API Tokens
5. Create new API Token with AI Gateway permissions

## Cloudflare Worker (apps/bridge)

`apps/bridge` is already a Cloudflare Worker project in this repo. You do not need to run `npx create-cloudflare@latest` in `apps/bridge` (it will fail because the directory already exists).

### Local dev
1. `cd apps/bridge`
2. `npm install` (or `pnpm install`)
3. `npm run build`
4. `npm run dev`

### Secrets & vars
- Non-secret vars live in `apps/bridge/wrangler.toml` under `[vars]` / `[env.*.vars]`.
- Secrets must be set via Wrangler, e.g. `wrangler secret put OPENROUTER_TOKEN`.

### Your API Token:
\`\`\`
CLOUDFLARE_API_TOKEN=your-token-here
CLOUDFLARE_ACCOUNT_ID=your-account-id
\`\`\`
