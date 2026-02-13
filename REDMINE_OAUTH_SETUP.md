# Redmine OAuth Setup Guide

This guide explains how to set up OAuth authentication for Redmine, allowing individual users to authenticate with their own accounts.

## Why OAuth?

- **Multi-user support**: Each user authenticates with their own Redmine account
- **Better security**: No shared API keys
- **Proper permissions**: Users can only access what they're allowed to see
- **Audit trail**: Actions are tracked per user

## Setup Steps

### 1. Enable OAuth in Redmine

First, check if your Redmine instance supports OAuth:
- Redmine 3.4+ has built-in OAuth support
- For older versions, you may need the `redmine_oauth` plugin

### 2. Register Your Application in Redmine

1. Log into Redmine as an **administrator**
2. Go to **Administration** → **Applications**
3. Click **New application**
4. Fill in the form:
   - **Name**: `MCP Music Server` (or any name you prefer)
   - **Redirect URI**: `http://localhost:3001/api/redmine/callback`
   - **Scopes**: Select `read` and `write`
5. Click **Submit**
6. Copy the **Application ID** (Client ID) and **Secret** (Client Secret)

### 3. Configure Environment Variables

Add to your `.env` file:

```env
# Redmine OAuth Configuration
REDMINE_URL=https://your-redmine-instance.com
REDMINE_CLIENT_ID=your_application_id_here
REDMINE_CLIENT_SECRET=your_secret_here
```

### 4. Update MCP Server

Add OAuth tools to your MCP server in `mcp-server/server.py`:

```python
from agents.redmine_oauth import register_redmine_oauth_tools

# Register OAuth tools
register_redmine_oauth_tools(mcp)
```

### 5. Restart Backend

```bash
# Stop current backend
# Restart with new configuration
python backend/server.py
```

## How to Use

### Step 1: Get Authorization URL

Ask the assistant:
```
"Get Redmine OAuth authorization URL"
```

The assistant will return a URL like:
```
https://your-redmine.com/oauth/authorize?client_id=...
```

### Step 2: Authorize

1. Visit the URL in your browser
2. Log in to Redmine (if not already logged in)
3. Click **Authorize** to grant access
4. You'll be redirected to the callback URL with a `code` parameter

### Step 3: Exchange Code for Token

Copy the `code` from the URL and ask:
```
"Exchange Redmine OAuth code: abc123xyz"
```

You'll receive an access token that you can use for API calls.

### Step 4: Use Redmine with OAuth

Now you can use Redmine tools with your personal access token:
```
"List my Redmine projects using token: your_access_token"
"Create issue in project X using token: your_access_token"
```

## OAuth vs API Key

| Feature | API Key | OAuth |
|---------|---------|-------|
| Setup complexity | Simple | Moderate |
| Multi-user | No (shared key) | Yes (per user) |
| Security | Lower | Higher |
| Permissions | Admin level | User level |
| Token expiry | Never | Yes (refresh needed) |
| Best for | Single user, testing | Production, multiple users |

## Troubleshooting

### "OAuth not configured" error
- Check that `REDMINE_CLIENT_ID` and `REDMINE_CLIENT_SECRET` are set in `.env`
- Restart the backend after updating `.env`

### "Invalid redirect URI" error
- Make sure the redirect URI in Redmine matches exactly: `http://localhost:3001/api/redmine/callback`
- Check for trailing slashes

### "Unauthorized" error
- Your access token may have expired
- Get a new authorization code and exchange it for a fresh token

### Redmine doesn't have OAuth
- Use API key authentication instead (simpler but less secure)
- Or upgrade Redmine to 3.4+

## Production Deployment

For production:

1. **Use HTTPS**: Change redirect URI to `https://your-domain.com/api/redmine/callback`
2. **Store tokens securely**: Use a database to store user tokens
3. **Implement token refresh**: Automatically refresh expired tokens
4. **Add session management**: Link tokens to user sessions

## Next Steps

- Implement token refresh mechanism
- Add token storage in database
- Create a web UI for OAuth flow
- Add support for multiple Redmine instances per user
