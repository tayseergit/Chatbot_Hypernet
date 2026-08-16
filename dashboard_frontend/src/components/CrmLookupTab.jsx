import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Search, Filter, ChevronLeft, ChevronRight, X,
  User, CheckCircle2, MoreVertical, MessageSquare, ShieldAlert, AlertCircle,
  Clock, MapPin, RefreshCw, Trash2, LogOut, Send, Image as ImageIcon, ZoomIn, ExternalLink
} from 'lucide-react';
import { usePasswordAuth, PasswordPromptModal } from './PasswordPromptModal';
import ConfirmModal from './ConfirmModal';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ─────────────── مكوّن: صف الجدول ─────────────── */
function TableRow({ cust, selected, onSelect, onOpen, onDelete, hasPermission }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isAuthed = cust.auth_state === 'AUTHENTICATED' || cust.authenticated;
  const authLabel = isAuthed ? 'موثق' : 'غير موثق';
  const authClass = isAuthed ? 'hcn-badge-success' : 'hcn-badge-warning';

  return (
    <tr>
      <td style={{ padding: '16px' }}>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onSelect(cust.session_id)}
          style={{ accentColor: 'var(--primary)', width: 18, height: 18, cursor: 'pointer' }}
        />
      </td>
      <td style={{ padding: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span
            onClick={() => onOpen(cust)}
            style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}
            onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
            onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}
          >
            {cust.user_name || cust.session_id}
          </span>
          <span style={{ fontSize: 12, color: 'var(--text-disabled)', fontFamily: 'monospace' }}>
            ID: {cust.session_id}
          </span>
          {cust.user_id && (
            <span style={{ fontSize: 12, color: 'var(--primary)', fontFamily: 'monospace', opacity: 0.8 }}>
              TG: {cust.user_id}
            </span>
          )}
        </div>
      </td>
      <td style={{ padding: '16px', fontWeight: 600 }}>{cust.customer_id}</td>
      <td style={{ padding: '16px' }}>
        <span className={`hcn-badge ${authClass}`}>
          {authLabel}
        </span>
      </td>
      <td style={{ padding: '16px', fontFamily: 'monospace', fontSize: 13 }}>{cust.lastActive}</td>
      <td style={{ padding: '16px', fontFamily: 'monospace', fontSize: 13 }}>{cust.created_at}</td>
      <td style={{ padding: '16px', textAlign: 'left', position: 'relative' }}>
        <button 
          onClick={(e) => { e.stopPropagation(); setMenuOpen(v => !v); }} 
          className="hcn-btn-icon"
          title="خيارات الجلسة"
        >
          <MoreVertical size={20} />
        </button>

        {menuOpen && (
          <div 
            style={{
              position: 'absolute',
              left: 16,
              top: 48,
              background: 'var(--bg-paper)',
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 10px 30px rgba(0,0,0,0.18)',
              border: '1px solid var(--border)',
              zIndex: 100,
              minWidth: 170,
              padding: '6px 0',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={() => setMenuOpen(false)}
          >
            <button
              onClick={() => onOpen(cust)}
              style={{
                background: 'transparent',
                border: 'none',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                fontSize: 13,
                color: 'var(--text-primary)',
                cursor: 'pointer',
                textAlign: 'right',
                width: '100%'
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-neutral)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <MessageSquare size={16} color="var(--primary)" /> عرض المحادثة
            </button>
            {hasPermission('delete_chat_sessions') && (
              <button
                onClick={() => onDelete(cust.session_id)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: '10px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  fontSize: 13,
                  color: 'var(--error)',
                  cursor: 'pointer',
                  textAlign: 'right',
                  width: '100%'
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--error-bg)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <Trash2 size={16} color="var(--error)" /> حذف الجلسة
              </button>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

/* ─────────────── مكوّن: نافذة التفاصيل والمحادثة (Modal) ─────────────── */
const DETAIL_TABS = [
  { key: 'chat',     label: 'المحادثة الحية', icon: MessageSquare },
  { key: 'session',  label: 'بيانات الجلسة', icon: User },
  { key: 'crm',      label: 'بيانات Hypernet (CRM)', icon: ShieldAlert },
];

function DetailModal({ cust, onClose, onDelete, requireAuth, hasPermission }) {
  const [tab, setTab] = useState('chat');
  const [messages, setMessages] = useState([]);
  const [loadingMsg, setLoadingMsg] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const chatEndRef = useRef(null);

  const fetchMessages = () => {
    fetch(`${API_BASE}/api/sessions/${cust.session_id}/messages`)
      .then(r => r.json())
      .then(data => {
        setMessages(data);
        setLoadingMsg(false);
      })
      .catch(e => {
        console.error(e);
        setLoadingMsg(false);
      });
  };

  useEffect(() => {
    let intervalId;
    if (tab === 'chat') {
      setLoadingMsg(true);
      fetchMessages();
      intervalId = setInterval(fetchMessages, 3000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [tab, cust.session_id]);

  useEffect(() => {
    if (tab === 'chat' && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, tab]);

  const [crmOverview, setCrmOverview] = useState(null);
  const [loadingOverview, setLoadingOverview] = useState(false);

  const isAuthed = cust.auth_state === 'AUTHENTICATED' || cust.authenticated;
  const authLabel = isAuthed ? 'موثق' : 'غير موثق';

  useEffect(() => {
    if (tab === 'crm' && isAuthed && !cust.is_playground && cust.customer_id && cust.customer_id !== 'غير مرتبط') {
      setLoadingOverview(true);
      fetch(`${API_BASE}/api/crm/overview/${cust.customer_id}`)
        .then(r => r.json())
        .then(data => {
          setCrmOverview(data);
          setLoadingOverview(false);
        })
        .catch(err => {
          console.error('Failed to fetch CRM overview:', err);
          setLoadingOverview(false);
        });
    }
  }, [tab, cust.customer_id, cust.is_playground, isAuthed]);

  const handleSendReply = () => {
    if (!replyText.trim() || sendingReply) return;
    setShowConfirm(true);
  };

  const executeSendReply = async () => {
    setSendingReply(true);
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${cust.session_id}/reply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: replyText.trim() })
      });
      if (res.ok) {
        setReplyText('');
        fetchMessages();
      }
    } catch (err) {
      console.error('Failed to send reply:', err);
    } finally {
      setSendingReply(false);
    }
  };

  // Helper to render message content (Text or Photo)
  const renderMessageContent = (text, isUser) => {
    if (text.includes('[صورة]')) {
      const match = text.match(/\[صورة\]\s*(\S+)/);
      const relativePath = match ? match[1] : '';
      const fullUrl = relativePath.startsWith('http') ? relativePath : `${API_BASE}${relativePath}`;
      const caption = text.replace(/\[صورة\]\s*\S+/, '').trim();

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div 
            onClick={() => setPreviewImage(fullUrl)}
            style={{ 
              position: 'relative', 
              borderRadius: 12, 
              overflow: 'hidden', 
              cursor: 'pointer',
              border: '2px solid rgba(255,255,255,0.2)',
              maxWidth: 280,
              maxHeight: 220
            }}
          >
            <img 
              src={fullUrl} 
              alt="User Upload" 
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              onError={(e) => { e.target.style.display = 'none'; }}
            />
            <div style={{ 
              position: 'absolute', bottom: 6, right: 6, 
              background: 'rgba(0,0,0,0.6)', color: '#fff', 
              padding: '4px 8px', borderRadius: 6, fontSize: 11,
              display: 'flex', alignItems: 'center', gap: 4
            }}>
              <ZoomIn size={12} /> انقر للتكبير
            </div>
          </div>
          {caption && <span style={{ fontSize: 13, marginTop: 4 }}>{caption}</span>}
        </div>
      );
    }
    return text;
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '40px'
    }}>
      <div style={{
        background: 'var(--bg-paper)',
        borderRadius: '24px',
        width: '100%', maxWidth: '800px', height: '100%', maxHeight: '85vh',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.3)',
        overflow: 'hidden'
      }}>
        {/* ── Modal Header ── */}
        <div style={{ padding: '24px 28px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-default)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <User size={24} color="var(--primary)" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontWeight: 800, fontSize: 18 }}>{cust.user_name || cust.session_id}</span>
                <span className={`hcn-badge ${isAuthed ? 'hcn-badge-success' : 'hcn-badge-warning'}`}>{authLabel}</span>
                <span style={{ fontSize: 12, color: 'var(--text-disabled)', fontFamily: 'monospace' }}>• ID: {cust.session_id}</span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            {hasPermission('delete_chat_sessions') && (
              <button 
                onClick={() => {
                  requireAuth('حذف الجلسة نهائياً', () => {
                    onDelete(cust.session_id);
                    onClose();
                  });
                }} 
                className="hcn-btn-secondary" 
                style={{ color: 'var(--error)', borderColor: 'var(--error)' }}
              >
                <Trash2 size={16} /> حذف
              </button>
            )}
            <button onClick={onClose} className="hcn-btn-icon" style={{ background: 'var(--bg-hover)' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* ── Tabs ── */}
        <div className="hcn-tabs-container" style={{ padding: '0 28px', margin: 0, borderBottom: '1px solid var(--border)' }}>
          {DETAIL_TABS.map(t => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`hcn-tab ${active ? 'active' : ''}`}
                style={{ padding: '12px 0' }}
              >
                <Icon size={16} />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* ── Tab Content ── */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {/* سجل المحادثة */}
          {tab === 'chat' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16, overflowY: 'auto', padding: '24px 28px', background: 'var(--bg-default)' }}>
                {loadingMsg && messages.length === 0 ? (
                  <div style={{ textAlign: 'center', color: 'var(--text-disabled)', margin: 'auto' }}>جاري تحميل الرسائل...</div>
                ) : messages.length === 0 ? (
                  <div style={{ textAlign: 'center', color: 'var(--text-disabled)', margin: 'auto' }}>لا توجد رسائل مسجلة لهذه الجلسة حتى الآن</div>
                ) : (
                  messages.map((msg, i) => {
                    const isUser = msg.sender === 'user';
                    const isAdmin = msg.sender === 'admin';
                    return (
                      <div key={i} style={{ 
                        alignSelf: isUser ? 'flex-start' : 'flex-end',
                        maxWidth: '75%',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: isUser ? 'flex-start' : 'flex-end'
                      }}>
                        <div style={{ 
                          background: isUser 
                            ? 'var(--primary)' 
                            : isAdmin 
                              ? '#4F46E5' 
                              : 'var(--bg-paper)',
                          color: (isUser || isAdmin) ? '#fff' : 'var(--text-primary)',
                          padding: '12px 18px',
                          borderRadius: '16px',
                          borderBottomRightRadius: isUser ? 4 : 16,
                          borderBottomLeftRadius: isUser ? 16 : 4,
                          fontSize: 14,
                          lineHeight: 1.5,
                          whiteSpace: 'pre-line',
                          boxShadow: 'var(--shadow-card)',
                          border: (isUser || isAdmin) ? 'none' : '1px solid var(--border)'
                        }}>
                          {renderMessageContent(msg.text, isUser)}
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text-disabled)', marginTop: 4, padding: '0 4px' }}>
                          {msg.time} • {isUser ? 'المشترك' : isAdmin ? 'الدعم الفني (لوحة التحكم)' : 'المساعد الذكي'}
                        </span>
                      </div>
                    );
                  })
                )}
                <div ref={chatEndRef} />
              </div>

              {/* ── شريط الرد اليدوي ── */}
              {hasPermission('reply_chat_sessions') && (
                <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-paper)', display: 'flex', gap: 12, alignItems: 'center' }}>
                  <input
                    type="text"
                    className="hcn-input"
                    placeholder="اكتب رداً يدويًا للمشترك عبر تيليجرام..."
                    value={replyText}
                    onChange={e => setReplyText(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendReply();
                      }
                    }}
                    style={{ flex: 1 }}
                  />
                  <button
                    onClick={handleSendReply}
                    disabled={sendingReply || !replyText.trim()}
                    className="hcn-btn-primary"
                    style={{ padding: '10px 20px', gap: 8, display: 'flex', alignItems: 'center', minWidth: 120, justifyContent: 'center' }}
                  >
                    <Send size={16} />
                    {sendingReply ? 'جاري الإرسال...' : 'إرسال رد'}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* معاينة الصورة في Lightbox */}
          {previewImage && (
            <div 
              onClick={() => setPreviewImage(null)}
              style={{
                position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)',
                zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center',
                padding: 24, cursor: 'zoom-out'
              }}
            >
              <img 
                src={previewImage} 
                alt="Enlarged User Photo" 
                style={{ maxWidth: '90%', maxHeight: '90%', borderRadius: 12, boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }} 
              />
            </div>
          )}

          {/* بيانات الجلسة */}
          {tab === 'session' && (
            <div style={{ padding: '28px', overflowY: 'auto' }}>
              <div className="hcn-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', border: '1px solid var(--border)', boxShadow: 'none' }}>
                <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 16 }}>بيانات الجلسة</h3>
                {[
                  { label: 'اسم المشترك (Telegram)', value: cust.user_name || cust.session_id },
                  { label: 'رقم المشترك (Telegram ID)', value: cust.user_id || 'غير متوفر' },
                  { label: 'معرف الجلسة',             value: cust.session_id },
                  { label: 'معرف العميل (CRM)',       value: cust.customer_id },
                  { label: 'حالة المصادقة',           value: authLabel },
                  { label: 'آخر تفاعل',               value: cust.lastActive },
                  { label: 'تاريخ بدء الجلسة',        value: cust.created_at },
                ].map((field, i, arr) => (
                  <div key={field.label} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '14px 0', borderBottom: i !== arr.length - 1 ? '1px solid var(--border)' : 'none'
                  }}>
                    <span style={{ fontSize: 13, color: 'var(--text-disabled)', fontWeight: 600 }}>{field.label}</span>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{field.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* بيانات CRM */}
          {tab === 'crm' && (
            <div style={{ padding: '28px', overflowY: 'auto' }}>
              {loadingOverview && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-disabled)' }}>
                  جاري تحميل بيانات العميل من نظام Hypernet CRM...
                </div>
              )}

              {crmOverview && !loadingOverview && (
                <div className="hcn-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', border: '1px solid var(--border)', boxShadow: 'none' }}>
                  <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: 16, color: 'var(--primary)' }}>بيانات العميل (Hypernet CRM)</h3>
                  {[
                    { label: 'اسم الحساب', value: crmOverview.username || '-' },
                    { label: 'الاسم الكامل', value: [crmOverview.firstname, crmOverview.lastname].filter(Boolean).join(' ') || '-' },
                    { label: 'رقم الهاتف', value: crmOverview.phone || '-' },
                    { label: 'الرصيد', value: crmOverview.balance !== undefined ? `${crmOverview.balance}` : '-' },
                    { label: 'الحالة', value: crmOverview.status || '-' },
                    { label: 'نوع الاشتراك', value: crmOverview.profile_name || '-' },
                    { label: 'تاريخ الانتهاء', value: crmOverview.expiration || '-' },
                    { label: 'الحصة المتبقية', value: crmOverview.remaining_rx || '-' },
                    { label: 'Mac Address', value: crmOverview.cpe_mac || '-' },
                  ].map((field, i, arr) => (
                    <div key={field.label} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '14px 0', borderBottom: i !== arr.length - 1 ? '1px solid var(--border)' : 'none'
                    }}>
                      <span style={{ fontSize: 13, color: 'var(--text-disabled)', fontWeight: 600 }}>{field.label}</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{field.value}</span>
                    </div>
                  ))}
                </div>
              )}

              {!loadingOverview && !crmOverview && isAuthed && cust.customer_id && cust.customer_id !== 'غير مرتبط' && !cust.is_playground && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--error)' }}>
                  لم يتم العثور على بيانات لهذا العميل في نظام CRM.
                </div>
              )}
              
              {(!isAuthed || cust.customer_id === 'غير مرتبط' || !cust.customer_id) && !cust.is_playground && (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-disabled)' }}>
                  المشترك غير موثق أو غير مرتبط بحساب CRM. لا يمكن جلب بيانات النظام.
                </div>
              )}
            </div>
          )}

          {/* Confirmation Modal */}
          <ConfirmModal
            isOpen={showConfirm}
            title="تأكيد إرسال الرد"
            message="هل أنت متأكد من إرسال هذا الرد للمشترك عبر تيليجرام؟"
            type="primary"
            confirmText="تأكيد الإرسال"
            onConfirm={() => { setShowConfirm(false); executeSendReply(); }}
            onCancel={() => setShowConfirm(false)}
          />
        </div>
      </div>
    </div>
  );
}

/* ─────────────── المكوّن الرئيسي ─────────────── */
export default function CrmLookupTab() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState([]);
  const [openCustomer, setOpenCustomer] = useState(null);
  const [page, setPage] = useState(0);
  const rowsPerPage = 10;
  const [activeTab, setActiveTab] = useState('all');

  const { requireAuth, modalProps } = usePasswordAuth();
  const { hasPermission } = useAuth();

  const fetchCustomers = () => {
    fetch(`${API_BASE}/api/crm/customers`)
      .then(res => res.json())
      .then(data => {
        setCustomers(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCustomers();
    const intervalId = setInterval(fetchCustomers, 4000);
    return () => clearInterval(intervalId);
  }, []);

  const handleDeleteSession = (sessionId) => {
    requireAuth('حذف جلسة المشترك', () => {
      if (!window.confirm(`هل أنت متأكد من حذف الجلسة ${sessionId}؟`)) return;
      fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(() => {
          setSelected(prev => prev.filter(id => id !== sessionId));
          fetchCustomers();
        })
        .catch(err => console.error('Failed to delete session:', err));
    });
  };

  const handleBatchDelete = () => {
    requireAuth('حذف جلسات متعددة', () => {
      if (!window.confirm(`هل أنت متأكد من حذف ${selected.length} جلسة محددة؟`)) return;
      Promise.all(selected.map(id => fetch(`${API_BASE}/api/sessions/${id}`, { method: 'DELETE' })))
        .then(() => {
          setSelected([]);
          fetchCustomers();
        })
        .catch(err => console.error('Batch delete failed:', err));
    });
  };

  // ── Global search and multi-criteria filter ──
  const filtered = useMemo(() => {
    return customers.filter(c => {
      if (c.is_playground) return false;

      const q = search.toLowerCase().trim();
      const sId = (c.session_id || '').toLowerCase();
      const uName = (c.user_name || '').toLowerCase();
      const cId = (c.customer_id || '').toLowerCase();

      const matchSearch = !q || sId.includes(q) || uName.includes(q) || cId.includes(q);

      const isAuthed = c.auth_state === 'AUTHENTICATED' || c.authenticated;

      const matchTab = activeTab === 'all'
        ? true
        : activeTab === 'authenticated'
          ? isAuthed
          : !isAuthed;

      return matchSearch && matchTab;
    });
  }, [search, activeTab, customers]);

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(0);
  };

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey);
    setPage(0);
  };

  const paginated = filtered.slice(page * rowsPerPage, (page + 1) * rowsPerPage);
  const totalPages = Math.max(1, Math.ceil(filtered.length / rowsPerPage));

  const toggleSelect = (sessionId) =>
    setSelected(prev => prev.includes(sessionId) ? prev.filter(x => x !== sessionId) : [...prev, sessionId]);
  const toggleAll = () =>
    setSelected(selected.length === paginated.length && paginated.length > 0 ? [] : paginated.map(c => c.session_id));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <PasswordPromptModal {...modalProps} />
      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="hcn-title" style={{ marginBottom: 8 }}>جلسات العملاء</h1>
        </div>
        <button onClick={fetchCustomers} className="hcn-btn-secondary" style={{ padding: '8px 16px', fontSize: 13, gap: 6, display: 'flex', alignItems: 'center' }}>
          <RefreshCw size={14} /> تحديث
        </button>
      </div>

      {/* ── Card الجدول ── */}
      <div className="hcn-card">
        {/* Tab Bar */}
        <div className="hcn-tabs-container" style={{ margin: 0, padding: '0 24px', borderBottom: '1px solid var(--border)' }}>
          <button className={`hcn-tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => handleTabChange('all')}>
            الكل <span className="hcn-tab-badge">{customers.length}</span>
          </button>
          <button className={`hcn-tab ${activeTab === 'authenticated' ? 'active' : ''}`} onClick={() => handleTabChange('authenticated')}>
            موثق <span className="hcn-tab-badge">{customers.filter(c => c.auth_state === 'AUTHENTICATED' || c.authenticated).length}</span>
          </button>
          <button className={`hcn-tab ${activeTab === 'unauthenticated' ? 'active' : ''}`} onClick={() => handleTabChange('unauthenticated')}>
            غير موثق <span className="hcn-tab-badge">{customers.filter(c => c.auth_state !== 'AUTHENTICATED' && !c.authenticated).length}</span>
          </button>
        </div>

        {/* شريط البحث و الفلتر */}
        <div style={{ padding: '20px 24px', display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 500 }}>
            <Search size={20} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }} />
            <input
              type="text"
              placeholder="بحث بالاسم أو معرف التلجرام أو معرف العميل..."
              value={search}
              onChange={handleSearchChange}
              className="hcn-input"
              style={{ paddingRight: 44 }}
            />
          </div>
          {selected.length > 0 && hasPermission('delete_chat_sessions') && (
            <button onClick={handleBatchDelete} className="hcn-btn-secondary" style={{ color: 'var(--error)', borderColor: 'var(--error)' }}>
              <Trash2 size={16} /> حذف المحدد ({selected.length})
            </button>
          )}
        </div>

        {/* الجدول */}
        <div className="hcn-table-wrapper">
          <table className="hcn-table">
            <thead>
              <tr>
                <th style={{ width: 60, paddingRight: 24 }}>
                  <input
                    type="checkbox"
                    checked={selected.length === paginated.length && paginated.length > 0}
                    onChange={toggleAll}
                    style={{ accentColor: 'var(--primary)', width: 18, height: 18, cursor: 'pointer' }}
                  />
                </th>
                <th>المشترك / الجلسة</th>
                <th>معرف العميل (CRM)</th>
                <th>المصادقة</th>
                <th>آخر تفاعل</th>
                <th>تاريخ البدء</th>
                <th style={{ width: 60 }}></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-disabled)' }}>
                    جاري تحميل بيانات العملاء...
                  </td>
                </tr>
              ) : paginated.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-disabled)' }}>
                    لا يوجد عملاء مطابقين للبحث
                  </td>
                </tr>
              ) : (
                paginated.map(c => (
                  <TableRow
                    key={c.session_id}
                    cust={c}
                    selected={selected.includes(c.session_id)}
                    onSelect={toggleSelect}
                    onOpen={setOpenCustomer}
                    onDelete={handleDeleteSession}
                    hasPermission={hasPermission}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border)' }}>
            <span style={{ fontSize: 13, color: 'var(--text-disabled)' }}>
              عرض {page * rowsPerPage + 1} إلى {Math.min((page + 1) * rowsPerPage, filtered.length)} من {filtered.length} عميل
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="hcn-btn-secondary"
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
                style={{ padding: '8px 12px' }}
              >
                <ChevronRight size={18} />
              </button>
              <button
                className="hcn-btn-secondary"
                disabled={page >= totalPages - 1}
                onClick={() => setPage(p => p + 1)}
                style={{ padding: '8px 12px' }}
              >
                <ChevronLeft size={18} />
              </button>
            </div>
          </div>
        )}
      </div>

      {openCustomer && (
        <DetailModal
          cust={openCustomer}
          onClose={() => setOpenCustomer(null)}
          onDelete={handleDeleteSession}
          requireAuth={requireAuth}
          hasPermission={hasPermission}
        />
      )}
    </div>
  );
}
