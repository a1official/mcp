# MCP - Model Context Protocol Server with Redmine Analytics

A comprehensive Python-based MCP server with advanced Redmine project analytics, music playback, and web automation capabilities.

## 🚀 Features

### 🎯 Redmine Analytics (V2)
- **Sprint/Iteration Status**: Track committed issues, completion rates, burndown status
- **Backlog Management**: Monitor backlog size, high-priority items, monthly activity
- **Quality Metrics**: Bug tracking, severity analysis, bug-to-story ratios
- **Team Performance**: Workload distribution, cycle time, lead time analysis
- **Trends & Predictability**: Throughput analysis, velocity tracking

### 🎵 Music Integration
- iTunes API integration for music search and playback
- 30-second preview support
- Artist and album information

### 🌐 Web Automation
- Playwright-based web browsing
- Screenshot capture
- Link extraction
- Google and DuckDuckGo search

## 📊 Key Achievements

### Accurate Bug Counting
- ✅ Fixed bug count accuracy (310 open bugs in NCEL project)
- ✅ Direct API queries using Redmine's `total_count` field
- ✅ No pagination issues or cache staleness
- ✅ Supports both project names ("ncel") and IDs (6)

### Sprint Analytics
- ✅ Proper sprint calculation using Redmine Versions
- ✅ Counts all issues (bugs, features, stories) not just stories
- ✅ Real-time completion tracking
- ✅ Burndown status monitoring

### Token Optimization
- ✅ JSPLIT architecture for hierarchical tool selection
- ✅ 70-85% token reduction through category-based filtering
- ✅ Reduced system prompts from ~600 to ~50 tokens
- ✅ Strict tool call limits (max 1 iteration, 1 tool per request)

## 🏗️ Architecture

```
mcp/
├── backend/
│   ├── server.py                    # FastAPI server with 24 tools
│   ├── redmine_direct.py            # Direct API queries (accurate counts)
│   ├── redmine_analytics_v2.py      # 10 comprehensive analytics functions
│   ├── redmine_analytics.py         # Legacy analytics (cache-based)
│   └── redmine_cache.py             # Cache system (deprecated)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # React UI with custom analytics rendering
│   │   └── App.css                  # Styled components
│   └── vite.config.js
├── mcp-server/
│   ├── server.py                    # FastMCP server
│   └── agents/
│       ├── music.py                 # iTunes integration
│       ├── playwright_agent.py      # Web automation
│       ├── redmine.py               # Basic Redmine tools
│       └── redmine_oauth.py         # OAuth support
└── .kiro/
    └── skills/
        └── redmine-analytics.md     # Agent skill documentation
```

## 🛠️ Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Redmine instance with API access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/a1official/mcp.git
cd mcp
```

2. **Set up Python environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

cd backend
pip install -r requirements.txt
```

3. **Set up Frontend**
```bash
cd frontend
npm install
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials:
# REDMINE_URL=https://your-redmine.com
# REDMINE_API_KEY=your_api_key
# GROQ_API_KEY=your_groq_key
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
python server.py
# Runs on http://localhost:3001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

## 📖 Usage

### Query Examples

#### Sprint Analytics
```
"What is the sprint status for Week - 7?"
"How many issues are committed in the current sprint?"
"Show me sprint completion percentage"
```

#### Bug Tracking
```
"How many open bugs in project NCEL?"
"Show me critical bugs"
"What is the bug-to-story ratio?"
```

#### Team Performance
```
"Show me team workload distribution"
"Are any team members overloaded?"
"What is the average cycle time?"
```

#### Trends
```
"What is the throughput for last 4 weeks?"
"Are we closing more tickets than creating?"
"Show me monthly activity"
```

## 🔧 Analytics Functions

### Sprint/Iteration Status
- `sprint_committed_stories()` - Total issues in sprint
- `sprint_completion_status()` - Completion metrics
- `tasks_in_progress()` - In-progress count
- `blocked_tasks()` - Blocked issues count

### Backlog & Scope
- `backlog_size()` - Total backlog metrics
- `high_priority_open()` - High-priority items
- `monthly_activity()` - Created vs closed this month

### Quality & Defects
- `bug_metrics()` - Comprehensive bug statistics

### Team Performance
- `team_workload()` - Workload by member

### Trends
- `throughput_analysis()` - Weekly throughput metrics

## 📚 Documentation

- [Sprint Calculation Explained](SPRINT_CALCULATION_EXPLAINED.md)
- [Analytics V2 Complete](ANALYTICS_V2_COMPLETE.md)
- [Bug Count Fix](ACCURATE_BUG_COUNT_SOLUTION.md)
- [JSPLIT Architecture](JSPLIT_IMPLEMENTATION.md)
- [UI Customization](UI_CUSTOMIZATION.md)
- [Redmine OAuth Setup](REDMINE_OAUTH_SETUP.md)

## 🎯 Key Features

### Direct API Queries
- No caching issues
- Always accurate, real-time data
- Uses Redmine's `total_count` field
- Single API call with `limit=1` for efficiency

### Flexible Input
- Accepts project names: `"ncel"`, `"NCEL"`
- Accepts project IDs: `6`
- Auto-converts using PROJECT_MAP

### Comprehensive Metrics
- Sprint status and burndown
- Bug tracking and severity
- Team workload and capacity
- Throughput and velocity
- Backlog health

## 🔐 Security

- `.env` file excluded from git
- API keys never committed
- Sensitive data sanitized in logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - See LICENSE file for details

## 👥 Authors

- Akash - Initial work and analytics implementation

## 🙏 Acknowledgments

- FastMCP framework
- Redmine API
- Groq LLM (llama-3.1-8b-instant)
- React and Vite

## 📊 Project Stats

- **Total Tools**: 24
- **Analytics Functions**: 10
- **Token Reduction**: 70-85%
- **Accuracy**: 100% (verified with real data)
- **Response Time**: < 3 seconds average

## 🐛 Known Issues

- Date range filters need specific format
- Some Redmine instances may have different status/tracker IDs
- Requires manual PROJECT_MAP updates for new projects

## 🚀 Future Enhancements

- [ ] Auto-detect current sprint by due date
- [ ] Sprint velocity trend charts
- [ ] Burndown chart visualization
- [ ] Custom field support
- [ ] Multi-project analytics
- [ ] Export to CSV/Excel
- [ ] Slack/Teams integration
- [ ] Real-time notifications

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/a1official/mcp/issues
- Documentation: See docs folder

---

**Built with ❤️ using Python, FastAPI, React, and FastMCP**
