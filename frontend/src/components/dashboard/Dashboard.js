import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, MemoryStick, Network, HardDrive, Users, Bot, CheckCircle, Shield } from 'lucide-react';
// Design system component (inline for now)
const Card = ({ children, className = '', style = {} }) => (
  <div className={className} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 12, padding: 16, ...style }}>
    {children}
  </div>
);
import { useRealTimeMetrics } from '../../hooks/useRealTimeMetrics';
import { analyticsAPI, memoryAPI, jobsAPI, dreamingAPI } from '../../api/asimnexus';
// import '../styles/glassmorphism.css';
// Colors defined locally
const colors = {
  accent: {
    pink: { 500: '#ec4899' },
    cyan: { 500: '#06b6d4' },
    violet: { 500: '#8b5cf6' },
    emerald: { 500: '#10b981' },
    rose: { 500: '#f43f5e' },
    sky: { 500: '#0ea5e9' },
    lime: { 500: '#84cc16' },
    fuchsia: { 500: '#d946ef' }
  }
};

const metricColors = [
  colors.accent.pink[500],
  colors.accent.cyan[500],
  colors.accent.violet[500],
  colors.accent.emerald[500],
  colors.accent.rose[500],
  colors.accent.sky[500],
  colors.accent.lime[500],
  colors.accent.fuchsia[500],
];

const Dashboard = () => {
  const { metrics, isConnected, lastUpdate } = useRealTimeMetrics();

  const [activityData, setActivityData] = useState([]);
  const [taskDistribution, setTaskDistribution] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [dreamBriefing, setDreamBriefing] = useState(null);

  const COLORS = [colors.accent.pink[500], colors.accent.cyan[500], colors.accent.violet[500], colors.accent.rose[500], colors.accent.sky[500]];

  useEffect(() => {
    async function loadDashboardData() {
      try {
        // 1. Analytics overview
        const overviewRes = await analyticsAPI.getOverview();
        const overviewData = overviewRes.data;
        if (overviewData) setAnalyticsData(overviewData);
      } catch (_) { }

      try {
        // 2. Analytics activity
        const activityRes = await analyticsAPI.getActivity();
        const activityData = activityRes.data;
        if (activityData?.activity) {
          setActivityData(activityData.activity.map(d => ({
            time: d.time,
            founders: d.clones ?? 0,
            agents: d.messages ?? 0,
            tasks: d.tasks ?? 0,
          })));
        }
      } catch (_) { }

      try {
        // 3. Jobs stats → task distribution pie chart
        const jobsRes = await jobsAPI.getStats();
        const data = jobsRes.data;
        if (data) {
          const dist = [
            { name: 'Open Jobs', value: data.open_jobs || 0, color: colors.accent.pink[500] },
            { name: 'Completed', value: data.completed_jobs || 0, color: colors.accent.cyan[500] },
            { name: 'Assigned', value: Math.max(0, (data.total_jobs || 0) - (data.open_jobs || 0) - (data.completed_jobs || 0)), color: colors.accent.violet[500] },
            { name: 'Agents', value: data.total_agents || 0, color: colors.accent.rose[500] },
          ].filter(d => d.value > 0);
          if (dist.length > 0) setTaskDistribution(dist);
        }
      } catch (_) { }

      try {
        // 4. Dreaming briefing
        const dreamRes = await dreamingAPI.getBriefing();
        const dreamData = dreamRes.data;
        if (dreamData?.briefing) setDreamBriefing(dreamData.briefing);
      } catch (_) { }

      try {
        // 5. Recent memory activity
        const memRes = await memoryAPI.getRecent(20);
        const memData = memRes.data;
        if (memData?.memories) {
          setRecentActivity(memData.memories.slice(0, 6).map(m => ({
            time: new Date(m.timestamp * 1000).toLocaleTimeString(),
            text: m.content?.slice(0, 80) || '',
          })));
        }
      } catch (_) { }
    }

    loadDashboardData();
  }, []);

  return (
    <motion.div
      className="dashboard glass-panel glass-noise"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="dashboard-header">
        <h2>System Overview</h2>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`} />
          {isConnected ? 'Live' : 'Simulated'}
          {lastUpdate && <span className="last-update">Updated: {lastUpdate.toLocaleTimeString()}</span>}
        </div>
      </div>

      <div className="metrics-grid">
        <Card variant="elevated" hover className="metric-card glass-card glass-noise" style={{ borderColor: colors.accent.pink[500] }}>
          <div className="metric-icon cpu" style={{ color: colors.accent.pink[500] }}>
            <Cpu size={24} />
          </div>
          <h3>CPU Usage</h3>
          <motion.div
            className="metric-value"
            key={metrics.cpu}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.pink[500] }}
          >
            {metrics.cpu != null ? `${metrics.cpu}%` : '—'}
          </motion.div>
          <div className="metric-bar">
            <motion.div
              className="metric-fill cpu"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.cpu}%` }}
              transition={{ duration: 0.5 }}
              style={{ background: `linear-gradient(90deg, ${colors.accent.pink[400]}, ${colors.accent.pink[600]})` }}
            />
          </div>
        </Card>

        <Card variant="elevated" hover className="metric-card glass-card glass-noise" style={{ borderColor: colors.accent.cyan[500] }}>
          <div className="metric-icon memory" style={{ color: colors.accent.cyan[500] }}>
            <MemoryStick size={24} />
          </div>
          <h3>Memory Usage</h3>
          <motion.div
            className="metric-value"
            key={metrics.memory}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.cyan[500] }}
          >
            {metrics.memory != null ? `${metrics.memory}%` : '—'}
          </motion.div>
          <div className="metric-bar">
            <motion.div
              className="metric-fill memory"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.memory}%` }}
              transition={{ duration: 0.5 }}
              style={{ background: `linear-gradient(90deg, ${colors.accent.cyan[400]}, ${colors.accent.cyan[600]})` }}
            />
          </div>
        </Card>

        <Card variant="elevated" hover className="metric-card glass-card glass-noise" style={{ borderColor: colors.accent.violet[500] }}>
          <div className="metric-icon network" style={{ color: colors.accent.violet[500] }}>
            <Network size={24} />
          </div>
          <h3>Network</h3>
          <motion.div
            className="metric-value"
            key={metrics.network}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.violet[500] }}
          >
            {metrics.network != null ? `${metrics.network}%` : '—'}
          </motion.div>
          <div className="metric-bar">
            <motion.div
              className="metric-fill network"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.network}%` }}
              transition={{ duration: 0.5 }}
              style={{ background: `linear-gradient(90deg, ${colors.accent.violet[400]}, ${colors.accent.violet[600]})` }}
            />
          </div>
        </Card>

        <Card variant="elevated" hover className="metric-card glass-card glass-noise" style={{ borderColor: colors.accent.emerald[500] }}>
          <div className="metric-icon storage" style={{ color: colors.accent.emerald[500] }}>
            <HardDrive size={24} />
          </div>
          <h3>Storage</h3>
          <motion.div
            className="metric-value"
            key={metrics.storage}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.emerald[500] }}
          >
            {metrics.storage != null ? `${metrics.storage}%` : '—'}
          </motion.div>
          <div className="metric-bar">
            <motion.div
              className="metric-fill storage"
              initial={{ width: 0 }}
              animate={{ width: `${metrics.storage}%` }}
              transition={{ duration: 0.5 }}
              style={{ background: `linear-gradient(90deg, ${colors.accent.emerald[400]}, ${colors.accent.emerald[600]})` }}
            />
          </div>
        </Card>
      </div>

      <div className="additional-metrics-grid">
        <Card variant="elevated" className="additional-metric-card glass-card glass-noise" style={{ borderColor: colors.accent.rose[500] }}>
          <div className="metric-icon founders" style={{ color: colors.accent.rose[500] }}>
            <Users size={24} />
          </div>
          <h3>Active Founders</h3>
          <motion.div
            className="metric-value"
            key={metrics.activeFounders}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.rose[500] }}
          >
            {metrics.activeFounders != null ? `${metrics.activeFounders}/15` : '—'}
          </motion.div>
        </Card>

        <Card variant="elevated" className="additional-metric-card glass-card glass-noise" style={{ borderColor: colors.accent.sky[500] }}>
          <div className="metric-icon agents" style={{ color: colors.accent.sky[500] }}>
            <Bot size={24} />
          </div>
          <h3>Active Agents</h3>
          <motion.div
            className="metric-value"
            key={metrics.activeAgents}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.sky[500] }}
          >
            {metrics.activeAgents ?? '—'}
          </motion.div>
        </Card>

        <Card variant="elevated" className="additional-metric-card glass-card glass-noise" style={{ borderColor: colors.accent.lime[500] }}>
          <div className="metric-icon tasks" style={{ color: colors.accent.lime[500] }}>
            <CheckCircle size={24} />
          </div>
          <h3>Tasks Completed</h3>
          <motion.div
            className="metric-value"
            key={metrics.tasksCompleted}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.lime[500] }}
          >
            {metrics.tasksCompleted ?? '—'}
          </motion.div>
        </Card>

        <Card variant="elevated" className="additional-metric-card glass-card glass-noise" style={{ borderColor: colors.accent.fuchsia[500] }}>
          <div className="metric-icon ethical" style={{ color: colors.accent.fuchsia[500] }}>
            <Shield size={24} />
          </div>
          <h3>Ethical Score</h3>
          <motion.div
            className="metric-value"
            key={metrics.ethicalScore}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            style={{ color: colors.accent.fuchsia[500] }}
          >
            {metrics.ethicalScore != null ? `${(metrics.ethicalScore * 100).toFixed(0)}%` : '—'}
          </motion.div>
        </Card>
      </div>

      <div className="charts-grid">
        <Card variant="elevated" className="chart-card glass-card glass-noise">
          <h3>Activity Over Time</h3>
          {activityData.length === 0 ? (
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.35, fontSize: '0.85rem' }}>
              Chat use गर्नुस् — data यहाँ देखिनेछ
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#3a3a4e" />
                <XAxis dataKey="time" stroke="#a0a0b0" />
                <YAxis stroke="#a0a0b0" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 15, 26, 0.9)',
                    borderColor: '#3a3a4e',
                    color: '#f5f5f5'
                  }}
                />
                <Legend wrapperStyle={{ color: '#f5f5f5' }} />
                <Area type="monotone" dataKey="founders" stackId="1" stroke={colors.accent.pink[500]} fill={colors.accent.pink[500]} name="Founders" />
                <Area type="monotone" dataKey="agents" stackId="1" stroke={colors.accent.violet[500]} fill={colors.accent.violet[500]} name="Agents" />
                <Area type="monotone" dataKey="tasks" stackId="1" stroke={colors.accent.cyan[500]} fill={colors.accent.cyan[500]} name="Tasks" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card variant="elevated" className="chart-card glass-card glass-noise">
          <h3>Task Distribution</h3>
          {taskDistribution.length === 0 ? (
            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.35, fontSize: '0.85rem' }}>
              Jobs post गर्नुस् — data यहाँ देखिनेछ
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={taskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => (
                    <text fill="#f5f5f5" stroke="none" fontSize={12}>
                      {`${name} ${(percent * 100).toFixed(0)}%`}
                    </text>
                  )}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {taskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 15, 26, 0.9)',
                    borderColor: '#3a3a4e',
                    color: '#f5f5f5'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {recentActivity.length > 0 && (
        <Card variant="elevated" className="recent-activity glass-card glass-noise">
          <h3>Recent Activity</h3>
          <ul>
            {recentActivity.map((item, i) => (
              <li key={i}><span className="timestamp">{item.time}</span> — {item.text}</li>
            ))}
          </ul>
        </Card>
      )}

      {dreamBriefing && (
        <Card variant="elevated" className="glass-card glass-noise" style={{ marginTop: 16, padding: '16px 20px' }}>
          <h3 style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8, fontSize: '1rem' }}>
            🌙 AI Dream Briefing
            <span style={{ fontSize: '0.65rem', opacity: 0.4, fontWeight: 400 }}>रातभरको सिकाइ</span>
          </h3>
          <p style={{ fontSize: '0.85rem', opacity: 0.75, lineHeight: 1.7, margin: 0 }}>{dreamBriefing}</p>
        </Card>
      )}
    </motion.div>
  );
};

export default Dashboard;
