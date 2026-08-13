import React, { useState, useCallback, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, RefreshCw } from 'lucide-react';

const API = 'http://localhost:8000/api';

const RISK_CONFIG = {
  CRITICAL: { color: 'var(--error)', bg: 'var(--error-bg)', label: 'حرج' },
  HIGH:     { color: 'var(--warning)', bg: 'var(--warning-bg)', label: 'عالي' },
  MEDIUM:   { color: 'var(--warning)', bg: 'var(--warning-bg)', label: 'متوسط' },
  LOW:      { color: 'var(--success)', bg: 'var(--success-bg)', label: 'منخفض' },
};

const CATEGORY_LABELS = {
  GLOBAL:   'التحكم العام',
  SERVICE:  'التحكم بالخدمات',
  CRM_TOOL: 'أدوات CRM',
};

function Toggle({ isOn, onChange, disabled }) {
  return (
    <button
      onClick={onChange}
      disabled={disabled}
      className="hcn-toggle"
      style={{
        background: isOn ? 'var(--primary)' : 'var(--text-disabled)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.7 : 1,
        boxShadow: isOn ? 'var(--shadow-card)' : 'none',
      }}
    >
      <span className="hcn-toggle-thumb" style={{ left: isOn ? 'calc(100% - 21px)' : 3 }} />
    </button>
  );
}

function PermissionCard({ perm, toggling, onToggle }) {
  const risk = RISK_CONFIG[perm.risk_level] || RISK_CONFIG.MEDIUM;
  const isEnabled = perm.is_enabled;

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 24,
      padding: '20px 24px',
      background: 'var(--bg-paper)',
      borderRadius: 12,
      border: `1px solid ${isEnabled ? 'var(--border)' : 'var(--error-bg)'}`,
      transition: 'all 0.2s',
      opacity: isEnabled ? 1 : 0.85,
    }}>
      <span className={`hcn-dot ${isEnabled ? 'hcn-dot-green' : 'hcn-dot-red'} ${isEnabled ? 'hcn-dot-pulse' : ''}`} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
          <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>{perm.display_name}</span>
          <span className="hcn-badge" style={{ background: risk.bg, color: risk.color, fontSize: 12 }}>{risk.label}</span>
          <span className={`hcn-badge ${isEnabled ? 'hcn-badge-success' : 'hcn-badge-error'}`} style={{ fontSize: 12 }}>
            {isEnabled ? 'مفعّل' : 'معطّل'}
          </span>
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{perm.description}</div>
        {perm.updated_at && (
          <div style={{ fontSize: 12, color: 'var(--text-disabled)', marginTop: 8 }}>
            آخر تعديل: {new Date(perm.updated_at).toLocaleString('ar-IQ')} بواسطة {perm.updated_by}
          </div>
        )}
      </div>
      <Toggle isOn={isEnabled} onChange={onToggle} disabled={toggling} />
    </div>
  );
}

export default function PermissionsTab() {
  const [permissions, setPermissions]         = useState([]);
  const [loading, setLoading]                 = useState(true);
  const [toggling, setToggling]               = useState(null);
  const [emergencyActive, setEmergencyActive] = useState(false);
  const [emergencyLoading, setEmergencyLoading] = useState(false);
  const [toast, setToast]                     = useState(null);
  const [lastRefresh, setLastRefresh]         = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchPermissions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/permissions`);
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      setPermissions(data);
      const global = data.find(p => p.tool_name === 'GLOBAL_AGENT');
      if (global) setEmergencyActive(!global.is_enabled);
      setLastRefresh(new Date().toLocaleTimeString('ar-IQ'));
    } catch {
      showToast('تعذّر تحميل الصلاحيات. تأكد من تشغيل الخادم.', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPermissions(); }, [fetchPermissions]);

  const handleToggle = async (perm) => {
    if (toggling) return;
    setToggling(perm.tool_name);
    const newState = !perm.is_enabled;
    try {
      const res = await fetch(`${API}/permissions/${encodeURIComponent(perm.tool_name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: newState, updated_by: 'dashboard_admin' }),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'فشل التحديث'); }
      setPermissions(prev => prev.map(p => p.tool_name === perm.tool_name ? { ...p, is_enabled: newState } : p));
      showToast(`${perm.display_name} — ${newState ? 'تم التفعيل' : 'تم التعطيل'}`, newState ? 'success' : 'warn');
    } catch (e) {
      showToast(`خطأ: ${e.message}`, 'error');
    } finally {
      setToggling(null);
    }
  };

  const handleEmergencyStop = async () => {
    const activate = !emergencyActive;
    if (activate && !window.confirm('تحذير: إيقاف الطوارئ\n\nسيتم إيقاف جميع عمليات النظام فوراً.\nهل أنت متأكد؟')) return;
    setEmergencyLoading(true);
    try {
      const res = await fetch(`${API}/permissions/emergency-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activate, updated_by: 'dashboard_admin' }),
      });
      if (!res.ok) throw new Error('فشل الطلب');
      setEmergencyActive(activate);
      await fetchPermissions();
      showToast(activate ? 'إيقاف الطوارئ مفعّل — جميع العمليات متوقفة' : 'تم استئناف النظام بشكل طبيعي', activate ? 'error' : 'success');
    } catch {
      showToast('فشل طلب إيقاف الطوارئ', 'error');
    } finally {
      setEmergencyLoading(false);
    }
  };

  const grouped = permissions.reduce((acc, p) => {
    const cat = p.category || 'CRM_TOOL';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(p);
    return acc;
  }, {});

  const toastStyles = {
    success: { bg: 'var(--success-bg)', color: 'var(--success)', border: '1px solid rgba(0, 171, 85, 0.2)' },
    warn:    { bg: 'var(--warning-bg)', color: 'var(--warning)', border: '1px solid rgba(255, 171, 0, 0.2)' },
    error:   { bg: 'var(--error-bg)',   color: 'var(--error)',   border: '1px solid rgba(255, 86, 48, 0.2)' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, maxWidth: 960, margin: '0 auto', width: '100%' }}>

      {/* Toast */}
      {toast && (() => {
        const ts = toastStyles[toast.type] || toastStyles.success;
        return (
          <div className="animate-slide-in" style={{
            position: 'fixed', top: 32, right: 32, zIndex: 9999,
            padding: '16px 24px', borderRadius: 12,
            background: ts.bg, color: ts.color, border: ts.border,
            fontWeight: 700, fontSize: 14, maxWidth: 400,
            boxShadow: 'var(--shadow-dropdown)',
          }}>
            {toast.msg}
          </div>
        );
      })()}

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            إدارة الصلاحيات
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>الصلاحيات والطوارئ</span>
            {lastRefresh && (
              <>
                <span>•</span>
                <span style={{ fontSize: 12 }}>آخر تحديث: {lastRefresh}</span>
              </>
            )}
          </div>
        </div>
        <button onClick={fetchPermissions} className="hcn-btn-outlined">
          <RefreshCw size={20} /> تحديث البيانات
        </button>
      </div>

      {/* ── بانر إيقاف الطوارئ ── */}
      <div className="hcn-card" style={{ padding: 32, background: emergencyActive ? 'var(--error-bg)' : 'var(--bg-paper)', border: `1px solid ${emergencyActive ? 'var(--error)' : 'var(--border)'}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: emergencyActive ? 'rgba(255, 86, 48, 0.16)' : 'var(--warning-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AlertTriangle size={24} color={emergencyActive ? 'var(--error)' : 'var(--warning)'} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18, color: emergencyActive ? 'var(--error)' : 'var(--warning)', marginBottom: 4 }}>
              {emergencyActive ? 'إيقاف الطوارئ مفعّل' : 'إيقاف الطوارئ'}
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {emergencyActive
                ? 'جميع عمليات النظام متوقفة. لا يمكن الوصول إلى أي خدمة.'
                : 'يوقف جميع عمليات النظام فوراً. استخدم في الحالات الحرجة فقط.'}
            </div>
          </div>
        </div>
        <button
          onClick={handleEmergencyStop}
          disabled={emergencyLoading}
          style={{
            padding: '12px 32px', borderRadius: 8, border: 'none',
            cursor: emergencyLoading ? 'not-allowed' : 'pointer',
            fontWeight: 800, fontSize: 14, fontFamily: 'inherit',
            background: emergencyActive ? 'var(--success)' : 'var(--error)',
            color: '#fff',
            boxShadow: 'var(--shadow-card)',
            opacity: emergencyLoading ? 0.7 : 1, transition: 'all 0.2s',
          }}
        >
          {emergencyLoading ? 'جارٍ التنفيذ...' : emergencyActive ? 'استئناف النظام' : 'إيقاف الطوارئ'}
        </button>
      </div>

      {/* ── قائمة الصلاحيات ── */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: 16, marginBottom: 8, fontWeight: 700 }}>جارٍ التحميل...</div>
          <div style={{ fontSize: 14 }}>يتم تحميل الصلاحيات من قاعدة البيانات</div>
        </div>
      ) : (
        ['GLOBAL', 'SERVICE', 'CRM_TOOL'].map(cat => {
          const items = grouped[cat];
          if (!items || items.length === 0) return null;
          return (
            <div key={cat} style={{ marginBottom: 16 }}>
              <div style={{
                fontSize: 14, fontWeight: 700, color: 'var(--text-secondary)',
                textTransform: 'uppercase', letterSpacing: '0.05em',
                marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid var(--border)',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                {CATEGORY_LABELS[cat] || cat}
                <span className="hcn-badge hcn-badge-neutral" style={{ fontSize: 12, padding: '4px 8px' }}>{items.length} عناصر</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {items.map(perm => (
                  <PermissionCard
                    key={perm.tool_name}
                    perm={perm}
                    toggling={toggling === perm.tool_name}
                    onToggle={() => handleToggle(perm)}
                  />
                ))}
              </div>
            </div>
          );
        })
      )}

      {/* ── معلومات التطبيق ── */}
      <div style={{ padding: '24px', borderRadius: 12, background: 'var(--info-bg)', border: '1px solid rgba(0, 184, 217, 0.2)' }}>
        <div style={{ fontWeight: 700, color: 'var(--info)', marginBottom: 12, fontSize: 16 }}>آلية التطبيق متعددة الطبقات</div>
        <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.8 }}>
          يتم تطبيق الصلاحيات المعطّلة عبر <strong>3 طبقات مستقلة</strong>:<br />
          <strong>الطبقة 1</strong> — قاعدة البيانات (مرجع أساسي، مخزّن مؤقتاً 30 ثانية) &nbsp;·&nbsp;
          <strong>الطبقة 2</strong> — WorkflowCoordinator (بوابة ما قبل التنفيذ) &nbsp;·&nbsp;
          <strong>الطبقة 3</strong> — ToolExecutor (حارس الأداة النهائي)<br />
          لا يمكن تجاوز الصلاحية المعطّلة — التغييرات تسري خلال 30 ثانية.
        </div>
      </div>
    </div>
  );
}
