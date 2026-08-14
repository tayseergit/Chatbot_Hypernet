import React, { useState, useEffect } from 'react';
import {
  FileText, Search, Download, RefreshCw, Eye, X,
  CheckCircle2, AlertCircle, Clock, ChevronLeft, ChevronRight,
  Filter, Check
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const TYPE_CONFIG = {
  CRM_TOOL: {
    label: 'خدمات المشتركين',
    bg: 'rgba(217, 119, 6, 0.12)',
    color: '#D97706',
    border: 'rgba(217, 119, 6, 0.25)'
  },
  RAG_SEARCH: {
    label: 'قاعدة المعرفة',
    bg: 'rgba(124, 58, 237, 0.12)',
    color: '#7C3AED',
    border: 'rgba(124, 58, 237, 0.25)'
  },
  INTENT_DECISION: {
    label: 'تصنيف الطلبات',
    bg: 'rgba(79, 70, 229, 0.12)',
    color: '#4F46E5',
    border: 'rgba(79, 70, 229, 0.25)'
  },
  NOTIFICATION: {
    label: 'بث الإشعارات',
    bg: 'rgba(5, 150, 105, 0.12)',
    color: '#059669',
    border: 'rgba(5, 150, 105, 0.25)'
  }
};

export default function AgentActionLogsTab() {
  const [selectedType, setSelectedType]     = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchTerm, setSearchTerm]         = useState('');
  const [activeModalLog, setActiveModalLog] = useState(null);
  const [logs, setLogs]                     = useState([]);
  const [loading, setLoading]               = useState(false);
  const [hasFetched, setHasFetched]         = useState(false);
  const [page, setPage]                     = useState(1);
  const perPage = 10;

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = `${API}/api/actions?action_type=${selectedType}&status=${selectedStatus}&limit=100`;
      if (searchTerm.trim()) {
        url += `&search=${encodeURIComponent(searchTerm.trim())}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(Array.isArray(data) ? data : []);
      } else {
        setLogs([]);
      }
    } catch (err) {
      console.warn('Failed to fetch action logs:', err);
      setLogs([]);
    } finally {
      setLoading(false);
      setHasFetched(true);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedType, selectedStatus, searchTerm]);

  const paginatedLogs = logs.slice((page - 1) * perPage, page * perPage);
  const totalPages = Math.ceil(logs.length / perPage) || 1;

  const exportCSV = () => {
    let csv = 'التاريخ والوقت,رقم الجلسة,المشترك,نوع العملية,الإجراء المنفذ,التصنيف,الحالة\n';
    logs.forEach(l => {
      const typeLabel = TYPE_CONFIG[l.type]?.label || l.type;
      const statusLabel = (l.status || '').toUpperCase() === 'SUCCESS' ? 'ناجحة' : 'غير مكتملة';
      csv += `"${l.timestamp}","${l.sessionId}","${l.customerId}","${typeLabel}","${l.tool}","${l.intent}","${statusLabel}"\n`;
    });
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `operation_logs_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: '100%', overflow: 'hidden' }}>

      {/* ── رأس الصفحة الرسمي والمنظم ── */}
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
            سجل العمليات
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            <span>متابعة وتدقيق العمليات والمهام المنفذة آلياً</span>
            <span>•</span>
            <span>إجمالي السجلات: <strong style={{ color: 'var(--text-primary)' }}>{logs.length}</strong></span>
          </div>
        </div>

        {/* أزرار الإجراءات العلوية بتصميم متناسق وأفقي */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={exportCSV}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              height: 38,
              padding: '0 16px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-paper)',
              color: 'var(--text-primary)',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease'
            }}
          >
            <Download size={15} />
            تصدير السجل
          </button>

          <button
            onClick={fetchLogs}
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              height: 38,
              padding: '0 18px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: 'var(--primary)',
              color: '#ffffff',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease'
            }}
          >
            <RefreshCw size={15} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            تحديث البيانات
          </button>
        </div>
      </div>

      {/* ── كارد الجدول والفلترة ── */}
      <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '20px' }}>

        {/* شريط الفلاتر والبحث */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: 16
        }}>
          {/* تبويبات التصفية بحسب نوع العملية */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {[
              { key: 'ALL', label: 'كافة العمليات' },
              { key: 'CRM_TOOL', label: 'خدمات المشتركين' },
              { key: 'RAG_SEARCH', label: 'قاعدة المعرفة' },
              { key: 'INTENT_DECISION', label: 'تصنيف الطلبات' },
            ].map((tab) => {
              const isActive = selectedType === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => { setSelectedType(tab.key); setPage(1); }}
                  style={{
                    padding: '7px 16px',
                    borderRadius: 'var(--radius-sm)',
                    border: isActive ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                    background: isActive ? 'rgba(0, 167, 111, 0.12)' : 'var(--bg-paper)',
                    color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* حقل البحث والقائمة المنسدلة لاختيار الحالة */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 300, justifyContent: 'flex-end' }}>
            {/* القائمة المنسدلة للحالة بتصميم احترافي واضح */}
            <select
              value={selectedStatus}
              onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
              style={{
                height: 38,
                padding: '0 14px',
                minWidth: 150,
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-paper)',
                color: 'var(--text-primary)',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
                textAlign: 'right',
                direction: 'rtl'
              }}
            >
              <option value="ALL">كافة الحالات</option>
              <option value="SUCCESS">عمليات ناجحة</option>
              <option value="FAILED">عمليات غير مكتملة</option>
            </select>

            {/* حقل البحث */}
            <div style={{ position: 'relative', width: 250 }}>
              <Search size={16} style={{ position: 'absolute', right: 12, top: 11, color: 'var(--text-disabled)' }} />
              <input
                type="text"
                placeholder="البحث في السجل..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
                className="hcn-input"
                style={{ paddingRight: 36, width: '100%', height: 38, fontSize: 13 }}
              />
            </div>
          </div>
        </div>

        {/* ── جدول العمليات ── */}
        <div className="hcn-table-wrapper" style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
          <table className="hcn-table" style={{ width: '100%', tableLayout: 'fixed' }}>
            <thead>
              <tr>
                <th style={{ width: '16%' }}>التاريخ والوقت</th>
                <th style={{ width: '14%' }}>رقم الجلسة</th>
                <th style={{ width: '18%' }}>المشترك</th>
                <th style={{ width: '14%' }}>نوع العملية</th>
                <th style={{ width: '13%' }}>الإجراء</th>
                <th style={{ width: '13%' }}>التصنيف</th>
                <th style={{ width: '8%', textAlign: 'center' }}>الحالة</th>
                <th style={{ width: '4%', textAlign: 'center' }}>التفاصيل</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-disabled)' }}>
                    جاري تحميل السجلات...
                  </td>
                </tr>
              ) : paginatedLogs.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-disabled)', fontSize: 13 }}>
                    لا توجد عمليات تطابق معايير الفلترة المحددة.
                  </td>
                </tr>
              ) : (
                paginatedLogs.map((log) => {
                  const cfg = TYPE_CONFIG[log.type] || { label: log.type, bg: 'rgba(145, 158, 171, 0.12)', color: 'var(--text-secondary)', border: 'transparent' };
                  const isSuccess = (log.status || '').toUpperCase() === 'SUCCESS';
                  return (
                    <tr key={log.id}>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                        {log.timestamp}
                      </td>
                      <td>
                        <span style={{ color: 'var(--info)', fontWeight: 600, fontFamily: 'monospace', fontSize: 12 }}>
                          {log.sessionId}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13, wordBreak: 'break-word' }}>
                        {log.customerId}
                      </td>
                      <td>
                        <span style={{
                          display: 'inline-block',
                          padding: '3px 8px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 600,
                          background: cfg.bg,
                          color: cfg.color,
                          border: `1px solid ${cfg.border}`,
                          whiteSpace: 'nowrap'
                        }}>
                          {cfg.label}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                        {log.tool}
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12, wordBreak: 'break-word' }}>
                        {log.intent}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className="hcn-badge" style={{
                          background: isSuccess ? 'var(--success-bg)' : 'var(--error-bg)',
                          color: isSuccess ? 'var(--success)' : 'var(--error)',
                          fontSize: 11,
                          fontWeight: 600
                        }}>
                          {isSuccess ? 'ناجحة' : 'فشلت'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => setActiveModalLog(log)}
                          className="hcn-btn-ghost"
                          style={{ padding: 6, color: 'var(--primary)' }}
                          title="عرض تفاصيل العملية"
                        >
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* ── التذييل وترقيم الصفحات ── */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--text-secondary)', flexWrap: 'wrap', gap: 8 }}>
          <div>
            عرض <strong>{paginatedLogs.length}</strong> من إجمالي <strong>{logs.length}</strong> عملية مسجلة
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              className="hcn-btn"
              style={{ padding: '3px 10px', fontSize: 12 }}
            >
              السابق
            </button>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', padding: '0 6px' }}>
              {page} / {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(p => p + 1)}
              className="hcn-btn"
              style={{ padding: '3px 10px', fontSize: 12 }}
            >
              التالي
            </button>
          </div>
        </div>
      </div>

      {/* ── نافذة تفاصيل العملية الرسمية ── */}
      {activeModalLog && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(4px)',
          padding: 16
        }}>
          <div className="hcn-card" style={{ width: '100%', maxWidth: 650, padding: 0, overflow: 'hidden' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 20px',
              borderBottom: '1px solid var(--border-color)',
              background: 'var(--bg-card)'
            }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                  تفاصيل العملية
                </h3>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  {activeModalLog.tool} — {TYPE_CONFIG[activeModalLog.type]?.label || activeModalLog.type}
                </div>
              </div>

              <button onClick={() => setActiveModalLog(null)} className="hcn-btn-ghost" style={{ padding: 4 }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 14, maxHeight: '65vh', overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <div style={{ background: 'var(--bg-paper)', borderRadius: 8, padding: 10, border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2 }}>نوع الإجراء</div>
                  <div style={{ fontWeight: 700, color: 'var(--primary)', fontSize: 13 }}>
                    {TYPE_CONFIG[activeModalLog.type]?.label || activeModalLog.type}
                  </div>
                </div>
                <div style={{ background: 'var(--bg-paper)', borderRadius: 8, padding: 10, border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 2 }}>الأداة المنفذة</div>
                  <div style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: 13, color: 'var(--text-primary)' }}>
                    {activeModalLog.tool}
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                  مدخلات ومعاملات الطلب:
                </div>
                <pre style={{
                  background: 'var(--bg-paper)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  padding: 12,
                  fontFamily: 'inherit',
                  fontSize: 12,
                  color: 'var(--text-primary)',
                  overflowX: 'auto',
                  margin: 0,
                  lineHeight: 1.5
                }}>
                  {JSON.stringify(activeModalLog.params, null, 2)}
                </pre>
              </div>

              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
                  استجابة النظام والنتيجة:
                </div>
                <pre style={{
                  background: 'var(--bg-paper)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  padding: 12,
                  fontFamily: 'inherit',
                  fontSize: 12,
                  color: 'var(--success)',
                  overflowX: 'auto',
                  margin: 0,
                  lineHeight: 1.5
                }}>
                  {JSON.stringify(activeModalLog.result, null, 2)}
                </pre>
              </div>
            </div>

            <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', background: 'var(--bg-card)' }}>
              <button onClick={() => setActiveModalLog(null)} className="hcn-btn-primary" style={{ fontSize: 13, height: 34, padding: '0 20px' }}>
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
