import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Box,
  BrainCircuit,
  Zap,
  Activity,
  Search,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
} from 'lucide-react';

function StatCard({ label, value, sub, icon: Icon, iconColor, iconBg, trend }) {
  return (
    <div className="hcn-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '24px' }}>
      <div style={{ width: 64, height: 64, borderRadius: '50%', background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={32} color={iconColor} />
      </div>
      <div style={{ flex: 1 }}>
        <div className="hcn-stat-label">{label}</div>
        <div className="hcn-stat-value" style={{ marginBottom: '8px' }}>{value}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {trend && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '4px',
              fontSize: '14px', fontWeight: 600,
              color: trend > 0 ? 'var(--success)' : 'var(--error)'
            }}>
              {trend > 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
              {Math.abs(trend)}%
            </span>
          )}
          {sub && <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{sub}</span>}
        </div>
      </div>
    </div>
  );
}

function ProgressRow({ label, percent, color }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 14 }}>
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>{label}</span>
        <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{percent}%</span>
      </div>
      <div style={{ width: '100%', height: 8, background: 'var(--bg-neutral)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', borderRadius: 4, width: `${percent}%`, background: color }} />
      </div>
    </div>
  );
}

export default function OverviewTab({ setActiveTab }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    total_sessions: 1284,
    active_sessions: 42,
    total_actions: 14892,
    top_intent: 'check_balance',
    avg_latency: '124ms',
    p95_latency: '210ms',
    health: { ollama: 'متصل', crm: 'متصل' },
  });
  const [recentActions, setRecentActions] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const statsRes = await fetch('http://localhost:8000/api/overview/stats');
      if (statsRes.ok) setStats(await statsRes.json());
      const actionsRes = await fetch('http://localhost:8000/api/actions?limit=5');
      if (actionsRes.ok) setRecentActions(await actionsRes.json());
    } catch (err) {
      console.warn('Backend API error, using cached data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const fallbackActions = [
    { type: 'CRM_TOOL',        tool: 'get_balance',       customerId: 'C001 (Ahmed Mohamed)',    intent: 'check_balance',          status: 'SUCCESS', timestamp: 'منذ 2 د' },
    { type: 'RAG_SEARCH',      tool: 'rag_service',       customerId: 'Query: "router restart"', intent: 'troubleshoot_slow_speed', status: 'SUCCESS', timestamp: 'منذ 5 د' },
    { type: 'INTENT_DECISION', tool: 'intent_classifier', customerId: 'Confidence: 0.95',        intent: 'check_balance',          status: 'SUCCESS', timestamp: 'منذ 8 د' },
    { type: 'CRM_TOOL',        tool: 'get_invoices',      customerId: 'C002 (Fatima Ali)',       intent: 'billing_invoices',       status: 'SUCCESS', timestamp: 'منذ 12 د' },
  ];

  const displayActions = recentActions.length > 0 ? recentActions : fallbackActions;
  const filteredActions = displayActions.filter(a =>
    (a.tool || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.customerId || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.intent || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
          <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            نظرة عامة على النظام
            <span className="hcn-badge hcn-badge-success">مباشر</span>
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>نظرة عامة</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ position: 'relative' }}>
            <Search size={20} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }} />
            <input
              type="text"
              placeholder="بحث في البيانات..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="hcn-input"
              style={{ paddingRight: 44, width: 280 }}
            />
          </div>
          <button onClick={loadData} disabled={isRefreshing} className="hcn-btn-primary">
            <RefreshCw size={20} style={{ animation: isRefreshing ? 'spin 1s linear infinite' : 'none' }} />
            تحديث البيانات
          </button>
        </div>
      </div>

      {/* ── بطاقات الإحصائيات ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
        <StatCard
          label="إجمالي الجلسات"
          value={stats.total_sessions.toLocaleString()}
          sub={`${stats.active_sessions} نشطة الآن`}
          icon={MessageSquare}
          iconColor="var(--info)"
          iconBg="var(--info-bg)"
          trend={12}
        />
        <StatCard
          label="إجمالي العمليات"
          value={stats.total_actions.toLocaleString()}
          sub="في قاعدة البيانات"
          icon={Box}
          iconColor="var(--warning)"
          iconBg="var(--warning-bg)"
          trend={5.4}
        />
        <StatCard
          label="متوسط زمن الاستجابة"
          value={stats.avg_latency}
          sub={`P95: ${stats.p95_latency}`}
          icon={Zap}
          iconColor="#8B5CF6"
          iconBg="rgba(139, 92, 246, 0.16)"
          trend={-8}
        />
        <div className="hcn-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)' }}>حالة النظام</span>
            <div style={{ width: 40, height: 40, borderRadius: '50%', background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <CheckCircle2 size={24} color="var(--success)" />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600 }}>Ollama LLM</span>
              <span className="hcn-badge hcn-badge-success">{stats.health.ollama}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600 }}>CRM API</span>
              <span className="hcn-badge hcn-badge-success">{stats.health.crm}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── الشبكة التفصيلية ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>
        {/* توزيع النوايا */}
        <div className="hcn-card" style={{ padding: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BrainCircuit size={24} color="var(--info)" />
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>توزيع نوايا المستخدمين</h2>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <ProgressRow label="check_balance — الاستفسار عن الرصيد"       percent={34} color="var(--info)" />
            <ProgressRow label="troubleshoot_slow_speed — الدعم الفني"      percent={28} color="var(--primary)" />
            <ProgressRow label="billing_invoices — الفواتير والمدفوعات"     percent={18} color="var(--warning)" />
            <ProgressRow label="check_package — الباقات والأسعار"           percent={12} color="#8B5CF6" />
            <ProgressRow label="general_inquiry — استفسارات أخرى"           percent={8}  color="var(--text-disabled)" />
          </div>
        </div>

        {/* آخر العمليات */}
        <div className="hcn-card" style={{ padding: 32 }}>
           <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--warning-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Activity size={24} color="var(--warning)" />
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>آخر العمليات</h2>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {filteredActions.map((act, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, paddingBottom: 16, borderBottom: i === filteredActions.length - 1 ? 'none' : '1px dashed var(--border)' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{act.tool}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{act.customerId}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-disabled)', marginTop: 4 }}>{act.timestamp}</div>
                </div>
                <span className="hcn-badge hcn-badge-success">{act.status}</span>
              </div>
            ))}
          </div>
          
          <button onClick={() => setActiveTab('actions')} className="hcn-btn-outlined" style={{ width: '100%', marginTop: 24 }}>
            عرض كل العمليات
          </button>
        </div>
      </div>
    </div>
  );
}
