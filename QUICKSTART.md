# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Get Your Groq API Key (Required)

1. Visit **https://console.groq.com**
2. Sign up or log in (it's free!)
3. Go to **API Keys** section
4. Click **Create API Key**
5. Copy your key

### Step 2: Add Your API Key

Open the `.env` file in the root directory and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_api_key_here
```

**Note:** The other API keys (Gmail, Spotify, GitHub) are optional. You can test the app with just Groq first!

### Step 3: Run the Application

Open a terminal in the project directory and run:

```bash
npm run dev
```

This will start both the backend and frontend servers.

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:3001

## 🧪 Testing Without External APIs

If you just want to see the app working without setting up Gmail/Spotify/GitHub:

1. Just add your `GROQ_API_KEY` to `.env`
2. Leave the other API keys empty
3. Run `npm run dev`
4. Try asking questions like:
   - "What tools do you have available?"
   - "How can you help me?"
   - "Explain what you can do with GitHub"

The LLM will respond even if the tools aren't configured yet.

## 🔧 Optional: Setting Up External APIs

### Gmail API

**Why?** Send emails and read your inbox using natural language.

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable the Gmail API
4. Create OAuth 2.0 Client credentials
5. Download credentials JSON
6. Use [OAuth 2.0 Playground](https://developers.google.com/oauthplayground) to get a refresh token:
   - Input your Client ID and Secret
   - Select Gmail API v1 scopes
   - Authorize and get refresh token
7. Add to `.env`:
   ```env
   GMAIL_CLIENT_ID=your_client_id
   GMAIL_CLIENT_SECRET=your_client_secret
   GMAIL_REFRESH_TOKEN=your_refresh_token
   ```

### Spotify API

**Why?** Search music, create playlists, control playback.

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Get your Client ID and Client Secret
4. Set redirect URI to `http://localhost:3000/callback`
5. Use the [Spotify OAuth flow](https://developer.spotify.com/documentation/web-api/tutorials/code-flow) to get a refresh token
6. Add to `.env`:
   ```env
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REFRESH_TOKEN=your_refresh_token
   ```

### GitHub API

**Why?** Manage repositories, create issues, search code.

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select scopes:
   - `repo` (full control of repositories)
   - `user` (read user data)
   - `read:org` (read organization data)
4. Generate and copy the token
5. Add to `.env`:
   ```env
   GITHUB_TOKEN=ghp_your_github_token_here
   ```

## 💡 Example Prompts to Try

Once your APIs are configured:

### Gmail
- "List my 5 most recent emails"
- "Send an email to john@example.com saying hello"

### Spotify
- "Search for songs by Taylor Swift"
- "Create a playlist called 'Workout Mix'"
- "Find the album 'After Hours' by The Weeknd"

### GitHub
- "Show me my repositories"
- "Search for popular Python projects"
- "Create an issue in myusername/myrepo with title 'Bug fix'"

## 🐛 Troubleshooting

### "MCP client not initialized"
- Check that the backend server is running
- Look for errors in the backend terminal

### "Invalid API key" (Groq)
- Verify your `GROQ_API_KEY` in `.env` is correct
- Make sure there are no extra spaces
- Try regenerating the key on Groq console

### Gmail/Spotify Tools Not Working
- Make sure your refresh tokens are valid
- Refresh tokens can expire - regenerate if needed
- Check the backend console for specific error messages

### Port Already in Use
If port 3001 or 5173 is already taken:
- Edit `.env` and change `PORT=3001` to another port
- Edit `frontend/vite.config.js` to change the frontend port

## 📊 Architecture Overview

```
┌─────────────────────┐
│   React Frontend    │  ← Beautiful UI at localhost:5173
│   (Vite + React)    │
└──────────┬──────────┘
           │ HTTP Requests
           ↓
┌─────────────────────┐
│  Express Backend    │  ← API Server at localhost:3001
│  (Node.js)          │
└──────────┬──────────┘
           │ Chat Completion
           ↓
┌─────────────────────┐
│   Groq LLM          │  ← Llama 3.3 70B model
│   (Tool-enabled)    │
└──────────┬──────────┘
           │ Tool Calls
           ↓
┌─────────────────────┐
│   MCP Client        │  ← Manages tool execution
└──────────┬──────────┘
           │ Stdio Communication
           ↓
┌─────────────────────┐
│   MCP Server        │  ← Custom tool implementations
└──────────┬──────────┘
           │ API Calls
           ↓
┌─────────────────────┐
│  External APIs      │  ← Gmail, Spotify, GitHub
│  (Google, etc.)     │
└─────────────────────┘
```

## 🎯 What Makes This Special?

1. **Model Context Protocol (MCP)** - Industry-standard way to connect LLMs to tools
2. **Groq Inference** - Lightning-fast LLM responses
3. **Real Tool Execution** - Not mocked - actually interacts with real APIs
4. **Beautiful UI** - Modern, responsive design with smooth animations
5. **Extensible** - Easy to add new tools and APIs

## 🚀 Next Steps

1. Get your Groq API key and test the basic chat
2. Add one external API at a time (start with GitHub - it's easiest)
3. Try the example prompts
4. Explore adding your own custom MCP tools!

---

Need help? Check the main README.md or review the code comments!
