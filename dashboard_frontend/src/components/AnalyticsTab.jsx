import React, { useState } from 'react';
import { BarChart3, Download, Clock, Activity, ArrowUpRight, ArrowDownRight, Search, CheckCircle2 } from 'lucide-react';

function StatCard({ label, value, sub, color = 'var(--text-primary)', trend, iconBg, iconColor, icon: Icon }) {
  return (
    <div className="hcn-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '24px' }}>
       {Icon && (
         <div style={{ width: 64, height: 64, borderRadius: '50%', background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Icon size={32} color={iconColor} />
        </div>
       )}
      <div style={{ flex: 1 }}>
        <div className="hcn-stat-label" style={{ marginBottom: 8 }}>{label}</div>
        <div className="hcn-stat-value" style={{ marginBottom: 8, color }}>{value}</div>
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

function ProgressRow({ label, value, percent, color }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 14 }}>
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600, fontFamily: 'monospace' }}>{label}</span>
        <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{value}</span>
      </div>
       <div style={{ width: '100%', height: 8, background: 'var(--bg-neutral)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', borderRadius: 4, width: `${percent}%`, background: color }} />
      </div>
    </div>
  );
}

function LatencyRow({ service, desc, value, color }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '16px',
      background: 'var(--bg-paper)',
      borderRadius: 12,
      border: '1px solid var(--border)',
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{service}</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{desc}</div>
      </div>
      <span style={{ fontSize: 18, fontWeight: 800, color, fontFamily: 'monospace' }}>{value}</span>
    </div>
  );
}

export default function AnalyticsTab() {
  const [timeframe, setTimeframe] = useState('24h');

  const queryCount = timeframe === '24h' ? '14,892' : timeframe === '7d' ? '94,120' : '382,400';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8 }}>الإحصائيات والتقارير</h1>
           <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>الإحصائيات</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="hcn-pill-group">
            {['24h', '7d', '30d'].map((tf) => (
              <button
                key={tf}
                className={`hcn-pill ${timeframe === tf ? 'active-primary' : ''}`}
                onClick={() => setTimeframe(tf)}
              >
                {tf === '24h' ? '24 ساعة' : tf === '7d' ? '7 أيام' : '30 يوم'}
              </button>
            ))}
          </div>
          <button
            onClick={() => alert('تم تصدير التقرير بنجاح!')}
            className="hcn-btn-primary"
          >
            <Download size={20} />
            تصدير التقرير
          </button>
        </div>
      </div>

      {/* ── بطاقات الإحصائيات ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
        <StatCard label="الطلبات المعالجة"  value={queryCount}  trend={14} iconBg="var(--primary-bg)" iconColor="var(--primary)" icon={BarChart3}/>
        <StatCard label="أدوات CRM المنفّذة" value="8,410" sub="56% من الطلبات" color="var(--info)" iconBg="var(--info-bg)" iconColor="var(--info)" icon={Activity} />
        <StatCard label="عمليات بحث RAG" value="4,120" sub="متوسط التطابق: 0.91" color="var(--warning)" iconBg="var(--warning-bg)" iconColor="var(--warning)" icon={Search} />
        <StatCard label="معدل الحل الناجح" value="98.4%" sub="التحويل: 1.6%" color="var(--success)" iconBg="var(--success-bg)" iconColor="var(--success)" icon={CheckCircle2} />
      </div>

      {/* ── شبكة الرسوم البيانية ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* توزيع النوايا */}
        <div className="hcn-card" style={{ padding: 32 }}>
           <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BarChart3 size={24} color="var(--info)" />
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>الطلبات حسب النية</h2>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <ProgressRow label="check_balance"           value="5,063 (34%)" percent={34} color="var(--info)" />
            <ProgressRow label="troubleshoot_slow_speed" value="4,169 (28%)" percent={28} color="var(--primary)" />
            <ProgressRow label="billing_invoices"        value="2,680 (18%)" percent={18} color="var(--warning)" />
            <ProgressRow label="check_package"           value="1,787 (12%)" percent={12} color="#8B5CF6" />
            <ProgressRow label="general_inquiry"         value="1,193 (8%)"  percent={8}  color="var(--text-disabled)" />
          </div>
        </div>

        {/* توزيع زمن الاستجابة */}
        <div className="hcn-card" style={{ padding: 32 }}>
           <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Clock size={24} color="var(--success)" />
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>تفصيل زمن الاستجابة</h2>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <LatencyRow service="توليد نص Ollama"       desc="llama3 response building"       value="85 ms"  color="var(--success)" />
            <LatencyRow service="تنفيذ أداة CRM"        desc="ToolExecutor HTTP calls"        value="24 ms"  color="var(--info)" />
            <LatencyRow service="بحث RAG المتجه"        desc="Document similarity matching"   value="15 ms"  color="#8B5CF6" />
            <LatencyRow service="تصنيف النية"           desc="NLP model classification"       value="12 ms"  color="var(--warning)" />
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '20px', background: 'var(--success-bg)', borderRadius: 12, border: '1px dashed var(--success)',
              marginTop: 8
            }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--success)' }}>إجمالي متوسط الاستجابة</div>
              <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--success)', fontFamily: 'monospace' }}>136 ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── ملخص استخدام الأدوات ── */}
      <div className="hcn-card" style={{ padding: 32 }}>
         <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--warning-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={24} color="var(--warning)" />
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>ملخص استخدام الأدوات</h2>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[
            { tool: 'get_balance',  count: 5063, pct: 34, color: 'var(--info)', bg: 'var(--info-bg)' },
            { tool: 'rag_service',  count: 4169, pct: 28, color: '#8B5CF6', bg: 'rgba(139, 92, 246, 0.16)' },
            { tool: 'get_invoices', count: 2680, pct: 18, color: 'var(--warning)', bg: 'var(--warning-bg)' },
            { tool: 'get_package',  count: 1787, pct: 12, color: 'var(--primary)', bg: 'var(--primary-bg)' },
          ].map((t) => (
            <div key={t.tool} style={{ background: 'var(--bg-neutral)', borderRadius: 12, padding: '24px', border: `1px solid var(--border)` }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 40, height: 40, borderRadius: 8, background: t.bg, marginBottom: 16 }}>
                <Activity size={20} color={t.color} />
              </div>
              <div style={{ fontSize: 14, fontFamily: 'monospace', fontWeight: 700, color: t.color, marginBottom: 8 }}>
                {t.tool}
              </div>
              <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)' }}>
                {t.count.toLocaleString()}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{t.pct}% من الطلبات</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
