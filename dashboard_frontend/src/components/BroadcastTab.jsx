import React, { useState, useEffect } from 'react';
import {
  Megaphone,
  Users,
  UserCheck,
  UserX,
  CheckCircle2,
  AlertCircle,
  Send,
  RefreshCw,
  Search,
  CheckSquare,
  Square,
  Clock,
  Sparkles,
  MessageSquare,
  Info,
  X,
  ChevronLeft,
  FileText
} from 'lucide-react';
import { usePasswordAuth, PasswordPromptModal } from './PasswordPromptModal';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const QUICK_TEMPLATES = [
  {
    id: 'maintenance',
    title: 'تنبيه: صيانة مجدولة في شبكة الإنترنت',
    text: 'نحيطكم علماً بوجود أعمال صيانة دورية لتحسين جودة الخدمة غداً من الساعة 2:00 إلى 4:00 صباحاً. قد يطرأ انقطاع مؤقت. شكراً لتفهمكم.',
  },
  {
    id: 'renew',
    title: 'تذكير: اقتراب موعد تجديد باقة الإنترنت',
    text: 'عزيزي المشترك، نقترب من نهاية دورة باقتك الحالية. لتجنب انقطاع الخدمة يرجى تسديد الرصيد أو تجديد الباقة عبر البوت أو أقرب مركز خدمة.',
  },
  {
    id: 'offer',
    title: 'عرض خاص: مضاعفة سرعة الإنترنت مجاناً',
    text: 'بمناسبة نهاية الشهر، تمتع بمضاعفة السرعة لجميع باقات ADSL غير المحدودة لمدة 3 أيام مجاناً! تابع استهلاكك عبر البوت في أي وقت.',
  },
  {
    id: 'support',
    title: 'تحديث: تحسينات جديدة في بوت هايبرنت',
    text: 'يسرنا إعلامكم بإضافة ميزة الاستعلام الفوري عن الفواتير ورفع تذاكر الدعم الفني مباشرة عبر البوت! جرب كتابة /help لاكتشاف المزايا.',
  }
];

export default function BroadcastTab() {
  const [subscribers, setSubscribers] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [subscribersLoading, setSubscribersLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Form State
  const [targetType, setTargetType] = useState('ALL'); // 'ALL' | 'AUTHED' | 'UNAUTHED' | 'CUSTOM'
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [title, setTitle] = useState('إشعار هام من هايبرنت');
  const [message, setMessage] = useState('');

  // UI Controls
  const [showUserModal, setShowUserModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [userFilter, setUserFilter] = useState('ALL'); // 'ALL' | 'AUTHED' | 'UNAUTHED'
  const [broadcastResult, setBroadcastResult] = useState(null);

  const { requireAuth, modalProps } = usePasswordAuth();

  // Fetch Subscribers & History
  const fetchSubscribers = async () => {
    setSubscribersLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/notifications/subscribers`);
      if (res.ok) {
        const data = await res.json();
        setSubscribers(data);
      }
    } catch (err) {
      console.error('Failed to fetch subscribers:', err);
    } finally {
      setSubscribersLoading(false);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/notifications/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('Failed to fetch broadcast history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscribers();
    fetchHistory();
  }, []);

  // Compute Audience Counts
  const totalCount = subscribers.length;
  const authedCount = subscribers.filter(s => s.authenticated).length;
  const unauthedCount = subscribers.filter(s => !s.authenticated).length;

  const getRecipientCount = () => {
    if (targetType === 'ALL') return totalCount;
    if (targetType === 'AUTHED') return authedCount;
    if (targetType === 'UNAUTHED') return unauthedCount;
    if (targetType === 'CUSTOM') return selectedUserIds.length;
    return 0;
  };

  // Filtered Subscribers for Modal
  const modalFilteredUsers = subscribers.filter(user => {
    const searchStr = userSearch.toLowerCase();
    const uname = (user.user_name || '').toLowerCase();
    const sid = (user.session_id || '').toLowerCase();
    const cid = (user.customer_id || '').toLowerCase();
    const uid = (user.user_id ? String(user.user_id) : '').toLowerCase();

    const matchesSearch =
      sid.includes(searchStr) ||
      cid.includes(searchStr) ||
      uname.includes(searchStr) ||
      uid.includes(searchStr);

    if (!matchesSearch) return false;
    if (userFilter === 'AUTHED') return user.authenticated;
    if (userFilter === 'UNAUTHED') return !user.authenticated;
    return true;
  });

  const toggleUserSelect = (sessionId) => {
    if (selectedUserIds.includes(sessionId)) {
      setSelectedUserIds(selectedUserIds.filter(id => id !== sessionId));
    } else {
      setSelectedUserIds([...selectedUserIds, sessionId]);
    }
  };

  const selectAllFiltered = () => {
    const ids = modalFilteredUsers.map(u => u.session_id);
    const combined = Array.from(new Set([...selectedUserIds, ...ids]));
    setSelectedUserIds(combined);
  };

  const clearSelection = () => {
    setSelectedUserIds([]);
  };

  // Apply Quick Template
  const applyTemplate = (tpl) => {
    setTitle(tpl.title);
    setMessage(tpl.text);
  };

  // Handle Send Broadcast
  const handleSendBroadcast = async () => {
    setShowConfirmModal(false);
    setLoading(true);
    setBroadcastResult(null);

    try {
      const payload = {
        target: targetType,
        user_ids: targetType === 'CUSTOM' ? selectedUserIds : undefined,
        title: title.trim() || 'إشعار من هايبرنت',
        message: message.trim(),
        sent_by: 'مدير النظام (Dashboard Admin)'
      };

      const res = await fetch(`${API_BASE}/api/notifications/broadcast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok) {
        setBroadcastResult({
          type: 'success',
          message: `تم إرسال الإشعار بنجاح إلى ${data.sent_count} من أصل ${data.total_recipients} مشترك.`
        });
        setMessage('');
        fetchHistory();
      } else {
        setBroadcastResult({
          type: 'error',
          message: data.detail || 'حدث خطأ أثناء إرسال الإشعار'
        });
      }
    } catch (err) {
      setBroadcastResult({
        type: 'error',
        message: 'تعذر الاتصال بالخادم، يرجى التأكد من تشغيل الـ Backend'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }} dir="rtl">
      <PasswordPromptModal {...modalProps} />

      {/* ── Page Header ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
          <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            <Megaphone size={26} color="var(--primary)" />
            بث الإشعارات والتنبيهات
            <span className="hcn-badge hcn-badge-success">Telegram Broadcast</span>
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={() => { fetchSubscribers(); fetchHistory(); }}
            disabled={subscribersLoading || historyLoading}
            className="hcn-btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <RefreshCw size={16} style={{ animation: (subscribersLoading || historyLoading) ? 'spin 1s linear infinite' : 'none' }} />
            تحديث البيانات
          </button>
        </div>
      </div>

      {/* ── Top Summary Stats ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
        <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(0, 167, 111, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Users size={24} color="var(--primary)" />
          </div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>إجمالي المشتركين</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{totalCount}</div>
          </div>
        </div>

        <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <UserCheck size={24} color="var(--success)" />
          </div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>المشتركين الموثقين</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--success)' }}>{authedCount}</div>
          </div>
        </div>

        <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <UserX size={24} color="#64748b" />
          </div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>غير الموثقين (زوار)</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{unauthedCount}</div>
          </div>
        </div>

        <div className="hcn-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Send size={24} color="var(--info)" />
          </div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 600 }}>الحملات المرسلة</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--info)' }}>{history.length}</div>
          </div>
        </div>
      </div>

      {/* ── Status Alert Banner ── */}
      {broadcastResult && (
        <div style={{
          padding: '16px 20px',
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: broadcastResult.type === 'success' ? 'var(--success-bg)' : 'var(--error-bg)',
          border: `1px solid ${broadcastResult.type === 'success' ? 'rgba(0, 167, 111, 0.3)' : 'rgba(255, 86, 48, 0.3)'}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {broadcastResult.type === 'success' ? (
              <CheckCircle2 size={22} color="var(--success)" />
            ) : (
              <AlertCircle size={22} color="var(--error)" />
            )}
            <span style={{ fontSize: 14, fontWeight: 600, color: broadcastResult.type === 'success' ? 'var(--success)' : 'var(--error)' }}>
              {broadcastResult.message}
            </span>
          </div>
          <button
            onClick={() => setBroadcastResult(null)}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
          >
            <X size={18} />
          </button>
        </div>
      )}

      {/* ── Main Composer & Live Preview Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24 }}>

        {/* ── Column 1: Notification Composer ── */}
        <div className="hcn-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Send size={20} color="var(--primary)" />
              إعداد الإشعار والبث
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
              اختر الفئة المستهدفة واكتب نص الرسالة التي ستصل فوراً على تطبيق تلجرام.
            </p>
          </div>

          {/* 1. Audience Target Selector */}
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
              1. الفئة المستهدفة (الجمهور)
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>

              {/* Option: ALL */}
              <div
                onClick={() => setTargetType('ALL')}
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  cursor: 'pointer',
                  border: `2px solid ${targetType === 'ALL' ? 'var(--primary)' : 'var(--border)'}`,
                  background: targetType === 'ALL' ? 'rgba(0, 167, 111, 0.06)' : 'var(--bg-default)',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}
              >
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'rgba(0, 167, 111, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Users size={18} color="var(--primary)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>جميع المشتركين</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{totalCount} مستخدم</div>
                </div>
                {targetType === 'ALL' && <CheckCircle2 size={20} color="var(--primary)" />}
              </div>

              {/* Option: AUTHED */}
              <div
                onClick={() => setTargetType('AUTHED')}
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  cursor: 'pointer',
                  border: `2px solid ${targetType === 'AUTHED' ? 'var(--primary)' : 'var(--border)'}`,
                  background: targetType === 'AUTHED' ? 'rgba(0, 167, 111, 0.06)' : 'var(--bg-default)',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}
              >
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserCheck size={18} color="var(--success)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>الموثقين فقط</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{authedCount} مشترك</div>
                </div>
                {targetType === 'AUTHED' && <CheckCircle2 size={20} color="var(--primary)" />}
              </div>

              {/* Option: UNAUTHED */}
              <div
                onClick={() => setTargetType('UNAUTHED')}
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  cursor: 'pointer',
                  border: `2px solid ${targetType === 'UNAUTHED' ? 'var(--primary)' : 'var(--border)'}`,
                  background: targetType === 'UNAUTHED' ? 'rgba(0, 167, 111, 0.06)' : 'var(--bg-default)',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}
              >
                <div style={{ width: 36, height: 36, borderRadius: 8, background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserX size={18} color="#64748b" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>غير الموثقين</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{unauthedCount} زائر</div>
                </div>
                {targetType === 'UNAUTHED' && <CheckCircle2 size={20} color="var(--primary)" />}
              </div>

              {/* Option: CUSTOM */}
              <div
                onClick={() => { setTargetType('CUSTOM'); setShowUserModal(true); }}
                style={{
                  padding: '16px',
                  borderRadius: 10,
                  cursor: 'pointer',
                  border: `2px solid ${targetType === 'CUSTOM' ? 'var(--primary)' : 'var(--border)'}`,
                  background: targetType === 'CUSTOM' ? 'rgba(0, 167, 111, 0.06)' : 'var(--bg-default)',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12
                }}
              >
                <div style={{ width: 36, height: 36, borderRadius: 8, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <CheckSquare size={18} color="var(--info)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>تحديد مخصص</div>
                  <div style={{ fontSize: 12, color: selectedUserIds.length > 0 ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: selectedUserIds.length > 0 ? 700 : 500 }}>
                    {selectedUserIds.length > 0 ? `${selectedUserIds.length} تم تحديدهم` : 'انقر للاختيار'}
                  </div>
                </div>
                {targetType === 'CUSTOM' && <CheckCircle2 size={20} color="var(--primary)" />}
              </div>

            </div>

            {targetType === 'CUSTOM' && (
              <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(0, 167, 111, 0.08)', borderRadius: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
                  المشتركين المحددين يدوياً: <strong>{selectedUserIds.length}</strong>
                </span>
                <button
                  onClick={() => setShowUserModal(true)}
                  className="hcn-btn-secondary"
                  style={{ padding: '6px 12px', fontSize: 12 }}
                >
                  تعديل القائمة المحددة
                </button>
              </div>
            )}
          </div>

          {/* 2. Quick Templates */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
              <Sparkles size={16} color="var(--primary)" />
              <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                قوالب رسائل جاهزة
              </label>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {QUICK_TEMPLATES.map(tpl => (
                <button
                  key={tpl.id}
                  type="button"
                  onClick={() => applyTemplate(tpl)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 20,
                    border: '1px solid var(--border)',
                    background: 'var(--bg-default)',
                    fontSize: 12,
                    fontWeight: 600,
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    fontFamily: 'inherit',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--primary)';
                    e.currentTarget.style.color = 'var(--primary)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border)';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  {tpl.title.split(':')[0] || tpl.title}
                </button>
              ))}
            </div>
          </div>

          {/* 3. Title Input */}
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              2. عنوان الإشعار (العنوان العريض)
            </label>
            <input
              type="text"
              className="hcn-input"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="مثال: تنبيه صيانة دورية، عروض خاصة..."
              style={{ width: '100%' }}
            />
          </div>

          {/* 4. Message Textarea */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                3. نص الإشعار
              </label>
              <span style={{ fontSize: 12, color: message.length > 500 ? '#ef4444' : 'var(--text-disabled)' }}>
                {message.length} حرف
              </span>
            </div>
            <textarea
              className="hcn-input"
              rows={5}
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="اكتب محتوى الإشعار هنا... سيتم إرساله وتنسيقه مباشرة في محادثة تلجرام للمشتركين."
              style={{ width: '100%', resize: 'vertical', lineHeight: 1.6 }}
            />
          </div>

          {/* 5. Submit Button */}
          <div style={{ paddingTop: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              سيتم إرسال هذا الإشعار إلى <strong style={{ color: 'var(--primary)' }}>{getRecipientCount()}</strong> مستخدم
            </div>

            <button
              onClick={() => setShowConfirmModal(true)}
              disabled={!message.trim() || getRecipientCount() === 0 || loading}
              className="hcn-btn-primary"
              style={{
                padding: '12px 28px',
                fontSize: 15,
                fontWeight: 700,
                opacity: (!message.trim() || getRecipientCount() === 0 || loading) ? 0.6 : 1,
                cursor: (!message.trim() || getRecipientCount() === 0 || loading) ? 'not-allowed' : 'pointer'
              }}
            >
              <Send size={18} />
              {loading ? 'جارِ البث...' : 'إرسال الإشعار الآن'}
            </button>
          </div>

        </div>

        {/* ── Column 2: Live Telegram Message Preview ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          <div className="hcn-card" style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column' }}>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <MessageSquare size={18} color="var(--primary)" />
                <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>معاينة حية على Telegram</span>
              </div>
              <span className="hcn-badge hcn-badge-info">Live Preview</span>
            </div>

            {/* Telegram Phone Simulator Frame */}
            <div style={{
              background: '#0e1621',
              borderRadius: 16,
              padding: '20px 16px',
              color: '#fff',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
              border: '1px solid #242f3d'
            }}>

              {/* Bot Header Bar */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                paddingBottom: 12,
                borderBottom: '1px solid #17212b'
              }}>
                <div style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  background: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700,
                  fontSize: 16,
                  color: '#fff'
                }}>
                  H
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#f5f5f5' }}>HYPERNET Bot</div>
                  <div style={{ fontSize: 11, color: '#4fa3e3' }}>bot • online</div>
                </div>
              </div>

              {/* Chat Body & Bubble */}
              <div style={{ padding: '24px 8px', display: 'flex', flexDirection: 'column', gap: 12, flex: 1, justifyContent: 'center' }}>

                {/* Date separator */}
                <div style={{ alignSelf: 'center', background: 'rgba(0,0,0,0.3)', padding: '4px 12px', borderRadius: 12, fontSize: 11, color: '#7f8c9b' }}>
                  اليوم
                </div>

                {/* Telegram Message Bubble */}
                <div style={{
                  alignSelf: 'flex-start',
                  maxWidth: '90%',
                  background: '#182533',
                  borderRadius: '12px 12px 12px 2px',
                  padding: '14px 16px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                  border: '1px solid #2b394a'
                }}>

                  {/* Title */}
                  <div style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: '#64b5f6',
                    marginBottom: 8,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}>
                    <span>{title || 'عنوان الإشعار'}</span>
                  </div>

                  {/* Message body */}
                  <div style={{
                    fontSize: 13,
                    lineHeight: 1.6,
                    color: '#e0e0e0',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}>
                    {message.trim() || 'نص الإشعار سيظهر هنا للمشتركين بشكل منسق وجذاب...'}
                  </div>

                  {/* Timestamp & Read indicator */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: 4,
                    marginTop: 8,
                    fontSize: 10,
                    color: '#7f8c9b'
                  }}>
                    <span>10:30 AM</span>
                  </div>

                </div>

              </div>

              {/* Simulated input bar */}
              <div style={{
                padding: '10px 14px',
                background: '#17212b',
                borderRadius: 24,
                fontSize: 12,
                color: '#6c7883',
                textAlign: 'right'
              }}>
                اكتب رسالة...
              </div>

            </div>

          </div>

        </div>

      </div>

      {/* ── Broadcast History Table ── */}
      <div className="hcn-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Clock size={20} color="var(--primary)" />
              سجل الإشعارات والحملات السابقة
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
              تاريخ جميع الرسائل والبثوث الإدارية التي تم إرسالها لمشتركي البوت.
            </p>
          </div>
          <span className="hcn-badge hcn-badge-info">{history.length} حملة</span>
        </div>

        {historyLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-disabled)' }}>
            جارِ تحميل سجل الإشعارات...
          </div>
        ) : history.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-disabled)', background: 'var(--bg-default)', borderRadius: 8 }}>
            لا يوجد إشعارات سابقة حتى الآن. يمكنك إرسال أول إشعار الآن من النموذج أعلاه.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="hcn-table" style={{ width: '100%', textAlign: 'right' }}>
              <thead>
                <tr>
                  <th style={{ padding: '12px 16px' }}>التاريخ والوقت</th>
                  <th style={{ padding: '12px 16px' }}>عنوان الإشعار</th>
                  <th style={{ padding: '12px 16px' }}>نص الرسالة</th>
                  <th style={{ padding: '12px 16px' }}>الفئة المستهدفة</th>
                  <th style={{ padding: '12px 16px' }}>المستلمين</th>
                  <th style={{ padding: '12px 16px' }}>المرسل</th>
                  <th style={{ padding: '12px 16px' }}>الحالة</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-disabled)', whiteSpace: 'nowrap' }}>
                      {item.timestamp}
                    </td>
                    <td style={{ padding: '14px 16px', fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                      {item.title}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-secondary)', maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.message}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {item.target === 'ALL' && <span className="hcn-badge hcn-badge-info">الكل</span>}
                      {item.target === 'AUTHED' && <span className="hcn-badge hcn-badge-success">الموثقين</span>}
                      {item.target === 'UNAUTHED' && <span className="hcn-badge hcn-badge-warning">غير الموثقين</span>}
                      {item.target === 'CUSTOM' && <span className="hcn-badge hcn-badge-default">تحديد مخصص</span>}
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, fontWeight: 600 }}>
                      <span style={{ color: 'var(--success)' }}>{item.sent_count}</span>
                      <span style={{ color: 'var(--text-disabled)' }}> / {item.target_count}</span>
                    </td>
                    <td style={{ padding: '14px 16px', fontSize: 13, color: 'var(--text-secondary)' }}>
                      {item.sent_by}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {item.status === 'SUCCESS' ? (
                        <span className="hcn-badge hcn-badge-success">ناجح</span>
                      ) : item.status === 'PARTIAL' ? (
                        <span className="hcn-badge hcn-badge-warning">جزئي</span>
                      ) : (
                        <span className="hcn-badge hcn-badge-error">فشل</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

      {/* ── Modal: Custom Subscriber Selector ── */}
      {showUserModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(4px)'
        }}>
          <div className="hcn-card" style={{
            width: '95%',
            maxWidth: 950,
            maxHeight: '85vh',
            display: 'flex',
            flexDirection: 'column',
            padding: 0,
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(0,0,0,0.3)'
          }}>

            {/* Modal Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  تحديد المشتركين المستهدفين يدوياً
                </h3>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                  تم تحديد <strong style={{ color: 'var(--primary)' }}>{selectedUserIds.length}</strong> من أصل {subscribers.length} مشترك
                </div>
              </div>
              <button
                onClick={() => setShowUserModal(false)}
                style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
              >
                <X size={22} />
              </button>
            </div>

            {/* Modal Filters & Search Bar */}
            <div style={{ padding: '16px 24px', borderBottom: '1px solid var(--border)', background: 'var(--bg-default)', display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
                <Search size={18} color="var(--text-disabled)" style={{ position: 'absolute', right: 12, top: 12 }} />
                <input
                  type="text"
                  className="hcn-input"
                  placeholder="بحث بمعرف المحادثة (Telegram ID) أو اسم المستخدم أو رقم العميل..."
                  value={userSearch}
                  onChange={e => setUserSearch(e.target.value)}
                  style={{ width: '100%', paddingRight: 38 }}
                />
              </div>

              {/* Filter Buttons */}
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  onClick={() => setUserFilter('ALL')}
                  className={userFilter === 'ALL' ? 'hcn-btn-primary' : 'hcn-btn-secondary'}
                  style={{ padding: '8px 12px', fontSize: 12 }}
                >
                  الكل ({subscribers.length})
                </button>
                <button
                  onClick={() => setUserFilter('AUTHED')}
                  className={userFilter === 'AUTHED' ? 'hcn-btn-primary' : 'hcn-btn-secondary'}
                  style={{ padding: '8px 12px', fontSize: 12 }}
                >
                  موثق ({authedCount})
                </button>
                <button
                  onClick={() => setUserFilter('UNAUTHED')}
                  className={userFilter === 'UNAUTHED' ? 'hcn-btn-primary' : 'hcn-btn-secondary'}
                  style={{ padding: '8px 12px', fontSize: 12 }}
                >
                  غير موثق ({unauthedCount})
                </button>
              </div>

              {/* Bulk Select/Clear */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={selectAllFiltered} className="hcn-btn-secondary" style={{ padding: '8px 12px', fontSize: 12 }}>
                  تحديد الكل الظاهر
                </button>
                <button onClick={clearSelection} className="hcn-btn-secondary" style={{ padding: '8px 12px', fontSize: 12, color: 'var(--error)' }}>
                  إلغاء التحديد
                </button>
              </div>
            </div>

            {/* Modal Subscribers List */}
            <div style={{ flex: 1, overflowY: 'auto', padding: '0 24px' }}>
              <table className="hcn-table" style={{ width: '100%', textAlign: 'right' }}>
                <thead>
                  <tr>
                    <th style={{ width: 40, padding: '12px 8px' }}>اختيار</th>
                    <th style={{ padding: '12px 16px' }}>معرف المحادثة</th>
                    <th style={{ padding: '12px 16px' }}>Telegram ID</th>
                    <th style={{ padding: '12px 16px' }}>اسم المستخدم</th>
                    <th style={{ padding: '12px 16px' }}>رقم المشترك</th>
                    <th style={{ padding: '12px 16px' }}>حالة التوثيق</th>
                    <th style={{ padding: '12px 16px' }}>آخر تفاعل</th>
                  </tr>
                </thead>
                <tbody>
                  {modalFilteredUsers.map((user) => {
                    const isSelected = selectedUserIds.includes(user.session_id);
                    return (
                      <tr
                        key={user.session_id}
                        onClick={() => toggleUserSelect(user.session_id)}
                        style={{ cursor: 'pointer', background: isSelected ? 'rgba(0, 167, 111, 0.05)' : undefined }}
                      >
                        <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                          {isSelected ? (
                            <CheckSquare size={18} color="var(--primary)" />
                          ) : (
                            <Square size={18} color="var(--text-disabled)" />
                          )}
                        </td>
                        <td style={{ padding: '12px 16px', fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
                          {user.session_id}
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text-secondary)' }}>
                          {user.user_id || 'غير متوفر'}
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text-secondary)', direction: 'ltr', textAlign: 'right' }}>
                          {user.user_name || 'غير متوفر'}
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: 13, color: 'var(--text-secondary)' }}>
                          {user.customer_id || 'غير محدد'}
                        </td>
                        <td style={{ padding: '12px 16px' }}>
                          {user.authenticated ? (
                            <span className="hcn-badge hcn-badge-success">موثق</span>
                          ) : (
                            <span className="hcn-badge hcn-badge-warning">غير موثق</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-disabled)' }}>
                          {user.last_active}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Modal Footer */}
            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-default)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                تم اختيار <strong style={{ color: 'var(--primary)' }}>{selectedUserIds.length}</strong> مستخدم
              </span>
              <button
                onClick={() => setShowUserModal(false)}
                className="hcn-btn-primary"
                style={{ padding: '8px 24px' }}
              >
                تأكيد الاختيار
              </button>
            </div>

          </div>
        </div>
      )}

      {/* ── Modal: Confirmation Before Sending ── */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          backdropFilter: 'blur(4px)'
        }}>
          <div className="hcn-card" style={{
            width: '90%',
            maxWidth: 480,
            padding: '28px',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            boxShadow: '0 20px 40px rgba(0,0,0,0.3)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(0, 167, 111, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Send size={24} color="var(--primary)" />
              </div>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                  تأكيد إرسال الإشعار
                </h3>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                  يرجى مراجعة التفاصيل قبل المتابعة
                </div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-default)', padding: '16px', borderRadius: 10, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>الجمهور المستهدف:</span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                  {targetType === 'ALL' && 'جميع المشتركين'}
                  {targetType === 'AUTHED' && 'المشتركين الموثقين فقط'}
                  {targetType === 'UNAUTHED' && 'غير الموثقين فقط'}
                  {targetType === 'CUSTOM' && 'مشتركين محددين يدوياً'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>عدد المستلمين:</span>
                <span style={{ fontWeight: 700, color: 'var(--primary)' }}>{getRecipientCount()} مستخدم</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>عنوان الإشعار:</span>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{title}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
              <button
                onClick={() => setShowConfirmModal(false)}
                className="hcn-btn-secondary"
                style={{ padding: '10px 20px' }}
              >
                إلغاء
              </button>
              <button
                onClick={handleSendBroadcast}
                className="hcn-btn-primary"
                style={{ padding: '10px 24px' }}
              >
                نعم، ابدأ البث الآن
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
