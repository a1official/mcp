import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, Mail, Music, Github, Play, Pause, Settings, X } from 'lucide-react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const [enabledTools, setEnabledTools] = useState({
    music: true,
    playwright: true,
    redmine: true,
  });
  const [redmineDbEnabled, setRedmineDbEnabled] = useState(false);
  const [redmineDbLoading, setRedmineDbLoading] = useState(false);
  const [redmineDbStatus, setRedmineDbStatus] = useState(null);
  const [cacheLoadProgress, setCacheLoadProgress] = useState(0);
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Create audio element
    audioRef.current = new Audio();
    audioRef.current.addEventListener('ended', () => {
      setIsPlaying(false);
    });
    audioRef.current.addEventListener('play', () => {
      setIsPlaying(true);
    });
    audioRef.current.addEventListener('pause', () => {
      setIsPlaying(false);
    });

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const playTrack = (track) => {
    console.log('playTrack called with:', track);
    if (audioRef.current && track.previewUrl) {
      try {
        audioRef.current.src = track.previewUrl;
        audioRef.current.play()
          .then(() => {
            console.log('Audio playing successfully');
            setCurrentTrack(track);
            setIsPlaying(true);
          })
          .catch(err => {
            console.error('Error playing audio:', err);
            alert('Failed to play audio. Please check browser permissions.');
          });
      } catch (err) {
        console.error('Error setting audio source:', err);
      }
    } else {
      console.error('No audio ref or preview URL:', { audioRef: audioRef.current, previewUrl: track.previewUrl });
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
    }
  };

  // Redmine DB Cache Control
  const toggleRedmineDb = async (enabled) => {
    setRedmineDbLoading(true);
    setCacheLoadProgress(0);
    
    let progressInterval = null;
    
    try {
      const action = enabled ? 'on' : 'off';
      
      // Auto-enable Redmine category when enabling DB
      if (enabled && !enabledTools.redmine) {
        setEnabledTools(prev => ({
          ...prev,
          redmine: true
        }));
      }
      
      // Simulate progress for loading animation
      if (enabled) {
        progressInterval = setInterval(() => {
          setCacheLoadProgress(prev => {
            if (prev >= 90) return 90;
            return prev + 10;
          });
        }, 400);
      }
      
      const response = await fetch('http://localhost:3001/api/redmine-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Toggle response:', result);
      
      if (result.success) {
        setRedmineDbEnabled(enabled);
        setCacheLoadProgress(100);
        
        // Fetch status after enabling
        if (enabled && result.cache_info) {
          setRedmineDbStatus(result.cache_info);
        } else if (!enabled) {
          setRedmineDbStatus(null);
        }
      } else {
        throw new Error(result.error || 'Failed to toggle cache');
      }
    } catch (error) {
      console.error('Error toggling Redmine DB:', error);
      alert(`Failed to toggle Redmine DB cache: ${error.message}`);
      setRedmineDbEnabled(!enabled); // Revert toggle
    } finally {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      setRedmineDbLoading(false);
      setTimeout(() => setCacheLoadProgress(0), 1000);
    }
  };

  const fetchRedmineDbStatus = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/redmine-cache', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'status' })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Status response:', result);
      
      if (result.success) {
        // Check if cache is enabled
        if (result.status === 'enabled' && result.cache_info) {
          setRedmineDbEnabled(true);
          setRedmineDbStatus(result.cache_info);
        } else if (result.status === 'disabled') {
          setRedmineDbEnabled(false);
          setRedmineDbStatus(null);
        }
      }
    } catch (error) {
      console.error('Error fetching Redmine DB status:', error);
      // Don't show alert for status check failures
    }
  };

  // Check Redmine DB status on mount
  useEffect(() => {
    fetchRedmineDbStatus();
  }, []);

  // Parse and render structured content
  const renderMessageContent = (content) => {
    try {
      // Try to parse JSON data from response
      const jsonMatch = content.match(/\{[\s\S]*?"success"\s*:\s*true[\s\S]*?\}/);
      
      if (jsonMatch) {
        const data = JSON.parse(jsonMatch[0]);
        
        // Sprint Status Analytics
        if (data.sprint_status) {
          const sprint = data.sprint_status;
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Sparkles size={20} className="content-icon" />
                <h3>📅 Sprint Status</h3>
              </div>
              <div className="analytics-grid">
                <div className="metric-card">
                  <div className="metric-value">{sprint.committed}</div>
                  <div className="metric-label">Committed</div>
                </div>
                <div className="metric-card success">
                  <div className="metric-value">{sprint.completed}</div>
                  <div className="metric-label">Completed</div>
                </div>
                <div className="metric-card warning">
                  <div className="metric-value">{sprint.remaining}</div>
                  <div className="metric-label">Remaining</div>
                </div>
                <div className="metric-card info">
                  <div className="metric-value">{sprint.in_progress}</div>
                  <div className="metric-label">In Progress</div>
                </div>
                {sprint.blocked > 0 && (
                  <div className="metric-card danger">
                    <div className="metric-value">{sprint.blocked}</div>
                    <div className="metric-label">Blocked</div>
                  </div>
                )}
              </div>
              <div className="progress-section">
                <div className="progress-label">Sprint Completion</div>
                <div className="progress-bar-large">
                  <div className="progress-fill-large" style={{ width: `${sprint.completion}%` }}>
                    {sprint.completion.toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          );
        }
        
        // Team Workload Analytics
        if (data.team_workload) {
          const workload = data.team_workload;
          const maxTasks = Math.max(...Object.values(workload));
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Github size={20} className="content-icon" />
                <h3>👥 Team Workload</h3>
              </div>
              <div className="workload-chart">
                {Object.entries(workload).map(([member, count]) => (
                  <div key={member} className="workload-bar-container">
                    <div className="workload-member">{member}</div>
                    <div className="workload-bar-wrapper">
                      <div 
                        className={`workload-bar ${count > 10 ? 'overloaded' : ''}`}
                        style={{ width: `${(count / maxTasks) * 100}%` }}
                      >
                        <span className="workload-count">{count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }
        
        // Bug Metrics Analytics
        if (data.bug_metrics) {
          const bugs = data.bug_metrics;
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Mail size={20} className="content-icon" />
                <h3>🐞 Bug Metrics</h3>
              </div>
              <div className="analytics-grid">
                <div className="metric-card">
                  <div className="metric-value">{bugs.total_bugs}</div>
                  <div className="metric-label">Total Bugs</div>
                </div>
                <div className="metric-card warning">
                  <div className="metric-value">{bugs.open_bugs}</div>
                  <div className="metric-label">Open Bugs</div>
                </div>
                <div className="metric-card danger">
                  <div className="metric-value">{bugs.critical_bugs}</div>
                  <div className="metric-label">Critical</div>
                </div>
                <div className="metric-card info">
                  <div className="metric-value">{bugs.bug_ratio.toFixed(2)}</div>
                  <div className="metric-label">Bug/Story Ratio</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{bugs.avg_resolution.toFixed(1)}d</div>
                  <div className="metric-label">Avg Resolution</div>
                </div>
              </div>
            </div>
          );
        }
        
        // Velocity Trend Analytics
        if (data.velocity_trend) {
          const velocity = data.velocity_trend;
          const maxVel = Math.max(...velocity.velocities.map(v => v.value));
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Sparkles size={20} className="content-icon" />
                <h3>📈 Velocity Trend</h3>
              </div>
              <div className="velocity-chart">
                {velocity.velocities.map((sprint, idx) => (
                  <div key={idx} className="velocity-bar-container">
                    <div className="velocity-bar-wrapper">
                      <div 
                        className="velocity-bar"
                        style={{ height: `${(sprint.value / maxVel) * 100}%` }}
                      >
                        <span className="velocity-value">{sprint.value.toFixed(0)}</span>
                      </div>
                    </div>
                    <div className="velocity-label">{sprint.name}</div>
                  </div>
                ))}
              </div>
              <div className="velocity-summary">
                <div className="summary-item">
                  <strong>Trend:</strong> 
                  <span className={`trend-badge ${velocity.trend}`}>{velocity.trend}</span>
                </div>
                <div className="summary-item">
                  <strong>Average:</strong> {velocity.average.toFixed(1)} hours
                </div>
              </div>
            </div>
          );
        }
        
        // Release Status Analytics
        if (data.release_status) {
          const release = data.release_status;
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Github size={20} className="content-icon" />
                <h3>🚀 Release Status: {release.name}</h3>
              </div>
              <div className="release-overview">
                <div className="release-circle">
                  <svg viewBox="0 0 100 100" className="progress-ring">
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="rgba(255,255,255,0.1)"
                      strokeWidth="10"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="url(#gradient)"
                      strokeWidth="10"
                      strokeDasharray={`${release.progress * 2.827} 282.7`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#667eea" />
                        <stop offset="100%" stopColor="#764ba2" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="progress-text">
                    <div className="progress-percent">{release.progress.toFixed(0)}%</div>
                    <div className="progress-subtext">Complete</div>
                  </div>
                </div>
                <div className="release-details">
                  <div className="detail-row">
                    <span className="detail-label">Total Scope:</span>
                    <span className="detail-value">{release.total} items</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Completed:</span>
                    <span className="detail-value success">{release.completed} items</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Unresolved:</span>
                    <span className="detail-value warning">{release.unresolved} items</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Due Date:</span>
                    <span className="detail-value">{release.due_date}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        }
        
        // Backlog Analytics
        if (data.backlog_metrics) {
          const backlog = data.backlog_metrics;
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Sparkles size={20} className="content-icon" />
                <h3>📊 Backlog Metrics</h3>
              </div>
              <div className="analytics-grid">
                <div className="metric-card">
                  <div className="metric-value">{backlog.total}</div>
                  <div className="metric-label">Total Items</div>
                </div>
                <div className="metric-card danger">
                  <div className="metric-value">{backlog.high_priority}</div>
                  <div className="metric-label">High Priority</div>
                </div>
                <div className="metric-card warning">
                  <div className="metric-value">{backlog.unestimated}</div>
                  <div className="metric-label">Unestimated</div>
                </div>
                <div className="metric-card info">
                  <div className="metric-value">{backlog.avg_age_days}d</div>
                  <div className="metric-label">Avg Age</div>
                </div>
              </div>
              
              <div className="charts-row">
                <div className="chart-container">
                  <div className="chart-title">Priority Distribution</div>
                  <div className="donut-chart">
                    <svg viewBox="0 0 100 100" className="donut-svg">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="rgba(239, 68, 68, 0.3)"
                        strokeWidth="20"
                        strokeDasharray={`${backlog.high_priority_percent * 2.513} 251.3`}
                        transform="rotate(-90 50 50)"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="rgba(59, 130, 246, 0.3)"
                        strokeWidth="20"
                        strokeDasharray={`${(100 - backlog.high_priority_percent) * 2.513} 251.3`}
                        strokeDashoffset={`-${backlog.high_priority_percent * 2.513}`}
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="donut-center">
                      <div className="donut-percent">{backlog.high_priority_percent.toFixed(0)}%</div>
                      <div className="donut-label">High Priority</div>
                    </div>
                  </div>
                </div>
                
                <div className="chart-container">
                  <div className="chart-title">Estimation Status</div>
                  <div className="donut-chart">
                    <svg viewBox="0 0 100 100" className="donut-svg">
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="rgba(251, 191, 36, 0.3)"
                        strokeWidth="20"
                        strokeDasharray={`${backlog.unestimated_percent * 2.513} 251.3`}
                        transform="rotate(-90 50 50)"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="40"
                        fill="none"
                        stroke="rgba(34, 197, 94, 0.3)"
                        strokeWidth="20"
                        strokeDasharray={`${(100 - backlog.unestimated_percent) * 2.513} 251.3`}
                        strokeDashoffset={`-${backlog.unestimated_percent * 2.513}`}
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="donut-center">
                      <div className="donut-percent">{backlog.unestimated_percent.toFixed(0)}%</div>
                      <div className="donut-label">Unestimated</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="monthly-trend">
                <div className="trend-item added">
                  <div className="trend-icon">📥</div>
                  <div className="trend-content">
                    <div className="trend-value">{backlog.added_this_month}</div>
                    <div className="trend-label">Added This Month</div>
                  </div>
                </div>
                <div className="trend-item closed">
                  <div className="trend-icon">✅</div>
                  <div className="trend-content">
                    <div className="trend-value">{backlog.closed_this_month}</div>
                    <div className="trend-label">Closed This Month</div>
                  </div>
                </div>
              </div>
            </div>
          );
        }
        
        // Cycle Time Metrics
        if (data.cycle_metrics) {
          const cycle = data.cycle_metrics;
          const maxTime = Math.max(cycle.avg_lead_time_days, cycle.avg_cycle_time_days);
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Github size={20} className="content-icon" />
                <h3>⏱️ Cycle Time Metrics</h3>
              </div>
              <div className="time-comparison">
                <div className="time-bar-container">
                  <div className="time-label">Lead Time</div>
                  <div className="time-bar-wrapper">
                    <div 
                      className="time-bar lead-time"
                      style={{ width: `${(cycle.avg_lead_time_days / maxTime) * 100}%` }}
                    >
                      <span className="time-value">{cycle.avg_lead_time_days} days</span>
                    </div>
                  </div>
                </div>
                <div className="time-bar-container">
                  <div className="time-label">Cycle Time</div>
                  <div className="time-bar-wrapper">
                    <div 
                      className="time-bar cycle-time"
                      style={{ width: `${(cycle.avg_cycle_time_days / maxTime) * 100}%` }}
                    >
                      <span className="time-value">{cycle.avg_cycle_time_days} days</span>
                    </div>
                  </div>
                </div>
              </div>
              {cycle.reopened_tickets > 0 && (
                <div className="reopened-alert">
                  <span className="alert-icon">⚠️</span>
                  <span className="alert-text">{cycle.reopened_tickets} tickets were reopened</span>
                </div>
              )}
            </div>
          );
        }
        
        // Throughput Analysis
        if (data.throughput) {
          const throughput = data.throughput;
          return (
            <div className="structured-content analytics-dashboard">
              <div className="content-header">
                <Sparkles size={20} className="content-icon" />
                <h3>📊 Throughput Analysis</h3>
              </div>
              <div className="throughput-comparison">
                <div className="throughput-bar created">
                  <div className="throughput-label">Created</div>
                  <div className="throughput-value">{throughput.created}</div>
                  <div className="throughput-visual" style={{ width: `${(throughput.created / Math.max(throughput.created, throughput.closed)) * 100}%` }}></div>
                </div>
                <div className="throughput-bar closed">
                  <div className="throughput-label">Closed</div>
                  <div className="throughput-value">{throughput.closed}</div>
                  <div className="throughput-visual" style={{ width: `${(throughput.closed / Math.max(throughput.created, throughput.closed)) * 100}%` }}></div>
                </div>
              </div>
              <div className="throughput-summary">
                <div className={`net-badge ${throughput.net >= 0 ? 'positive' : 'negative'}`}>
                  {throughput.net >= 0 ? '✅' : '⚠️'} Net: {throughput.net > 0 ? '+' : ''}{throughput.net} tickets
                </div>
                <div className="throughput-status">
                  {throughput.net >= 0 ? 'Closing more than creating' : 'Creating more than closing'}
                </div>
              </div>
            </div>
          );
        }
        
        // Redmine Issues List
        if (data.issues && Array.isArray(data.issues)) {
          return (
            <div className="structured-content">
              <div className="content-header">
                <Mail size={20} className="content-icon" />
                <h3>Redmine Issues ({data.count})</h3>
              </div>
              <div className="issues-list">
                {data.issues.slice(0, 10).map((issue) => (
                  <div key={issue.id} className="issue-card">
                    <div className="issue-header">
                      <span className="issue-id">#{issue.id}</span>
                      <span className={`issue-status status-${issue.status?.toLowerCase().replace(' ', '-')}`}>
                        {issue.status}
                      </span>
                      <span className={`issue-priority priority-${issue.priority?.toLowerCase()}`}>
                        {issue.priority}
                      </span>
                    </div>
                    <div className="issue-title">{issue.subject}</div>
                    <div className="issue-meta">
                      <span>📁 {issue.project}</span>
                      {issue.assigned_to && <span>👤 {issue.assigned_to}</span>}
                      <span>📅 {new Date(issue.updated_on).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        }
        
        // Redmine Projects List
        if (data.projects && Array.isArray(data.projects)) {
          return (
            <div className="structured-content">
              <div className="content-header">
                <Github size={20} className="content-icon" />
                <h3>Redmine Projects ({data.count})</h3>
              </div>
              <div className="projects-grid">
                {data.projects.map((project) => (
                  <div key={project.id} className="project-card">
                    <div className="project-name">{project.name}</div>
                    <div className="project-id">ID: {project.identifier}</div>
                    {project.description && (
                      <div className="project-desc">{project.description.substring(0, 100)}...</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        }
        
        // Single Redmine Issue
        if (data.issue && data.issue.id) {
          const issue = data.issue;
          return (
            <div className="structured-content">
              <div className="content-header">
                <Mail size={20} className="content-icon" />
                <h3>Issue #{issue.id}</h3>
              </div>
              <div className="issue-detail">
                <div className="issue-detail-header">
                  <h2>{issue.subject}</h2>
                  <div className="issue-badges">
                    <span className={`badge status-${issue.status?.toLowerCase().replace(' ', '-')}`}>
                      {issue.status}
                    </span>
                    <span className={`badge priority-${issue.priority?.toLowerCase()}`}>
                      {issue.priority}
                    </span>
                  </div>
                </div>
                <div className="issue-detail-body">
                  <p>{issue.description}</p>
                </div>
                <div className="issue-detail-meta">
                  <div className="meta-item">
                    <strong>Project:</strong> {issue.project}
                  </div>
                  <div className="meta-item">
                    <strong>Tracker:</strong> {issue.tracker}
                  </div>
                  {issue.assigned_to && (
                    <div className="meta-item">
                      <strong>Assigned to:</strong> {issue.assigned_to}
                    </div>
                  )}
                  <div className="meta-item">
                    <strong>Author:</strong> {issue.author}
                  </div>
                  <div className="meta-item">
                    <strong>Created:</strong> {new Date(issue.created_on).toLocaleString()}
                  </div>
                  <div className="meta-item">
                    <strong>Updated:</strong> {new Date(issue.updated_on).toLocaleString()}
                  </div>
                  {issue.done_ratio !== undefined && (
                    <div className="meta-item">
                      <strong>Progress:</strong>
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${issue.done_ratio}%` }}>
                          {issue.done_ratio}%
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        }
        
        // Search Results (DuckDuckGo, Google)
        if (data.results && Array.isArray(data.results)) {
          return (
            <div className="structured-content">
              <div className="content-header">
                <Sparkles size={20} className="content-icon" />
                <h3>Search Results ({data.result_count || data.total_results})</h3>
              </div>
              <div className="search-results">
                {data.results.slice(0, 8).map((result, idx) => (
                  <div key={idx} className="search-result-card">
                    <a href={result.link || result.url} target="_blank" rel="noopener noreferrer" className="result-title">
                      {result.title}
                    </a>
                    <div className="result-url">{result.domain || new URL(result.link || result.url).hostname}</div>
                    {result.snippet && <div className="result-snippet">{result.snippet}</div>}
                  </div>
                ))}
              </div>
            </div>
          );
        }
      }
    } catch (e) {
      // If parsing fails, fall back to plain text
      console.log('Could not parse structured content:', e);
    }
    
    // Default: render as plain text
    return <div className="plain-text">{content}</div>;
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversationHistory,
          enabledTools,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      console.log('=== RESPONSE DATA ===');
      console.log('Full response:', data.response);
      console.log('====================');
      
      // Check if response contains music playback action
      let musicPlayed = false;
      try {
        // Method 1: Try to find complete JSON with PLAY_MUSIC action (including nested objects)
        const jsonPattern = /\{[\s\S]*?"action"\s*:\s*"PLAY_MUSIC"[\s\S]*?"track"\s*:\s*\{[\s\S]*?\}[\s\S]*?\}/;
        const jsonMatch = data.response.match(jsonPattern);
        console.log('JSON match found:', jsonMatch);
        
        if (jsonMatch) {
          try {
            const musicData = JSON.parse(jsonMatch[0]);
            console.log('Parsed music data:', musicData);
            if (musicData.track && musicData.track.previewUrl) {
              console.log('Playing track:', musicData.track);
              playTrack(musicData.track);
              musicPlayed = true;
            }
          } catch (e) {
            console.log('Failed to parse music data:', e);
          }
        }
        
        // Method 2: Extract individual fields if JSON parsing fails
        if (!musicPlayed) {
          console.log('Trying field extraction method...');
          const previewMatch = data.response.match(/"previewUrl"\s*:\s*"([^"]+)"/);
          const nameMatch = data.response.match(/"name"\s*:\s*"([^"]+)"/);
          const artistMatch = data.response.match(/"artist"\s*:\s*"([^"]+)"/);
          const artworkMatch = data.response.match(/"artworkUrl"\s*:\s*"([^"]+)"/);
          
          console.log('Field matches:', { previewMatch, nameMatch, artistMatch, artworkMatch });
          
          if (previewMatch) {
            const track = {
              previewUrl: previewMatch[1],
              name: nameMatch ? nameMatch[1] : 'Unknown Track',
              artist: artistMatch ? artistMatch[1] : 'Unknown Artist',
              artworkUrl: artworkMatch ? artworkMatch[1] : 'https://via.placeholder.com/100',
            };
            console.log('Playing track (extracted):', track);
            playTrack(track);
            musicPlayed = true;
          }
        }
        
        if (!musicPlayed) {
          console.log('No music data found in response');
        }
      } catch (e) {
        console.error('Error processing music data:', e);
      }

      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      setConversationHistory(data.conversationHistory);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const examplePrompts = [
    { icon: Mail, text: 'List my recent emails', color: '#ff6b6b' },
    { icon: Music, text: 'Play some jazz', color: '#1db954' },
    { icon: Github, text: 'Show my GitHub repos', color: '#6e5494' },
  ];

  const toolCategories = [
    { 
      id: 'music', 
      name: 'Music Tools', 
      description: 'Play music, search songs, get artist info',
      icon: Music,
      color: '#1db954'
    },
    { 
      id: 'playwright', 
      name: 'Web Automation', 
      description: 'Browse websites, search, scrape products',
      icon: Github,
      color: '#6e5494'
    },
    { 
      id: 'redmine', 
      name: 'Redmine', 
      description: 'Manage projects, issues, and tasks',
      icon: Mail,
      color: '#ff6b6b'
    },
  ];

  const toggleTool = (toolId) => {
    // Prevent disabling Redmine if DB cache is enabled
    if (toolId === 'redmine' && enabledTools[toolId] && redmineDbEnabled) {
      const confirmDisable = window.confirm(
        'Redmine DB cache is currently enabled. Disabling Redmine tools will prevent analytics from working.\n\nDo you want to disable both Redmine tools and Redmine DB cache?'
      );
      
      if (confirmDisable) {
        // Disable both
        toggleRedmineDb(false);
        setEnabledTools(prev => ({
          ...prev,
          [toolId]: false
        }));
      }
      return;
    }
    
    setEnabledTools(prev => ({
      ...prev,
      [toolId]: !prev[toolId]
    }));
  };

  // Test music player
  const testMusicPlayer = () => {
    const testTrack = {
      name: 'Test Song',
      artist: 'Test Artist',
      previewUrl: 'https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/3d/07/37/3d073731-8b8e-3c54-4c5f-8e6f5f4e5e5e/mzaf_1234567890.plus.aac.p.m4a',
      artworkUrl: 'https://via.placeholder.com/100',
    };
    console.log('Testing music player with:', testTrack);
    playTrack(testTrack);
  };

  return (
    <div className="app">
      {currentTrack && (
        <div className="music-player">
          <img src={currentTrack.artworkUrl} alt={currentTrack.name} className="album-art" />
          <div className="track-info">
            <div className="track-name">{currentTrack.name}</div>
            <div className="track-artist">{currentTrack.artist}</div>
          </div>
          <button onClick={togglePlayPause} className="play-btn">
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
        </div>
      )}

      {showToolsPanel && (
        <div className="tools-panel-overlay" onClick={() => setShowToolsPanel(false)}>
          <div className="tools-panel" onClick={(e) => e.stopPropagation()}>
            <div className="tools-panel-header">
              <h2>Tool Settings</h2>
              <button className="close-btn" onClick={() => setShowToolsPanel(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="tools-panel-content">
              <p className="tools-description">
                Enable or disable tool categories. Disabled tools won't be available to the AI.
              </p>
              
              {/* Redmine DB Cache Toggle */}
              <div className="tool-category redmine-db-section">
                <div className="tool-category-info">
                  <div className="tool-category-icon" style={{ backgroundColor: '#e74c3c' }}>
                    <span style={{ fontSize: '20px' }}>🗄️</span>
                  </div>
                  <div className="tool-category-text">
                    <h3>Redmine DB Cache</h3>
                    <p>Enable fast analytics with in-memory cache (loads 1000 issues)</p>
                    {redmineDbEnabled && (
                      <small style={{ color: '#3498db', display: 'block', marginTop: '4px' }}>
                        ℹ️ Redmine tools are auto-enabled when cache is on
                      </small>
                    )}
                    {redmineDbStatus && redmineDbStatus.initialized && (
                      <div className="cache-status">
                        <small>
                          📊 {redmineDbStatus.counts?.issues || 0} issues cached
                          {redmineDbStatus.age_seconds && (
                            <> • Updated {Math.floor(redmineDbStatus.age_seconds / 60)}m ago</>
                          )}
                        </small>
                      </div>
                    )}
                  </div>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={redmineDbEnabled}
                    onChange={(e) => toggleRedmineDb(e.target.checked)}
                    disabled={redmineDbLoading}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              
              {/* Loading Progress */}
              {redmineDbLoading && (
                <div className="cache-loading">
                  <div className="loading-header">
                    <Loader2 className="spin" size={16} />
                    <span>Loading Redmine cache...</span>
                  </div>
                  <div className="progress-bar-cache">
                    <div 
                      className="progress-fill-cache" 
                      style={{ width: `${cacheLoadProgress}%` }}
                    ></div>
                  </div>
                  <small>{cacheLoadProgress}% complete</small>
                </div>
              )}
              
              <div className="tools-divider"></div>
              
              {toolCategories.map((category) => (
                <div key={category.id} className="tool-category">
                  <div className="tool-category-info">
                    <div className="tool-category-icon" style={{ backgroundColor: category.color }}>
                      <category.icon size={20} />
                    </div>
                    <div className="tool-category-text">
                      <h3>
                        {category.name}
                        {category.id === 'redmine' && redmineDbEnabled && (
                          <span style={{ fontSize: '0.7rem', color: '#3498db', marginLeft: '8px' }}>
                            (auto-enabled)
                          </span>
                        )}
                      </h3>
                      <p>{category.description}</p>
                    </div>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={enabledTools[category.id]}
                      onChange={() => toggleTool(category.id)}
                      disabled={category.id === 'redmine' && redmineDbEnabled}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      <div className="container">
        <header className="header">
          <div className="header-content">
            <Sparkles className="header-icon" />
            <h1>MCP Integration Platform</h1>
            <p>AI-powered assistant with Gmail, Spotify & GitHub</p>
          </div>
          <button className="settings-btn" onClick={() => setShowToolsPanel(true)}>
            <Settings size={20} />
          </button>
        </header>

        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">
                <Sparkles size={48} />
              </div>
              <h2>Welcome! How can I help you today?</h2>
              <p>Try one of these examples:</p>
              <div className="examples">
                {examplePrompts.map((prompt, index) => (
                  <button
                    key={index}
                    className="example-btn"
                    onClick={() => setInput(prompt.text)}
                    style={{ '--accent-color': prompt.color }}
                  >
                    <prompt.icon size={20} />
                    <span>{prompt.text}</span>
                  </button>
                ))}
                <button
                  className="example-btn test-btn"
                  onClick={testMusicPlayer}
                  style={{ '--accent-color': '#ff9800' }}
                >
                  <Play size={20} />
                  <span>Test Music Player</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <div className="message-content">
                    {message.role === 'assistant' ? renderMessageContent(message.content) : message.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message assistant">
                  <div className="message-content loading">
                    <Loader2 className="spinner" />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <form className="input-form" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask me anything..."
            disabled={isLoading}
            className="input-field"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="send-btn"
          >
            {isLoading ? (
              <Loader2 className="spinner" size={20} />
            ) : (
              <Send size={20} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
