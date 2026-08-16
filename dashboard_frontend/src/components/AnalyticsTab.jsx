import React, { useState, useEffect } from 'react';
import { BarChart3, Clock, Activity, ArrowUpRight, Search, CheckCircle2, RefreshCw, Loader2 } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function StatCard({ label, value, sub, color = 'var(--text-primary)', iconBg, iconColor, icon: Icon }) {
  return (
    <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '18px' }}>
      {Icon && (
        <div style={{ width: 52, height: 52, borderRadius: 12, background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon size={26} color={iconColor} />
        </div>
      )}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 24, fontWeight: 800, color, marginBottom: 2 }}>{value}</div>
      </div>
    </div>
  );
}

function ProgressRow({ label, value, percent, color }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
        <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'monospace' }}>{label}</span>
        <span style={{ color: 'var(--text-secondary)', fontWeight: 700 }}>{value}</span>
      </div>
      <div style={{ width: '100%', height: 7, background: 'var(--bg-paper)', borderRadius: 4, overflow: 'hidden', border: '1px solid var(--border-color)' }}>
        <div style={{ height: '100%', borderRadius: 4, width: `${Math.min(100, Math.max(2, percent))}%`, background: color }} />
      </div>
    </div>
  );
}

function LatencyRow({ service, desc, value, color }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px',
      background: 'var(--bg-paper)',
      borderRadius: 10,
      border: '1px solid var(--border-color)',
    }}>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{service}</div>
        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{desc}</div>
      </div>
      <span style={{ fontSize: 16, fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</span>
    </div>
  );
}

export default function AnalyticsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAnalytics = () => {
    setLoading(true);
    fetch(`${API}/api/analytics/summary`)
      .then(r => r.json())
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load analytics:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAnalytics();
    const intervalId = setInterval(fetchAnalytics, 10 * 60 * 1000); // 10 minutes
    return () => clearInterval(intervalId);
  }, []);

  const totalActions = data?.total_actions ?? 0;
  const totalSessions = data?.total_sessions ?? 0;
  const authedSessions = data?.authed_sessions ?? 0;
  const topIntent = data?.top_intent || 'لا يوجد';
  const intents = data?.intents || [];
  const tools = data?.tools || [];

  const intentColors = ['var(--primary)', '#8B5CF6', 'var(--info)', '#64748b', 'var(--text-disabled)'];
  const toolColors = [
    { color: 'var(--primary)', bg: 'rgba(0, 167, 111, 0.12)' },
    { color: '#8B5CF6', bg: 'rgba(139, 92, 246, 0.12)' },
    { color: 'var(--info)', bg: 'rgba(0, 184, 217, 0.12)' },
    { color: '#64748b', bg: 'rgba(100, 116, 139, 0.12)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: '100%', overflow: 'hidden' }}>

      {/* ── رأس الصفحة الرسمي ── */}
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
          <h1 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            الإحصائيات والتقارير
          </h1>
        </div>

      </div>

      {/* ── بطاقات المؤشرات الرئيسية (بيانات حقيقية من MySQL) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
        <StatCard
          label="إجمالي العمليات المنفذة"
          value={totalActions.toLocaleString()}
          iconBg="rgba(0, 167, 111, 0.12)"
          iconColor="var(--primary)"
          icon={BarChart3}
        />
        <StatCard
          label="إجمالي المشتركين والجلسات"
          value={totalSessions.toLocaleString()}
          color="var(--info)"
          iconBg="rgba(0, 184, 217, 0.12)"
          iconColor="var(--info)"
          icon={Activity}
        />
        <StatCard
          label="المشتركون الموثقون"
          value={authedSessions.toLocaleString()}
          color="#64748b"
          iconBg="rgba(100, 116, 139, 0.12)"
          iconColor="#64748b"
          icon={Search}
        />
        <StatCard
          label="الخدمة الأكثر طلباً"
          value={topIntent}
          color="var(--success)"
          iconBg="rgba(34, 197, 94, 0.12)"
          iconColor="var(--success)"
          icon={CheckCircle2}
        />
      </div>

      {/* ── الرسوم البيانية وتوزيع الطلبات ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 18 }}>

        {/* توزيع النوايا الفعلي */}
        <div className="hcn-card" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid var(--border-color)', paddingBottom: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(0, 184, 217, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart3 size={20} color="var(--info)" />
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              توزيع الطلبات حسب التصنيف
            </h3>
          </div>

          {intents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-disabled)', fontSize: 13 }}>
              لا توجد عمليات مسجلة حتى الآن.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {intents.map((item, idx) => (
                <ProgressRow
                  key={idx}
                  label={item.label}
                  value={`${item.count} (${item.percent}%)`}
                  percent={item.percent}
                  color={intentColors[idx % intentColors.length]}
                />
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
