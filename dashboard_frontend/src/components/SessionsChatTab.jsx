import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Search, Eye, User, Cpu, RefreshCw, Send, ZoomIn, Image as ImageIcon } from 'lucide-react';
import { usePasswordAuth, PasswordPromptModal } from './PasswordPromptModal';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SESSION_KEY = 'hypernet_selected_session';

export default function SessionsChatTab() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState(
    () => localStorage.getItem(SESSION_KEY) || null
  );
  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAuth, setFilterAuth] = useState('ALL');
  const [replyText, setReplyText] = useState('');
  const [sendingReply, setSendingReply] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const chatEndRef = useRef(null);

  const { requireAuth, modalProps } = usePasswordAuth();

  // Persist session selection
  const selectSession = (id) => {
    localStorage.setItem(SESSION_KEY, id);
    // Save current draft before switching
    if (selectedSessionId) {
      const draftKey = `hypernet_draft_${selectedSessionId}`;
      if (replyText.trim()) localStorage.setItem(draftKey, replyText);
      else localStorage.removeItem(draftKey);
    }
    setSelectedSessionId(id);
    // Restore draft for the new session
    const newDraft = localStorage.getItem(`hypernet_draft_${id}`) || '';
    setReplyText(newDraft);
  };

  // ── Fetch all sessions from backend ──
  const fetchSessions = () => {
    fetch(`${API_BASE}/api/crm/customers`)
      .then((res) => res.json())
      .then((data) => {
        setSessions(data);
        setLoading(false);
        // Only auto-select if no session was previously saved
        const saved = localStorage.getItem(SESSION_KEY);
        const savedExists = data.some((s) => s.session_id === saved);
        if (!savedExists && data.length > 0) {
          selectSession(data[0].session_id);
        } else if (!selectedSessionId && !saved && data.length > 0) {
          selectSession(data[0].session_id);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch sessions:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 4000);
    return () => clearInterval(interval);
  }, []);

  // ── Fetch messages for selected session ──
  const fetchMsgs = () => {
    if (!selectedSessionId) return;
    fetch(`${API_BASE}/api/sessions/${selectedSessionId}/messages`)
      .then((res) => res.json())
      .then((data) => {
        setMessages(data);
        setLoadingMessages(false);
      })
      .catch((err) => {
        console.error('Failed to fetch messages:', err);
        setLoadingMessages(false);
      });
  };

  useEffect(() => {
    if (!selectedSessionId) return;
    setLoadingMessages(true);
    fetchMsgs();
    const interval = setInterval(fetchMsgs, 3000);
    return () => clearInterval(interval);
  }, [selectedSessionId]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, selectedSessionId]);

  const handleSendReply = async () => {
    if (!replyText.trim() || sendingReply || !selectedSessionId) return;
    requireAuth('إرسال رد للمشترك', async () => {
      setSendingReply(true);
      try {
        const res = await fetch(`${API_BASE}/api/sessions/${selectedSessionId}/reply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: replyText.trim() })
        });
        if (res.ok) {
          setReplyText('');
          fetchMsgs();
        }
      } catch (err) {
        console.error('Failed to send reply:', err);
      } finally {
        setSendingReply(false);
      }
    });
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

  const activeSession = sessions.find((s) => s.session_id === selectedSessionId) || sessions[0] || {
    session_id: 'N/A',
    customer_id: 'غير مرتبط',
    authenticated: false,
    auth_state: 'UNAUTHENTICATED',
    lastActive: 'لا يوجد',
    created_at: 'غير معروف',
  };

  const isAuthed = activeSession.auth_state === 'AUTHENTICATED' || activeSession.authenticated;

  const filteredSessions = sessions.filter((s) => {
    const sId = (s.session_id || '').toLowerCase();
    const cId = (s.customer_id || '').toLowerCase();
    const q = searchTerm.toLowerCase();
    const matchSearch = sId.includes(q) || cId.includes(q);

    const sAuthed = s.auth_state === 'AUTHENTICATED' || s.authenticated;
    const matchAuth =
      filterAuth === 'ALL' ||
      (filterAuth === 'AUTH' && sAuthed) ||
      (filterAuth === 'GUEST' && !sAuthed);

    return matchSearch && matchAuth;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, height: 'calc(100vh - 64px)' }}>
      <PasswordPromptModal {...modalProps} />
      {/* ── رأس الصفحة ── */}
      <div
        className="hcn-page-header"
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0, paddingBottom: 16 }}
      >
        <div>
          <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            مراقبة المحادثات والرد المباشر
            <span className="hcn-badge hcn-badge-success">حي ومباشر</span>
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <button onClick={fetchSessions} className="hcn-btn-secondary" style={{ padding: '8px 16px', fontSize: 13, gap: 6, display: 'flex', alignItems: 'center' }}>
            <RefreshCw size={14} /> تحديث
          </button>
          <span className="hcn-badge hcn-badge-success" style={{ padding: '8px 16px', fontSize: 13, gap: 6 }}>
            <span className="hcn-dot hcn-dot-green hcn-dot-pulse" /> {sessions.length} جلسة مسجلة
          </span>
        </div>
      </div>

      {/* ── اللوحة المزدوجة ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24, flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {/* قائمة الجلسات */}
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', padding: 24, overflow: 'hidden' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 16 }}>
            <div style={{ position: 'relative' }}>
              <Search
                size={20}
                style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }}
              />
              <input
                type="text"
                placeholder="بحث في معرف الجلسة أو العميل..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="hcn-input"
                style={{ paddingRight: 44 }}
              />
            </div>
            <div className="hcn-pill-group" style={{ width: '100%', display: 'flex' }}>
              {[
                { key: 'ALL', label: 'الكل' },
                { key: 'AUTH', label: 'موثّق' },
                { key: 'GUEST', label: 'غير موثّق' },
              ].map((m) => (
                <button
                  key={m.key}
                  className={`hcn-pill ${filterAuth === m.key ? 'active-primary' : ''}`}
                  onClick={() => setFilterAuth(m.key)}
                  style={{ flex: 1 }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, paddingLeft: 4 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-disabled)' }}>جاري تحميل الجلسات...</div>
            ) : filteredSessions.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-disabled)' }}>لا توجد جلسات مطابقة للبحث</div>
            ) : (
              filteredSessions.map((s) => {
                const isSelected = s.session_id === selectedSessionId;
                const isAuth = s.auth_state === 'AUTHENTICATED' || s.authenticated;

                return (
                  <div
                    key={s.session_id}
                    onClick={() => selectSession(s.session_id)}
                    style={{
                      padding: 16,
                      borderRadius: 12,
                      border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                      background: isSelected ? 'var(--primary-light, rgba(0, 102, 255, 0.06))' : 'var(--bg-paper)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div
                        style={{
                          width: 40,
                          height: 40,
                          borderRadius: 10,
                          background: isAuth ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <User size={20} color={isAuth ? 'var(--success)' : 'var(--text-secondary)'} />
                      </div>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14, fontFamily: 'monospace', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {(s.user_name && s.user_name !== s.session_id) ? (
                            s.user_name.includes(' (@') ? (
                              <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                                <span>{s.user_name.split(' (@')[0]}</span>
                                <span style={{ fontSize: 12, color: 'var(--text-disabled)' }}>@{s.user_name.split(' (@')[1].replace(')', '')}</span>
                              </div>
                            ) : s.user_name
                          ) : (s.user_id || s.session_id)}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-disabled)', marginTop: 2 }}>
                          {s.customer_id !== 'غير مرتبط' ? `حساب: ${s.customer_id}` : 'مستخدم زائر'}
                        </div>
                      </div>
                    </div>
                    <span className={`hcn-badge ${isAuth ? 'hcn-badge-success' : 'hcn-badge-warning'}`} style={{ fontSize: 11 }}>
                      {isAuth ? 'موثق' : 'ضيف'}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* لوحة تفاصيل المحادثة والرد */}
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          {/* رأس المحادثة */}
          <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--info-bg, rgba(59, 130, 246, 0.12))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={22} color="var(--primary)" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>
                    {(activeSession.user_name && activeSession.user_name !== activeSession.session_id) 
                      ? activeSession.user_name 
                      : (activeSession.user_id || 'مستخدم زائر (Web)')}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-disabled)', fontFamily: 'monospace', background: 'var(--bg-hover)', padding: '2px 6px', borderRadius: 4 }}>
                    ID: {activeSession.user_id || (activeSession.session_id.length > 20 ? `${activeSession.session_id.substring(0,8)}...` : activeSession.session_id)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    حالة المصادقة: <strong style={{ color: isAuthed ? 'var(--success)' : 'var(--text-secondary)' }}>{isAuthed ? 'موثق' : 'غير موثق'}</strong>
                  </span>
                  <span style={{ color: 'var(--text-disabled)' }}>•</span>
                  <span style={{ color: 'var(--text-secondary)' }}>
                    تاريخ البدء: <strong style={{ fontFamily: 'monospace' }}>{activeSession.created_at}</strong>
                  </span>
                </div>
              </div>
            </div>
            <span className={`hcn-badge ${isAuthed ? 'hcn-badge-success' : 'hcn-badge-warning'}`} style={{ padding: '6px 14px', fontSize: 12 }}>
              {isAuthed ? 'مستخدم موثّق' : 'ضيف (غير موثّق)'}
            </span>
          </div>

          {/* الرسائل الحية */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 18, background: 'var(--bg-default)' }}>
            {loadingMessages && messages.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-disabled)', margin: 'auto' }}>جاري تحميل سجل المحادثة...</div>
            ) : messages.length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-disabled)', margin: 'auto' }}>لا توجد رسائل مسجلة لهذه الجلسة حتى الآن</div>
            ) : (
              messages.map((msg, i) => {
                const isUser = msg.sender === 'user';
                const isAdmin = msg.sender === 'admin';
                return (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: isUser ? 'flex-start' : 'flex-end',
                      maxWidth: '75%',
                      alignSelf: isUser ? 'flex-start' : 'flex-end'
                    }}
                  >
                    <div
                      style={{
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
                        border: (isUser || isAdmin) ? 'none' : '1px solid var(--border)',
                      }}
                    >
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
              disabled={sendingReply || !replyText.trim() || !selectedSessionId}
              className="hcn-btn-primary"
              style={{ padding: '10px 20px', gap: 8, display: 'flex', alignItems: 'center', minWidth: 120, justifyContent: 'center' }}
            >
              <Send size={16} />
              {sendingReply ? 'جاري الإرسال...' : 'إرسال رد'}
            </button>
          </div>

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


        </div>
      </div>
    </div>
  );
}
