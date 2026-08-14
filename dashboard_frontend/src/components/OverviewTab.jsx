import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  Activity,
  ShieldCheck,
  Search,
  Server
} from 'lucide-react';
import AgentActionLogsTab from './AgentActionLogsTab';

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
        {sub && <div style={{ fontSize: 11, color: 'var(--text-disabled)' }}>{sub}</div>}
      </div>
    </div>
  );
}

export default function OverviewTab({ setActiveTab }) {
  const [stats, setStats] = useState({
    total_sessions: 0,
    active_sessions: 0,
    total_actions: 0,
    health: { ollama: 'متصل', crm: 'متصل' },
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
            <span className="hcn-badge hcn-badge-success" style={{ fontSize: 11 }}>MySQL — مباشر</span>
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            <span>نظرة شاملة ومتابعة حية للعمليات والمؤشرات</span>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={isRefreshing}
          className="hcn-btn-primary"
          style={{ gap: 8, fontSize: 13, height: 38, fontWeight: 600 }}
        >
          <RefreshCw size={15} style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
          تحديث المؤشرات
        </button>
      </div>

      {/* ── بطاقات الإحصائيات المباشرة ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <StatCard
          label="إجمالي المشتركين والجلسات"
          value={stats.total_sessions.toLocaleString()}
          sub="سجلات الجلسات المعتمدة"
          icon={MessageSquare}
          iconColor="var(--info)"
          iconBg="rgba(0, 184, 217, 0.12)"
        />

        <StatCard
          label="المشتركون الموثقون"
          value={stats.active_sessions.toLocaleString()}
          sub="حسابات مربوطة بـ HyperCRM"
          icon={ShieldCheck}
          iconColor="var(--warning)"
          iconBg="rgba(255, 171, 0, 0.12)"
        />

        <StatCard
          label="إجمالي العمليات المنفذة"
          value={stats.total_actions.toLocaleString()}
          sub="سجلات العمليات في MySQL"
          icon={Activity}
          iconColor="var(--primary)"
          iconBg="rgba(0, 167, 111, 0.12)"
        />

        <div className="hcn-card" style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>حالة الخدمات</span>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CheckCircle2 size={16} color="var(--success)" />
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12 }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Ollama LLM</span>
            <span className="hcn-badge hcn-badge-success" style={{ fontSize: 10, padding: '1px 6px' }}>{stats.health?.ollama || 'متصل'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12 }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>HyperCRM API</span>
            <span className="hcn-badge hcn-badge-success" style={{ fontSize: 10, padding: '1px 6px' }}>{stats.health?.crm || 'متصل'}</span>
          </div>
        </div>
      </div>

      {/* ── دمج صفحة سجل العمليات التفصيلي داخل الرئيسية ── */}
      <div style={{ marginTop: 4 }}>
        <AgentActionLogsTab />
      </div>

    </div>
  );
}
