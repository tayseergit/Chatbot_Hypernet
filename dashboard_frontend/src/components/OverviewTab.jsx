import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  Activity,
  ShieldCheck,
  Search,
  Server,
  XCircle
} from 'lucide-react';
import AgentActionLogsTab from './AgentActionLogsTab';
import { useAuth } from '../context/AuthContext';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function StatCard({ label, value, sub, icon: Icon, iconColor, iconBg }) {
  return (
    <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '18px' }}>
      <div style={{ width: 52, height: 52, borderRadius: 12, background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={26} color={iconColor} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 2 }}>{value}</div>
      </div>
    </div>
  );
}

export default function OverviewTab({ setActiveTab }) {
  const { admin } = useAuth();
  const [stats, setStats] = useState({
    total_sessions: 0,
    active_sessions: 0,
    total_actions: 0,
    health: {
      bot: 'جاري الفحص...', bot_latency: '...',
      llm: 'جاري الفحص...', llm_latency: '...',
      crm: 'جاري الفحص...', crm_latency: '...'
    },
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const statsRes = await fetch(`${API}/api/overview/stats`);
      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
    } catch (err) {
      console.warn('Backend API error:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const intervalId = setInterval(loadData, 10 * 60 * 1000); // 10 minutes
    return () => clearInterval(intervalId);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24, maxWidth: '100%', overflow: 'hidden' }}>

      {/* ── رأس الصفحة الرئيسي ── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 16,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 22px'
      }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
            لوحة التحكم الرئيسية
          </h1>
        </div>

      </div>

      {/* ── بطاقات الإحصائيات المباشرة ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <StatCard
          label="إجمالي المشتركين والجلسات"
          value={stats.total_sessions.toLocaleString()}
          icon={MessageSquare}
          iconColor="var(--info)"
          iconBg="rgba(0, 184, 217, 0.12)"
        />

        <StatCard
          label="المشتركون الموثقون"
          value={stats.authed_sessions !== undefined ? stats.authed_sessions.toLocaleString() : stats.active_sessions.toLocaleString()}
          icon={ShieldCheck}
          iconColor="var(--text-secondary)"
          iconBg="#f1f5f9"
        />

        <StatCard
          label="إجمالي العمليات المنفذة"
          value={stats.total_actions.toLocaleString()}
          icon={Activity}
          iconColor="var(--primary)"
          iconBg="rgba(0, 167, 111, 0.12)"
        />

      </div>

      {/* ── مراقبة صحة النظام ── */}
      <div className="hcn-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ width: 42, height: 42, borderRadius: 10, background: 'rgba(99, 102, 241, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Server size={22} color="var(--primary)" />
          </div>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>مراقبة صحة النظام</h3>

          </div>
        </div>

        <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
          <table className="hcn-table">
            <thead>
              <tr>
                <th>الخدمة / المكون</th>
                <th>الحالة</th>
                <th>زمن الاستجابة (Ping)</th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: 'حالة توافر البوت (Bot API)', status: stats.health?.bot, ping: stats.health?.bot_latency },
                { name: 'اتصالية نظام العملاء (CRM API)', status: stats.health?.crm, ping: stats.health?.crm_latency },
                { name: 'حالة خدمة الذكاء الاصطناعي (LLM)', status: stats.health?.llm, ping: stats.health?.llm_latency }
              ].map((item, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{item.name}</td>
                  <td>
                    {item.status === 'متصل' ? (
                      <span className="hcn-badge hcn-badge-success" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <CheckCircle2 size={14} /> متصل
                      </span>
                    ) : item.status === 'جاري الفحص...' || isRefreshing ? (
                      <span className="hcn-badge" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: 'var(--bg-paper)', color: 'var(--text-secondary)' }}>
                        <RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> جاري الفحص...
                      </span>
                    ) : (
                      <span className="hcn-badge hcn-badge-error" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <XCircle size={14} /> {item.status || 'غير متصل'}
                      </span>
                    )}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontWeight: 700, color: item.status === 'متصل' ? 'var(--primary)' : 'var(--text-secondary)' }}>
                    {isRefreshing ? '...' : item.ping}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── دمج صفحة سجل العمليات التفصيلي داخل الرئيسية ── */}
      {admin?.permissions?.includes('view_system_logs') && (
        <div style={{ marginTop: 4 }}>
          <AgentActionLogsTab />
        </div>
      )}

    </div>
  );
}
