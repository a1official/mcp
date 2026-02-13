# 🎵 Music Playback Quick Start

Get music playback working in 5 minutes!

## Prerequisites

- **Spotify Premium account** (required for playback)
- Spotify app installed (desktop, mobile, or web player)

## Setup Steps

### 1. Get Spotify Credentials (2 minutes)

1. Go to https://developer.spotify.com/dashboard
2. Click "Create app"
3. Fill in:
   - Name: "MCP Music Player"
   - Description: "Music playback"
   - Redirect URI: `http://localhost:8888/callback`
4. Click "Save"
5. Copy your **Client ID** and **Client Secret**

### 2. Add to .env (30 seconds)

Open your `.env` file and add:

```env
SPOTIFY_CLIENT_ID=paste_your_client_id_here
SPOTIFY_CLIENT_SECRET=paste_your_client_secret_here
```

### 3. Get Refresh Token (1 minute)

Run this command:

```bash
npm run spotify:setup
```

This will:
1. Open your browser to `http://localhost:8888/login`
2. Ask you to log in to Spotify
3. Show you the refresh token

Copy the token and add it to `.env`:

```env
SPOTIFY_REFRESH_TOKEN=paste_your_refresh_token_here
```

### 4. Start the App (30 seconds)

```bash
npm run dev
```

### 5. Open Spotify (30 seconds)

**Important**: Open Spotify on any device:
- Desktop app
- Mobile app
- Web player (open.spotify.com)

Play any song (you can pause it after). This makes the device "active".

### 6. Test It! (30 seconds)

Open http://localhost:5173 and try:

- "Play some jazz"
- "Play Bohemian Rhapsody"
- "What's playing?"
- "Next song"

## Natural Language Commands

You can use natural language to control music:

### Play Music
- "Play [song name]"
- "Play [artist name]"
- "Play some [genre]"
- "Play Bohemian Rhapsody by Queen"
- "Play The Beatles"

### Control Playback
- "Pause" / "Pause the music"
- "Next song" / "Skip"
- "Previous song" / "Go back"
- "What's playing?" / "Current song"

### Search
- "Search for songs by Coldplay"
- "Find albums by Pink Floyd"

## Troubleshooting

### "No active device found"

**Solution**: Open Spotify on any device and play something (even if you pause it immediately).

Check available devices:
- In chat: "Show my Spotify devices"

### "Invalid refresh token"

**Solution**: Run `npm run spotify:setup` again to get a new token.

### "Insufficient client scope"

**Solution**: Delete your old token and run `npm run spotify:setup` again. Make sure to authorize all permissions.

### Music not playing

**Checklist**:
- ✅ Spotify Premium account?
- ✅ Spotify app open on a device?
- ✅ Device is active (played something recently)?
- ✅ All credentials in .env?
- ✅ Server restarted after adding credentials?

## How It Works

1. You say: "Play some jazz"
2. AI understands your intent
3. Searches Spotify for jazz tracks
4. Plays the top result on your active device

## Free Account?

If you don't have Spotify Premium, you can still:
- Search for music
- Get song information
- See what's popular

But you cannot control playback (Spotify API limitation).

## Next Steps

Try these advanced commands:
- "Play my discover weekly"
- "Play the album Dark Side of the Moon"
- "Search for chill electronic music"

Enjoy your music! 🎵
