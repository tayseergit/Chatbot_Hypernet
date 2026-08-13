import React, { useState, useEffect } from 'react';
import { FileText, Search, Download, RefreshCw, Code, X } from 'lucide-react';

const TYPE_COLORS = {
  CRM_TOOL:        { bg: 'var(--info-bg)', color: 'var(--info)' },
  RAG_SEARCH:      { bg: 'rgba(139, 92, 246, 0.16)', color: '#8B5CF6' },
  INTENT_DECISION: { bg: 'var(--warning-bg)', color: 'var(--warning)' },
};

export default function AgentActionLogsTab() {
  const [selectedType, setSelectedType]     = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchTerm, setSearchTerm]         = useState('');
  const [activeModalLog, setActiveModalLog] = useState(null);
  const [logs, setLogs]                     = useState([]);
  const [loading, setLoading]               = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = `http://localhost:8000/api/actions?action_type=${selectedType}&status=${selectedStatus}`;
      if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
      const res = await fetch(url);
      if (res.ok) setLogs(await res.json());
    } catch (err) {
      console.warn('Backend API error, using fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, [selectedType, selectedStatus, searchTerm]);

  const mockLogs = [
    {
      id: 1, timestamp: '2026-08-07 10:29:43', sessionId: 'test-session-101',
      customerId: 'C001 (Ahmed Mohamed)', type: 'CRM_TOOL', tool: 'get_balance',
      intent: 'check_balance', status: 'SUCCESS',
      params: { crm_customer_id: 'C001' },
      result: { balance: 125000, currency: 'IQD', status: 'active', paid_until: '2026-09-01' },
    },
    {
      id: 2, timestamp: '2026-08-07 10:29:43', sessionId: 'test-session-101',
      customerId: 'C001 (Ahmed Mohamed)', type: 'RAG_SEARCH', tool: 'rag_service',
      intent: 'troubleshoot_slow_speed', status: 'SUCCESS',
      params: { query: 'Internet is slow' },
      result: { matches_count: 2, top_similarity: 0.94, context_snippet: 'Restart the router for 30 seconds...' },
    },
    {
      id: 3, timestamp: '2026-08-07 10:15:22', sessionId: 'test-session-102',
      customerId: 'C002 (Fatima Ali)', type: 'INTENT_DECISION', tool: 'intent_classifier',
      intent: 'billing_invoices', status: 'SUCCESS',
      params: { text: 'I need my invoice', confidence: 0.97 },
      result: { classified_intent: 'billing_invoices', confidence: 0.97 },
    },
  ];

  const displayLogs = logs.length > 0 ? logs : mockLogs;

  const exportCSV = () => {
    let csv = 'الوقت,رقم الجلسة,رقم العميل,نوع العملية,الأداة,النية,الحالة\n';
    displayLogs.forEach(l => {
      csv += `"${l.timestamp}","${l.sessionId}","${l.customerId}","${l.type}","${l.tool}","${l.intent}","${l.status}"\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'agent_action_logs.csv'; a.click();
  };

  const typeLabels = { ALL: 'الكل', CRM_TOOL: 'CRM_TOOL', RAG_SEARCH: 'RAG_SEARCH', INTENT_DECISION: 'INTENT_DECISION' };
  const statusLabels = { ALL: 'الكل', SUCCESS: 'SUCCESS', FAILED: 'FAILED' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            سجل العمليات التفصيلي
            <span className="hcn-badge hcn-badge-warning">MySQL — مباشر</span>
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>سجل العمليات</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <button onClick={exportCSV} className="hcn-btn-outlined">
            <Download size={20} /> تصدير CSV
          </button>
          <button onClick={fetchLogs} className="hcn-btn-primary">
            <RefreshCw size={20} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            تحديث السجل
          </button>
        </div>
      </div>

      <div className="hcn-card">
        {/* الفلاتر */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: 24, borderBottom: '1px solid var(--border)', flexWrap: 'wrap', gap: 16,
        }}>
          <div className="hcn-pill-group">
            {['ALL', 'CRM_TOOL', 'RAG_SEARCH', 'INTENT_DECISION'].map((type) => (
              <button key={type} className={`hcn-pill ${selectedType === type ? 'active-primary' : ''}`} onClick={() => setSelectedType(type)}>
                {typeLabels[type]}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="hcn-input" style={{ width: 'auto' }}>
              {Object.entries(statusLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
            <div style={{ position: 'relative' }}>
              <Search size={20} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }} />
              <input
                type="text"
                placeholder="بحث في السجل..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="hcn-input"
                style={{ paddingRight: 44, width: 280 }}
              />
            </div>
          </div>
        </div>

        {/* ── جدول السجلات ── */}
        <div className="hcn-table-wrapper">
          <table className="hcn-table">
            <thead>
              <tr>
                <th>الوقت</th>
                <th>رقم الجلسة</th>
                <th>العميل</th>
                <th>نوع العملية</th>
                <th>الأداة</th>
                <th>النية</th>
                <th>الحالة</th>
                <th style={{ textAlign: 'left' }}>التفاصيل</th>
              </tr>
            </thead>
            <tbody>
              {displayLogs.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-disabled)', fontSize: 15 }}>
                    لا توجد سجلات
                  </td>
                </tr>
              ) : displayLogs.map((log) => {
                const tc = TYPE_COLORS[log.type] || { bg: 'var(--bg-neutral)', color: 'var(--text-secondary)' };
                return (
                  <tr key={log.id}>
                    <td style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{log.timestamp}</td>
                    <td style={{ color: 'var(--info)', fontWeight: 700, fontFamily: 'monospace' }}>{log.sessionId}</td>
                    <td style={{ fontWeight: 600 }}>{log.customerId}</td>
                    <td>
                      <span style={{ display: 'inline-block', padding: '4px 8px', borderRadius: 6, fontSize: 12, fontWeight: 700, background: tc.bg, color: tc.color }}>
                        {log.type}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'monospace', fontWeight: 700 }}>{log.tool}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{log.intent}</td>
                    <td>
                      <span className="hcn-badge hcn-badge-success">{log.status}</span>
                    </td>
                    <td style={{ textAlign: 'left' }}>
                      <button onClick={() => setActiveModalLog(log)} className="hcn-btn-icon">
                        <Code size={20} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
            يتم عرض <strong>{displayLogs.length}</strong> سجلات
          </span>
          <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
            المصدر: <code style={{ background: 'var(--bg-neutral)', padding: '2px 8px', borderRadius: 6 }}>agent_action_logs</code>
          </span>
        </div>
      </div>

      {/* ── نافذة JSON ── */}
      {activeModalLog && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1200,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(33, 43, 54, 0.48)', backdropFilter: 'blur(4px)', padding: 16,
        }}>
          <div className="hcn-card animate-scale-in" style={{ width: '100%', maxWidth: 720, padding: 0, overflow: 'hidden', boxShadow: 'var(--shadow-dialog)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '24px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Code size={24} color="var(--info)" />
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 18 }}>تفاصيل العملية</div>
                  <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{activeModalLog.tool} — {activeModalLog.type}</div>
                </div>
              </div>
              <button onClick={() => setActiveModalLog(null)} className="hcn-btn-icon">
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 24, maxHeight: '60vh', overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div style={{ background: 'var(--bg-neutral)', borderRadius: 12, padding: '16px' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>نوع العملية</div>
                  <div style={{ fontWeight: 700, color: 'var(--info)', fontFamily: 'monospace', fontSize: 16 }}>{activeModalLog.type}</div>
                </div>
                <div style={{ background: 'var(--bg-neutral)', borderRadius: 12, padding: '16px' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>الأداة المستخدمة</div>
                  <div style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: 16 }}>{activeModalLog.tool}</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>المدخلات (JSON)</div>
                <pre className="hcn-code-block">{JSON.stringify(activeModalLog.params, null, 2)}</pre>
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>المخرجات (JSON)</div>
                <pre className="hcn-code-block" style={{ color: 'var(--info)' }}>{JSON.stringify(activeModalLog.result, null, 2)}</pre>
              </div>
            </div>

            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setActiveModalLog(null)} className="hcn-btn-primary">إغلاق</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
