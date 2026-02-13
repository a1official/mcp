# MCP Music Player

A modern web application that demonstrates the **Model Context Protocol (MCP)** architecture with AI-powered music playback using natural language.

## 🏗️ Architecture

```
Web App (React + Vite)
        ↓
Backend API Server (Node.js + Express)
        ↓
LLM (Groq - Llama 3.3 70B)
        ↓
MCP Client
        ↓
Python FastMCP Server
        ↓
iTunes API (no auth needed)
```

## ✨ Features

- 🤖 **AI-Powered Music** - Natural language music playback ("play some jazz")
- 🎵 **Instant Playback** - 30-second previews from iTunes (no authentication)
- 🎨 **Modern UI** - Beautiful glassmorphism design with floating music player
- 🔄 **Real-time** - Watch as the AI searches and plays music
- 🐍 **Python FastMCP** - Simple, fast, and reliable MCP server

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ installed
- Python 3.8+ installed
- Groq API key ([Get it here](https://console.groq.com))

### Installation

1. **Clone or navigate to the project:**
   ```bash
   cd c:\Users\akash2000.at\Desktop\mcp
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   cd frontend
   npm install
   cd ..
   ```

3. **Install Python dependencies:**
   ```bash
   pip install fastmcp httpx
   ```
   
   Or run:
   ```bash
   npm run setup:python
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running the Application

```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173 (or 5174)
- Backend API: http://localhost:3001

## 🔧 API Setup

### Groq API Key (Required)
1. Visit https://console.groq.com
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy and add to `.env`

## 💬 Example Prompts

Try these in the chat interface:

- "Play Bohemian Rhapsody"
- "Play some jazz"
- "Play The Weeknd"
- "Search for songs by Coldplay"
- "Tell me about The Beatles"

## 🛠️ Tech Stack

### Frontend
- React 18
- Vite
- Lucide React (icons)
- Vanilla CSS with glassmorphism

### Backend
- Express.js
- Groq SDK (LLM)
- MCP SDK (Client)

### MCP Server
- Python 3.8+
- FastMCP
- httpx (async HTTP)
- iTunes API

## 📁 Project Structure

```
mcp/
├── backend/
│   └── server.js           # Express server with Groq + MCP client
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── App.css         # Component styles
│   │   ├── index.css       # Global styles
│   │   └── main.jsx        # React entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── mcp-server/
│   ├── server.py           # Python FastMCP server
│   └── requirements.txt    # Python dependencies
├── .env                    # Environment variables
├── .env.example            # Template
├── package.json            # Node.js dependencies
├── PYTHON_MCP_SETUP.md     # Python setup guide
└── README.md
```

## 🎨 Design Features

- **Glassmorphism UI** - Frosted glass effects with backdrop blur
- **Gradient Accents** - Beautiful purple-pink-cyan gradients
- **Smooth Animations** - Fade-ins, slides, and hover effects
- **Dark Mode** - Eye-friendly dark theme
- **Responsive Layout** - Works on all screen sizes
- **Micro-interactions** - Delightful button hovers and transitions

## 🔍 How It Works

1. **User Input**: User types "Play some jazz" in the chat
2. **Backend Processing**: Request sent to Express backend
3. **LLM Analysis**: Groq's Llama 3.3 70B analyzes the request
4. **Tool Selection**: LLM calls the `play_music` tool via MCP
5. **Python Execution**: FastMCP server searches iTunes API
6. **Response**: Track data with preview URL returned
7. **Auto-Play**: Frontend detects music data and plays automatically
8. **Music Player**: Floating player appears with album art and controls

## 🐛 Troubleshooting

**Python not found:**
- Install Python from https://www.python.org/downloads/

**FastMCP not installed:**
- Run: `pip install fastmcp httpx`

**Groq API errors:**
- Verify your GROQ_API_KEY is valid
- Check your Groq API quota/limits

**Music not playing:**
- Check browser console (F12) for errors
- Make sure backend is running
- Try the "Test Music Player" button

**Port already in use:**
- Kill the process: `taskkill /F /PID <pid>`
- Or change the port in `.env`

## 📝 License

MIT License - feel free to use this project for learning or building your own applications!

## 🤝 Contributing

This is a demonstration project, but feel free to fork and enhance it with additional MCP tools and integrations!

## 🌟 Next Steps

Possible enhancements:
- Add more music sources (YouTube, SoundCloud)
- Implement playlists and favorites
- Add lyrics display
- Voice input/output
- Music recommendations
- Full-length playback (requires Spotify Premium)

## 📚 Documentation

- [Python MCP Setup Guide](PYTHON_MCP_SETUP.md)
- [Music Quick Start](MUSIC_QUICKSTART.md)
- [Custom Tools Guide](CUSTOM_TOOLS.md)

---

Built with ❤️ using Model Context Protocol, FastMCP, Groq, and modern web technologies.
