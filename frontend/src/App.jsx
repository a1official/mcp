import { useState, useRef, useEffect } from 'react';
import {
  Send, Loader2, Sparkles, Music, Github, Play, Pause, Settings, X,
  BarChart3, Bug, Users, Clock, Rocket, TrendingUp, Activity,
  FolderKanban, Hash, AlertTriangle, CheckCircle2, Circle, ArrowUpRight,
  ArrowDownRight, Minus, ChevronRight, ListTodo, Tag, Calendar, User,
  Layers
} from 'lucide-react';
import './App.css';

/* ------------------------------------------------------------------ */
/*  Utility helpers                                                    */
/* ------------------------------------------------------------------ */
const fmtDate = (d) => {
  if (!d) return '--';
  try { return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
  catch { return d; }
};
const pct = (n, t) => (t > 0 ? ((n / t) * 100).toFixed(1) : '0');
const safeNum = (v) => (typeof v === 'number' ? v : 0);

/* ------------------------------------------------------------------ */
/*  Structured content renderers                                       */
/* ------------------------------------------------------------------ */

/* -- Sprint Analytics Card -- */
function SprintCard({ data }) {
  const m = data.metrics || {};
  const sprint = data.sprint || {};
  const byStatus = data.breakdown_by_status || {};
  const assess = data.burndown_assessment || '';
  const assessColor = assess === 'on_track' ? 'var(--accent-green)' : assess === 'at_risk' ? 'var(--accent-amber)' : 'var(--accent-red)';

  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon sprint"><BarChart3 size={18} /></div>
          <div>
            <h3 className="card-title">Sprint Analytics</h3>
            <span className="card-subtitle">{sprint.name || 'Current Sprint'}{sprint.due_date ? ` \u2022 Due ${fmtDate(sprint.due_date)}` : ''}</span>
          </div>
        </div>
        <span className="status-pill" style={{ background: assessColor + '22', color: assessColor, borderColor: assessColor + '44' }}>
          {assess.replace('_', ' ')}
        </span>
      </div>
      <div className="metric-grid cols-4">
        <MetricTile label="Committed" value={safeNum(m.total_committed)} variant="default" />
        <MetricTile label="Completed" value={safeNum(m.completed)} variant="success" />
        <MetricTile label="In Progress" value={safeNum(m.in_progress)} variant="info" />
        <MetricTile label="Blocked" value={safeNum(m.blocked)} variant="danger" />
      </div>
      <div className="progress-section">
        <div className="progress-header">
          <span className="progress-label">Completion</span>
          <span className="progress-pct">{safeNum(m.completion_percentage)}%</span>
        </div>
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${Math.min(safeNum(m.completion_percentage), 100)}%` }} />
        </div>
      </div>
      {Object.keys(byStatus).length > 0 && (
        <div className="breakdown-row">
          {Object.entries(byStatus).map(([status, count]) => (
            <span key={status} className="breakdown-chip">{status}: <strong>{count}</strong></span>
          ))}
        </div>
      )}
      {(m.total_estimated_hours > 0 || m.total_spent_hours > 0) && (
        <div className="hours-row">
          <span className="hours-item">Est: <strong>{safeNum(m.total_estimated_hours)}h</strong></span>
          <span className="hours-item">Spent: <strong>{safeNum(m.total_spent_hours)}h</strong></span>
        </div>
      )}
    </div>
  );
}

/* -- Backlog Analytics Card -- */
function BacklogCard({ data }) {
  const bl = data.backlog || {};
  const aging = data.aging || {};
  const monthly = data.monthly_activity || {};
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon backlog"><ListTodo size={18} /></div>
          <div>
            <h3 className="card-title">Backlog Analytics</h3>
            <span className="card-subtitle">{monthly.month || ''}</span>
          </div>
        </div>
      </div>
      <div className="metric-grid cols-4">
        <MetricTile label="Open Items" value={safeNum(bl.total_open)} variant="default" />
        <MetricTile label="High Priority" value={safeNum(bl.high_priority_open)} variant="danger" />
        <MetricTile label="Unestimated" value={`${safeNum(bl.unestimated_percentage)}%`} variant="warning" />
        <MetricTile label="Avg Age" value={`${safeNum(aging.average_days_open)}d`} variant="info" />
      </div>
      {(monthly.created_this_month !== undefined) && (
        <div className="monthly-row">
          <div className="monthly-item created">
            <ArrowUpRight size={16} />
            <span>Created: <strong>{safeNum(monthly.created_this_month)}</strong></span>
          </div>
          <div className="monthly-item closed">
            <ArrowDownRight size={16} />
            <span>Closed: <strong>{safeNum(monthly.closed_this_month)}</strong></span>
          </div>
          <div className={`monthly-item ${safeNum(monthly.net_change) <= 0 ? 'closed' : 'created'}`}>
            <Minus size={16} />
            <span>Net: <strong>{monthly.net_change > 0 ? '+' : ''}{safeNum(monthly.net_change)}</strong></span>
          </div>
        </div>
      )}
    </div>
  );
}

/* -- Team Workload Card -- */
function WorkloadCard({ data }) {
  const workload = data.workload_by_member || {};
  const overloaded = data.overloaded_members || {};
  const entries = Object.entries(workload);
  const maxVal = Math.max(...entries.map(([,v]) => v), 1);
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon workload"><Users size={18} /></div>
          <div>
            <h3 className="card-title">Team Workload</h3>
            <span className="card-subtitle">{data.team_size || entries.length} members \u2022 {safeNum(data.total_open_issues)} open \u2022 {safeNum(data.unassigned_issues)} unassigned</span>
          </div>
        </div>
      </div>
      <div className="workload-bars">
        {entries.slice(0, 12).map(([name, count]) => {
          const isOver = overloaded[name] !== undefined;
          return (
            <div key={name} className="wl-row">
              <span className={`wl-name ${isOver ? 'overloaded' : ''}`}>{name}</span>
              <div className="wl-track">
                <div className={`wl-fill ${isOver ? 'over' : ''}`} style={{ width: `${(count / maxVal) * 100}%` }}>
                  <span className="wl-count">{count}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* -- Quality / Bug Metrics Card -- */
function QualityCard({ data }) {
  const bm = data.bug_metrics || {};
  const crit = bm.critical_open || {};
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon quality"><Bug size={18} /></div>
          <div>
            <h3 className="card-title">Quality Metrics</h3>
            <span className="card-subtitle">Bug-to-story ratio: {bm.bug_to_story_ratio ?? 'N/A'}</span>
          </div>
        </div>
      </div>
      <div className="metric-grid cols-4">
        <MetricTile label="Open Bugs" value={safeNum(bm.open_bugs)} variant="warning" />
        <MetricTile label="Closed Bugs" value={safeNum(bm.closed_bugs)} variant="success" />
        <MetricTile label="Total Bugs" value={safeNum(bm.total_bugs)} variant="default" />
        <MetricTile label="Critical Open" value={safeNum(crit.total_critical)} variant="danger" />
      </div>
      {(crit.high > 0 || crit.urgent > 0 || crit.immediate > 0) && (
        <div className="breakdown-row">
          {crit.high > 0 && <span className="breakdown-chip warning">High: {crit.high}</span>}
          {crit.urgent > 0 && <span className="breakdown-chip danger">Urgent: {crit.urgent}</span>}
          {crit.immediate > 0 && <span className="breakdown-chip danger">Immediate: {crit.immediate}</span>}
        </div>
      )}
    </div>
  );
}

/* -- Cycle Time Card -- */
function CycleTimeCard({ data }) {
  const lead = data.lead_time || {};
  const cycle = data.cycle_time || {};
  const reopen = data.reopened_tickets || {};
  const maxDays = Math.max(safeNum(lead.average_days), safeNum(cycle.average_days), 1);
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon cycle"><Clock size={18} /></div>
          <div>
            <h3 className="card-title">Cycle Time</h3>
            <span className="card-subtitle">Sample: {safeNum(data.sample_size)} closed issues</span>
          </div>
        </div>
      </div>
      <div className="time-bars">
        <div className="time-row">
          <span className="time-label">Lead Time</span>
          <div className="time-track">
            <div className="time-fill lead" style={{ width: `${(safeNum(lead.average_days) / maxDays) * 100}%` }}>
              {lead.average_days != null ? `${lead.average_days} days` : '--'}
            </div>
          </div>
        </div>
        <div className="time-row">
          <span className="time-label">Cycle Time</span>
          <div className="time-track">
            <div className="time-fill cycle" style={{ width: `${(safeNum(cycle.average_days) / maxDays) * 100}%` }}>
              {cycle.average_days != null ? `${cycle.average_days} days` : '--'}
            </div>
          </div>
        </div>
      </div>
      {safeNum(reopen.count) > 0 && (
        <div className="alert-row warning">
          <AlertTriangle size={16} />
          <span>{reopen.count} tickets reopened ({reopen.percentage}%)</span>
        </div>
      )}
    </div>
  );
}

/* -- Release Status Card -- */
function ReleaseCard({ data }) {
  const releases = data.releases || [];
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon release"><Rocket size={18} /></div>
          <div>
            <h3 className="card-title">Release Status</h3>
            <span className="card-subtitle">{releases.length} version(s)</span>
          </div>
        </div>
      </div>
      <div className="release-list">
        {releases.map((r, i) => (
          <div key={i} className="release-item">
            <div className="release-item-header">
              <span className="release-name">{r.version_name}</span>
              <span className="release-pct">{safeNum(r.completion_percentage)}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${Math.min(safeNum(r.completion_percentage), 100)}%` }} />
            </div>
            <div className="release-meta">
              <span>Total: {r.total_issues}</span>
              <span>Closed: {r.closed_issues}</span>
              <span>Open: {r.open_issues}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Velocity Trend Card -- */
function VelocityCard({ data }) {
  const sprints = data.per_sprint || [];
  const maxCompleted = Math.max(...sprints.map(s => s.completed_issues), 1);
  const trend = data.velocity_trend || 'stable';
  const TrendIcon = trend === 'increasing' ? ArrowUpRight : trend === 'decreasing' ? ArrowDownRight : Minus;
  const trendColor = trend === 'increasing' ? 'var(--accent-green)' : trend === 'decreasing' ? 'var(--accent-red)' : 'var(--accent-blue)';
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon velocity"><TrendingUp size={18} /></div>
          <div>
            <h3 className="card-title">Velocity Trend</h3>
            <span className="card-subtitle">{sprints.length} sprints analyzed \u2022 Avg: {data.average_velocity}</span>
          </div>
        </div>
        <span className="status-pill" style={{ background: trendColor + '22', color: trendColor, borderColor: trendColor + '44' }}>
          <TrendIcon size={14} /> {trend}
        </span>
      </div>
      <div className="velocity-bars">
        {sprints.map((s, i) => (
          <div key={i} className="vel-col">
            <div className="vel-bar-wrap">
              <div className="vel-bar" style={{ height: `${(s.completed_issues / maxCompleted) * 100}%` }}>
                <span className="vel-val">{s.completed_issues}</span>
              </div>
            </div>
            <span className="vel-label" title={s.sprint}>{s.sprint?.slice(0, 12)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Throughput Card -- */
function ThroughputCard({ data }) {
  const weekly = data.weekly_breakdown || [];
  const trend = data.trend || '';
  const trendColor = trend === 'positive' ? 'var(--accent-green)' : 'var(--accent-red)';
  return (
    <div className="card analytics-card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon throughput"><Activity size={18} /></div>
          <div>
            <h3 className="card-title">Throughput</h3>
            <span className="card-subtitle">{data.period_weeks} weeks \u2022 Avg {data.avg_created_per_week}/wk created, {data.avg_closed_per_week}/wk closed</span>
          </div>
        </div>
        <span className="status-pill" style={{ background: trendColor + '22', color: trendColor, borderColor: trendColor + '44' }}>
          Net: {data.net_throughput > 0 ? '+' : ''}{safeNum(data.net_throughput)}
        </span>
      </div>
      <div className="throughput-table">
        <div className="tp-header-row">
          <span>Week</span><span>Created</span><span>Closed</span><span>Net</span>
        </div>
        {weekly.map((w, i) => (
          <div key={i} className="tp-row">
            <span className="tp-week">{w.week}</span>
            <span className="tp-created">{w.created}</span>
            <span className="tp-closed">{w.closed}</span>
            <span className={`tp-net ${w.net >= 0 ? 'pos' : 'neg'}`}>{w.net > 0 ? '+' : ''}{w.net}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Issues List Card -- */
function IssuesCard({ data }) {
  const issues = data.issues || [];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon issues"><FolderKanban size={18} /></div>
          <div>
            <h3 className="card-title">Issues</h3>
            <span className="card-subtitle">Showing {issues.length} of {safeNum(data.total_count)}</span>
          </div>
        </div>
      </div>
      <div className="issues-list">
        {issues.slice(0, 15).map((issue) => (
          <div key={issue.id} className="issue-row">
            <div className="issue-row-top">
              <span className="issue-id">#{issue.id}</span>
              {issue.tracker && <span className="chip tracker">{issue.tracker}</span>}
              {issue.status && <StatusChip status={issue.status} />}
              {issue.priority && <PriorityChip priority={issue.priority} />}
            </div>
            <div className="issue-subject">{issue.subject}</div>
            <div className="issue-row-meta">
              {issue.project && <span><FolderKanban size={12} /> {issue.project}</span>}
              {issue.assigned_to && <span><User size={12} /> {issue.assigned_to}</span>}
              {issue.version && <span><Tag size={12} /> {issue.version}</span>}
              {issue.updated_on && <span><Calendar size={12} /> {fmtDate(issue.updated_on)}</span>}
              {issue.done_ratio > 0 && <span><CheckCircle2 size={12} /> {issue.done_ratio}%</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Projects List Card -- */
function ProjectsCard({ data }) {
  const projects = data.projects || [];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon projects"><Layers size={18} /></div>
          <div>
            <h3 className="card-title">Projects</h3>
            <span className="card-subtitle">{safeNum(data.count)} projects</span>
          </div>
        </div>
      </div>
      <div className="projects-grid">
        {projects.map((p) => (
          <div key={p.id} className="project-tile">
            <div className="project-tile-header">
              <span className="project-name">{p.name}</span>
              <span className="project-id">{p.identifier}</span>
            </div>
            {p.description && <p className="project-desc">{(p.description || '').slice(0, 120)}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Versions List Card -- */
function VersionsCard({ data }) {
  const versions = data.versions || [];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon versions"><Tag size={18} /></div>
          <div>
            <h3 className="card-title">Versions / Sprints</h3>
            <span className="card-subtitle">{safeNum(data.count)} versions</span>
          </div>
        </div>
      </div>
      <div className="versions-list">
        {versions.map((v) => (
          <div key={v.id} className="version-row">
            <span className="version-name">{v.name}</span>
            <StatusChip status={v.status || 'open'} />
            {v.due_date && <span className="version-due">{fmtDate(v.due_date)}</span>}
            <span className="version-id">ID: {v.id}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Single Issue Detail Card -- */
function IssueDetailCard({ data }) {
  const issue = data.issue || data;
  const journals = issue.journals || [];
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon issues"><Hash size={18} /></div>
          <div>
            <h3 className="card-title">Issue #{issue.id}</h3>
            <span className="card-subtitle">{issue.tracker} \u2022 {issue.project}</span>
          </div>
        </div>
        <div className="chip-group">
          {issue.status && <StatusChip status={issue.status} />}
          {issue.priority && <PriorityChip priority={issue.priority} />}
        </div>
      </div>
      <h4 className="issue-detail-subject">{issue.subject}</h4>
      {issue.description && <div className="issue-detail-desc">{issue.description}</div>}
      <div className="detail-grid">
        {issue.assigned_to && <DetailItem label="Assignee" value={issue.assigned_to} />}
        {issue.author && <DetailItem label="Author" value={issue.author} />}
        {issue.version && <DetailItem label="Version" value={issue.version} />}
        <DetailItem label="Created" value={fmtDate(issue.created_on)} />
        <DetailItem label="Updated" value={fmtDate(issue.updated_on)} />
        {issue.estimated_hours != null && <DetailItem label="Estimated" value={`${issue.estimated_hours}h`} />}
        {issue.done_ratio != null && (
          <div className="detail-item span-2">
            <span className="detail-label">Progress</span>
            <div className="progress-track sm">
              <div className="progress-fill" style={{ width: `${issue.done_ratio}%` }} />
            </div>
            <span className="detail-value">{issue.done_ratio}%</span>
          </div>
        )}
      </div>
      {journals.length > 0 && (
        <div className="journal-section">
          <h5 className="journal-title">Recent Activity</h5>
          {journals.slice(-5).map((j) => (
            <div key={j.id} className="journal-entry">
              <div className="journal-header">
                <span className="journal-user">{j.user}</span>
                <span className="journal-date">{fmtDate(j.created_on)}</span>
              </div>
              {j.notes && <p className="journal-notes">{j.notes}</p>}
              {j.details && j.details.length > 0 && (
                <div className="journal-details">
                  {j.details.map((d, idx) => (
                    <span key={idx} className="journal-change">{d.name}: {d.old_value || '--'} &rarr; {d.new_value || '--'}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* -- Trackers / Statuses List -- */
function SimpleListCard({ title, icon: Icon, items, labelKey = 'name', idKey = 'id' }) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-header-left">
          <div className="card-icon default"><Icon size={18} /></div>
          <h3 className="card-title">{title}</h3>
        </div>
      </div>
      <div className="simple-list">
        {items.map((item) => (
          <div key={item[idKey]} className="simple-list-item">
            <span className="simple-list-name">{item[labelKey]}</span>
            <span className="simple-list-id">ID: {item[idKey]}</span>
            {item.is_closed !== undefined && (
              <span className={`chip ${item.is_closed ? 'closed' : 'open'}`}>{item.is_closed ? 'Closed' : 'Open'}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* -- Tiny reusable components -- */
function MetricTile({ label, value, variant = 'default' }) {
  return (
    <div className={`metric-tile ${variant}`}>
      <div className="metric-tile-value">{value}</div>
      <div className="metric-tile-label">{label}</div>
    </div>
  );
}

function StatusChip({ status }) {
  const s = (status || '').toLowerCase().replace(/\s+/g, '-');
  const cls = s.includes('closed') || s.includes('resolved') ? 'success'
    : s.includes('progress') ? 'info'
    : s.includes('feedback') || s.includes('blocked') ? 'warning'
    : s.includes('new') || s.includes('open') ? 'primary'
    : 'default';
  return <span className={`chip ${cls}`}>{status}</span>;
}

function PriorityChip({ priority }) {
  const p = (priority || '').toLowerCase();
  const cls = p === 'urgent' || p === 'immediate' ? 'danger'
    : p === 'high' ? 'warning'
    : p === 'low' ? 'muted'
    : 'default';
  return <span className={`chip ${cls}`}>{priority}</span>;
}

function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main App                                                           */
/* ------------------------------------------------------------------ */
function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showToolsPanel, setShowToolsPanel] = useState(false);
  const [enabledTools, setEnabledTools] = useState({ music: true, playwright: true, redmine: true });
  const messagesEndRef = useRef(null);
  const audioRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.addEventListener('ended', () => setIsPlaying(false));
    audioRef.current.addEventListener('play', () => setIsPlaying(true));
    audioRef.current.addEventListener('pause', () => setIsPlaying(false));
    return () => { if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; } };
  }, []);

  const playTrack = (track) => {
    if (audioRef.current && track.previewUrl) {
      audioRef.current.src = track.previewUrl;
      audioRef.current.play().then(() => { setCurrentTrack(track); setIsPlaying(true); }).catch(() => {});
    }
  };
  const togglePlayPause = () => { if (audioRef.current) { isPlaying ? audioRef.current.pause() : audioRef.current.play(); } };

  /* ---- Parse structured data from assistant response ---- */
  const tryParseStructured = (content) => {
    // 1. Try to find JSON blocks in content
    const jsonBlocks = [];
    // Match {... "success": true ...} patterns
    const regex = /\{[\s\S]*?"success"\s*:\s*true[\s\S]*?\}(?=\s*(?:[^{]|$))/g;
    let match;
    // More robust: try to find the largest JSON object
    let braceDepth = 0;
    let start = -1;
    for (let i = 0; i < content.length; i++) {
      if (content[i] === '{') {
        if (braceDepth === 0) start = i;
        braceDepth++;
      } else if (content[i] === '}') {
        braceDepth--;
        if (braceDepth === 0 && start !== -1) {
          const candidate = content.slice(start, i + 1);
          try {
            const parsed = JSON.parse(candidate);
            if (parsed.success === true) jsonBlocks.push(parsed);
          } catch {}
          start = -1;
        }
      }
    }
    return jsonBlocks;
  };

  const renderMessageContent = (content) => {
    try {
      const blocks = tryParseStructured(content);
      if (blocks.length > 0) {
        const cards = [];
        const textParts = [];

        for (const data of blocks) {
          // Sprint analytics (new format)
          if (data.sprint && data.metrics) {
            cards.push(<SprintCard key={`sprint-${cards.length}`} data={data} />);
          }
          // Backlog analytics (new format)
          else if (data.backlog) {
            cards.push(<BacklogCard key={`backlog-${cards.length}`} data={data} />);
          }
          // Team workload (new format)
          else if (data.workload_by_member) {
            cards.push(<WorkloadCard key={`workload-${cards.length}`} data={data} />);
          }
          // Quality / bug metrics (new format)
          else if (data.bug_metrics) {
            cards.push(<QualityCard key={`quality-${cards.length}`} data={data} />);
          }
          // Cycle time (new format)
          else if (data.lead_time || data.cycle_time) {
            cards.push(<CycleTimeCard key={`cycle-${cards.length}`} data={data} />);
          }
          // Release status (new format)
          else if (data.releases && Array.isArray(data.releases)) {
            cards.push(<ReleaseCard key={`release-${cards.length}`} data={data} />);
          }
          // Velocity trend (new format)
          else if (data.per_sprint || data.velocity_trend) {
            cards.push(<VelocityCard key={`velocity-${cards.length}`} data={data} />);
          }
          // Throughput (new format)
          else if (data.weekly_breakdown) {
            cards.push(<ThroughputCard key={`tp-${cards.length}`} data={data} />);
          }
          // Issue detail
          else if (data.issue && data.issue.id) {
            cards.push(<IssueDetailCard key={`detail-${cards.length}`} data={data} />);
          }
          // Issues list
          else if (data.issues && Array.isArray(data.issues)) {
            cards.push(<IssuesCard key={`issues-${cards.length}`} data={data} />);
          }
          // Projects list
          else if (data.projects && Array.isArray(data.projects)) {
            cards.push(<ProjectsCard key={`projects-${cards.length}`} data={data} />);
          }
          // Versions list
          else if (data.versions && Array.isArray(data.versions)) {
            cards.push(<VersionsCard key={`versions-${cards.length}`} data={data} />);
          }
          // Trackers
          else if (data.trackers && Array.isArray(data.trackers)) {
            cards.push(<SimpleListCard key={`trackers-${cards.length}`} title="Trackers" icon={Layers} items={data.trackers} />);
          }
          // Statuses
          else if (data.statuses && Array.isArray(data.statuses)) {
            cards.push(<SimpleListCard key={`statuses-${cards.length}`} title="Issue Statuses" icon={Circle} items={data.statuses} />);
          }
          // Members / Users
          else if (data.members && Array.isArray(data.members)) {
            cards.push(<SimpleListCard key={`members-${cards.length}`} title="Members" icon={Users} items={data.members} />);
          }
          else if (data.users && Array.isArray(data.users)) {
            cards.push(<SimpleListCard key={`users-${cards.length}`} title="Users" icon={Users} items={data.users} />);
          }
          // Search results
          else if (data.results && Array.isArray(data.results)) {
            cards.push(
              <div key={`search-${cards.length}`} className="card">
                <div className="card-header">
                  <div className="card-header-left">
                    <div className="card-icon default"><Sparkles size={18} /></div>
                    <h3 className="card-title">Search Results ({data.result_count || data.total_results})</h3>
                  </div>
                </div>
                <div className="search-results">
                  {data.results.slice(0, 8).map((result, idx) => (
                    <a key={idx} href={result.link || result.url} target="_blank" rel="noopener noreferrer" className="search-item">
                      <span className="search-title">{result.title}</span>
                      {result.snippet && <span className="search-snippet">{result.snippet}</span>}
                    </a>
                  ))}
                </div>
              </div>
            );
          }
          // Success message (issue created/updated/deleted)
          else if (data.message) {
            cards.push(
              <div key={`msg-${cards.length}`} className="card success-card">
                <CheckCircle2 size={20} />
                <span>{data.message}</span>
              </div>
            );
          }
        }

        // Strip JSON from text content
        let textContent = content;
        for (const block of blocks) {
          const jsonStr = JSON.stringify(block);
          // Remove the JSON from the text (approximate)
          // This is a best-effort approach
        }

        // Get surrounding text (remove JSON blocks from content)
        let cleanText = content;
        // Simple heuristic: remove everything between { and matching }
        let cleaned = '';
        let depth = 0;
        let inJson = false;
        for (let i = 0; i < content.length; i++) {
          if (content[i] === '{') {
            depth++;
            inJson = true;
          } else if (content[i] === '}') {
            depth--;
            if (depth === 0) { inJson = false; continue; }
          }
          if (!inJson && depth === 0) cleaned += content[i];
        }
        cleanText = cleaned.trim();

        if (cards.length > 0) {
          return (
            <div className="structured-response">
              {cleanText && <div className="response-text">{cleanText}</div>}
              <div className="cards-stack">{cards}</div>
            </div>
          );
        }
      }
    } catch (e) {
      // fall through to plain text
    }
    return <div className="response-text">{content}</div>;
  };

  /* ---- Send message ---- */
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, conversationHistory, enabledTools }),
      });
      if (!response.ok) throw new Error('Failed to get response');
      const data = await response.json();

      // Check for music
      try {
        const previewMatch = data.response.match(/"previewUrl"\s*:\s*"([^"]+)"/);
        const nameMatch = data.response.match(/"name"\s*:\s*"([^"]+)"/);
        const artistMatch = data.response.match(/"artist"\s*:\s*"([^"]+)"/);
        const artworkMatch = data.response.match(/"artworkUrl"\s*:\s*"([^"]+)"/);
        if (previewMatch) {
          playTrack({
            previewUrl: previewMatch[1],
            name: nameMatch ? nameMatch[1] : 'Unknown Track',
            artist: artistMatch ? artistMatch[1] : 'Unknown Artist',
            artworkUrl: artworkMatch ? artworkMatch[1] : '',
          });
        }
      } catch {}

      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      setConversationHistory(data.conversationHistory);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const examplePrompts = [
    { icon: FolderKanban, text: 'List all Redmine projects', color: '#3b82f6' },
    { icon: BarChart3, text: 'Show sprint analytics for ncel', color: '#8b5cf6' },
    { icon: Bug, text: 'How many bugs are open?', color: '#ef4444' },
    { icon: Users, text: 'Show team workload', color: '#10b981' },
  ];

  const toolCategories = [
    { id: 'music', name: 'Music Tools', description: 'Play music, search songs, get artist info', icon: Music, color: '#22c55e' },
    { id: 'playwright', name: 'Web Automation', description: 'Browse websites, search, scrape products', icon: Github, color: '#8b5cf6' },
    { id: 'redmine', name: 'Redmine', description: 'Projects, issues, sprints, analytics, quality', icon: FolderKanban, color: '#3b82f6' },
  ];

  const toggleTool = (toolId) => {
    setEnabledTools(prev => ({ ...prev, [toolId]: !prev[toolId] }));
  };

  return (
    <div className="app">
      {/* Music Player */}
      {currentTrack && (
        <div className="music-player">
          {currentTrack.artworkUrl && <img src={currentTrack.artworkUrl} alt={currentTrack.name} crossOrigin="anonymous" className="album-art" />}
          <div className="track-info">
            <div className="track-name">{currentTrack.name}</div>
            <div className="track-artist">{currentTrack.artist}</div>
          </div>
          <button onClick={togglePlayPause} className="play-btn">{isPlaying ? <Pause size={18} /> : <Play size={18} />}</button>
        </div>
      )}

      {/* Tools Panel Modal */}
      {showToolsPanel && (
        <div className="tools-overlay" onClick={() => setShowToolsPanel(false)}>
          <div className="tools-panel" onClick={(e) => e.stopPropagation()}>
            <div className="tools-panel-header">
              <h2>Tool Settings</h2>
              <button className="icon-btn" onClick={() => setShowToolsPanel(false)}><X size={18} /></button>
            </div>
            <div className="tools-panel-body">
              <p className="tools-desc">Enable or disable tool categories. Disabled tools will not be available to the AI.</p>
              {toolCategories.map((cat) => (
                <div key={cat.id} className="tool-row">
                  <div className="tool-row-info">
                    <div className="tool-icon" style={{ background: cat.color + '22', color: cat.color }}><cat.icon size={18} /></div>
                    <div>
                      <span className="tool-name">{cat.name}</span>
                      <span className="tool-desc">{cat.description}</span>
                    </div>
                  </div>
                  <label className="toggle">
                    <input type="checkbox" checked={enabledTools[cat.id]} onChange={() => toggleTool(cat.id)} />
                    <span className="toggle-track" />
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="container">
        <header className="header">
          <div className="header-left">
            <Sparkles className="header-icon" size={28} />
            <div>
              <h1 className="header-title">MCP Platform</h1>
              <p className="header-subtitle">Redmine AI Assistant</p>
            </div>
          </div>
          <button className="icon-btn settings" onClick={() => setShowToolsPanel(true)} aria-label="Settings">
            <Settings size={18} />
          </button>
        </header>

        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-orb"><Sparkles size={32} /></div>
              <h2 className="welcome-title">How can I help you today?</h2>
              <p className="welcome-sub">Ask about projects, issues, sprints, team workload, or quality metrics.</p>
              <div className="examples">
                {examplePrompts.map((p, i) => (
                  <button key={i} className="example-btn" onClick={() => setInput(p.text)}>
                    <p.icon size={16} style={{ color: p.color, flexShrink: 0 }} />
                    <span>{p.text}</span>
                    <ChevronRight size={14} className="example-arrow" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  {msg.role === 'assistant' && (
                    <div className="avatar assistant-avatar"><Sparkles size={14} /></div>
                  )}
                  <div className={`message-bubble ${msg.role}`}>
                    {msg.role === 'assistant' ? renderMessageContent(msg.content) : msg.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="message assistant">
                  <div className="avatar assistant-avatar"><Sparkles size={14} /></div>
                  <div className="message-bubble assistant loading-bubble">
                    <Loader2 className="spinner" size={16} />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <form className="input-bar" onSubmit={sendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about projects, sprints, bugs, workload..."
            disabled={isLoading}
            className="input-field"
          />
          <button type="submit" disabled={isLoading || !input.trim()} className="send-btn" aria-label="Send message">
            {isLoading ? <Loader2 className="spinner" size={18} /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
