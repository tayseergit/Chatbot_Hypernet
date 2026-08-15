import React, { useState, useCallback, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { usePasswordAuth, PasswordPromptModal } from './PasswordPromptModal';

const API = 'http://localhost:8000/api';

const RISK_CONFIG = {
  CRITICAL: { color: '#d32f2f', bg: '#ffebee', label: 'حرج' },
  HIGH:     { color: '#ed6c02', bg: '#fff3e0', label: 'عالي' },
  MEDIUM:   { color: '#ed6c02', bg: '#fff3e0', label: 'متوسط' },
  LOW:      { color: '#2e7d32', bg: '#e8f5e9', label: 'منخفض' },
};

const CATEGORY_LABELS = {
  GLOBAL:   'التحكم العام',
  SERVICE:  'التحكم بالخدمات',
  CRM_TOOL: 'أدوات CRM',
};

const stripEmojis = (str) => {
  if (!str) return '';
  return str.replace(/[\u1000-\uFFFF]+/g, '').replace(/[^\x00-\x7F\u0600-\u06FF\s()a-zA-Z0-9_\-/]+/g, '').trim();
};

function Toggle({ isOn, onChange, disabled }) {
  return (
    <button
      onClick={onChange}
      disabled={disabled}
      style={{
        width: 44, height: 24, borderRadius: 12,
        background: isOn ? '#1976d2' : '#e0e0e0',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.7 : 1,
        border: 'none', position: 'relative', transition: 'background 0.2s',
        padding: 0
      }}
    >
      <span style={{
        position: 'absolute', top: 2, left: isOn ? 'calc(100% - 22px)' : 2,
        width: 20, height: 20, borderRadius: '50%', background: '#fff',
        transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
      }} />
    </button>
  );
}



function PermissionCard({ perm, toggling, onToggleRequest }) {
  const risk = RISK_CONFIG[perm.risk_level] || RISK_CONFIG.MEDIUM;
  const isEnabled = perm.is_enabled;

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 24,
      padding: '20px 24px',
      background: '#ffffff',
      borderRadius: 4,
      border: '1px solid #e0e0e0',
      borderRight: `4px solid ${isEnabled ? '#2e7d32' : '#d32f2f'}`,
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      opacity: isEnabled ? 1 : 0.85,
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
          <span style={{ fontWeight: 600, fontSize: 16, color: '#212121' }}>{stripEmojis(perm.display_name)}</span>
          <span style={{ background: risk.bg, color: risk.color, fontSize: 12, padding: '2px 8px', borderRadius: 2, fontWeight: 'bold', border: `1px solid ${risk.color}33` }}>{risk.label}</span>
          <span style={{ background: isEnabled ? '#e8f5e9' : '#ffebee', color: isEnabled ? '#2e7d32' : '#d32f2f', fontSize: 12, padding: '2px 8px', borderRadius: 2, fontWeight: 'bold', border: `1px solid ${isEnabled ? '#2e7d3233' : '#d32f2f33'}` }}>
            {isEnabled ? 'مفعّل' : 'معطّل'}
          </span>
        </div>
        <div style={{ fontSize: 14, color: '#616161', lineHeight: 1.6 }}>{perm.description}</div>
        {perm.updated_at && (
          <div style={{ fontSize: 12, color: '#9e9e9e', marginTop: 8 }}>
            آخر تعديل: {new Date(perm.updated_at).toLocaleString('ar-IQ')} {perm.updated_by ? `بواسطة ${perm.updated_by}` : ''}
          </div>
        )}
      </div>
      <Toggle isOn={isEnabled} onChange={() => onToggleRequest(perm)} disabled={toggling} />
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

  const { requireAuth, modalProps } = usePasswordAuth();

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

  const requestToggle = (perm) => {
    if (toggling) return;
    requireAuth(
      perm.is_enabled ? `تعطيل الصلاحية (${stripEmojis(perm.display_name)})` : `تفعيل الصلاحية (${stripEmojis(perm.display_name)})`,
      (adminUsername) => executeToggle(perm, adminUsername)
    );
  };

  const requestEmergencyStop = () => {
    if (emergencyLoading) return;
    requireAuth(
      emergencyActive ? 'استئناف النظام' : 'تفعيل الإيقاف الطارئ لجميع العمليات',
      (adminUsername) => executeEmergencyStop(adminUsername)
    );
  };

  const executeToggle = async (perm, adminUsername) => {
    setToggling(perm.tool_name);
    const newState = !perm.is_enabled;
    try {
      const res = await fetch(`${API}/permissions/${encodeURIComponent(perm.tool_name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: newState, updated_by: adminUsername }),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'فشل التحديث'); }
      setPermissions(prev => prev.map(p => p.tool_name === perm.tool_name ? { ...p, is_enabled: newState } : p));
      showToast(`${stripEmojis(perm.display_name)} — ${newState ? 'تم التفعيل' : 'تم التعطيل'}`, newState ? 'success' : 'warn');
    } catch (e) {
      showToast(`خطأ: ${e.message}`, 'error');
    } finally {
      setToggling(null);
    }
  };

  const executeEmergencyStop = async (adminUsername) => {
    const activate = !emergencyActive;
    setEmergencyLoading(true);
    try {
      const res = await fetch(`${API}/permissions/emergency-stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ activate, updated_by: adminUsername }),
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
    success: { bg: '#e8f5e9', color: '#2e7d32', border: '1px solid #a5d6a7' },
    warn:    { bg: '#fff3e0', color: '#ed6c02', border: '1px solid #ffcc80' },
    error:   { bg: '#ffebee', color: '#d32f2f', border: '1px solid #ef9a9a' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, maxWidth: 960, margin: '0 auto', width: '100%', fontFamily: 'system-ui, sans-serif' }}>
      
      <PasswordPromptModal {...modalProps} />

      {/* Toast */}
      {toast && (() => {
        const ts = toastStyles[toast.type] || toastStyles.success;
        return (
          <div style={{
            position: 'fixed', top: 32, right: 32, zIndex: 9999,
            padding: '16px 24px', borderRadius: 4,
            background: ts.bg, color: ts.color, border: ts.border,
            fontWeight: 600, fontSize: 14, maxWidth: 400,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          }}>
            {toast.msg}
          </div>
        );
      })()}

      {/* ── رأس الصفحة ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '2px solid #eee', paddingBottom: 16 }}>
        <div>
           <h1 style={{ margin: 0, fontSize: 24, fontWeight: 'bold', color: '#212121' }}>
            إدارة الصلاحيات والوصول
          </h1>
          <div style={{ fontSize: 14, color: '#757575', marginTop: 4 }}>لوحة تحكم النظام - إدارة أمان العمليات</div>
        </div>
        <button onClick={fetchPermissions} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '8px 16px', background: '#f5f5f5', border: '1px solid #e0e0e0', borderRadius: 4,
          color: '#424242', cursor: 'pointer', fontWeight: 600, fontSize: 14
        }}>
          <RefreshCw size={16} /> تحديث
        </button>
      </div>

      {/* ── بانر إيقاف الطوارئ ── */}
      <div style={{ 
        padding: 24, 
        background: emergencyActive ? '#ffebee' : '#ffffff', 
        border: `1px solid ${emergencyActive ? '#d32f2f' : '#e0e0e0'}`, 
        borderRadius: 4,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div>
            <div style={{ fontWeight: 'bold', fontSize: 18, color: emergencyActive ? '#d32f2f' : '#212121', marginBottom: 4 }}>
              {emergencyActive ? 'النظام في حالة توقف طارئ' : 'التحكم العام (إيقاف الطوارئ)'}
            </div>
            <div style={{ fontSize: 14, color: '#616161' }}>
              {emergencyActive
                ? 'جميع عمليات النظام متوقفة حالياً.'
                : 'يوقف جميع عمليات النظام فوراً. يقتصر استخدامه على الحالات الأمنية والتقنية الحرجة.'}
            </div>
          </div>
        </div>
        <button
          onClick={requestEmergencyStop}
          disabled={emergencyLoading}
          style={{
            padding: '10px 24px', borderRadius: 4, border: 'none',
            cursor: emergencyLoading ? 'not-allowed' : 'pointer',
            fontWeight: 'bold', fontSize: 14, fontFamily: 'inherit',
            background: emergencyActive ? '#2e7d32' : '#d32f2f',
            color: '#fff',
            opacity: emergencyLoading ? 0.7 : 1, transition: 'all 0.2s',
          }}
        >
          {emergencyLoading ? 'جارٍ التنفيذ...' : emergencyActive ? 'استئناف النظام' : 'تفعيل إيقاف الطوارئ'}
        </button>
      </div>

      {/* ── قائمة الصلاحيات ── */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#757575' }}>
          <div style={{ fontSize: 16, marginBottom: 8, fontWeight: 600 }}>جارٍ التحميل...</div>
          <div style={{ fontSize: 14 }}>يتم جلب سجلات الصلاحيات من الخادم</div>
        </div>
      ) : (
        ['GLOBAL', 'SERVICE', 'CRM_TOOL'].map(cat => {
          const items = grouped[cat];
          if (!items || items.length === 0) return null;
          return (
            <div key={cat} style={{ marginBottom: 24 }}>
              <div style={{
                fontSize: 14, fontWeight: 'bold', color: '#424242',
                marginBottom: 16, paddingBottom: 8, borderBottom: '1px solid #e0e0e0',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                {CATEGORY_LABELS[cat] || cat}
                <span style={{ fontSize: 12, padding: '2px 8px', background: '#f5f5f5', border: '1px solid #e0e0e0', borderRadius: 2, color: '#616161' }}>{items.length} أوامر</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {items.map(perm => (
                  <PermissionCard
                    key={perm.tool_name}
                    perm={perm}
                    toggling={toggling === perm.tool_name}
                    onToggleRequest={requestToggle}
                  />
                ))}
              </div>
            </div>
          );
        })
      )}

      {/* ── معلومات التطبيق ── */}
      <div style={{ padding: 24, borderRadius: 4, background: '#f5f5f5', border: '1px solid #e0e0e0', marginTop: 16 }}>
        <div style={{ fontWeight: 'bold', color: '#424242', marginBottom: 8, fontSize: 15 }}>ملاحظات النظام الفنية</div>
        <div style={{ fontSize: 13, color: '#616161', lineHeight: 1.8 }}>
          يتم تطبيق التعديلات بشكل فوري على مستوى قاعدة البيانات. نظراً لوجود طبقات تخزين مؤقت (Caching)، قد تستغرق التغييرات فترة تصل إلى 30 ثانية لتنعكس على جميع طبقات الخدمة بشكل كامل. يتم تسجيل اسم المسؤول وتوقيت الإجراء للتدقيق الأمني.
        </div>
      </div>
    </div>
  );
}
