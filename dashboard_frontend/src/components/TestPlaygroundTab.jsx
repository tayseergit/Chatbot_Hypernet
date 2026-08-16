import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, FlaskConical, Bot, User, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const PLAYGROUND_MSGS_KEY     = 'hypernet_playground_messages';
const PLAYGROUND_DRAFT_KEY    = 'hypernet_playground_draft';
const PLAYGROUND_PENDING_KEY  = 'hypernet_playground_processing';

const DEFAULT_MSG = {
  sender: 'bot',
  text: 'مرحباً بك في بيئة الاختبار. يمكنك إدخال أي استفسار أو أمر لتجربة استجابة البوت وقاعدة المعرفة والخدمات التلقائية.',
  time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
};

// ─── Module-level: survives tab switches (component unmount/remount) ───────────
let _pendingPromise = null;         // The in-flight fetch promise
let _mountedSetters = null;         // Setters of the currently mounted instance

/** Append a message directly to localStorage (safe even when component is unmounted) */
function _appendToStorage(msg) {
  try {
    const raw = localStorage.getItem(PLAYGROUND_MSGS_KEY);
    const msgs = raw ? JSON.parse(raw) : [DEFAULT_MSG];
    msgs.push(msg);
    localStorage.setItem(PLAYGROUND_MSGS_KEY, JSON.stringify(msgs));
  } catch { /* quota */ }
}

export default function TestPlaygroundTab() {
  const { admin } = useAuth();
  const sessionId = `playground_admin_${admin?.username || 'session'}`;
  const [inputPrompt, setInputPrompt] = useState(
    () => localStorage.getItem(PLAYGROUND_DRAFT_KEY) || ''
  );
  const [isProcessing, setIsProcessing] = useState(
    () => localStorage.getItem(PLAYGROUND_PENDING_KEY) === '1'
  );
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(PLAYGROUND_MSGS_KEY);
      return saved ? JSON.parse(saved) : [DEFAULT_MSG];
    } catch {
      return [DEFAULT_MSG];
    }
  });
  const bottomRef = useRef(null);

  // Register this instance's setters so the module-level fetch can update UI
  useEffect(() => {
    _mountedSetters = { setMessages, setIsProcessing };

    // If there's an in-flight fetch from before the tab switch, attach to its result
    if (_pendingPromise && isProcessing) {
      _pendingPromise.then(() => {
        // localStorage was already updated by the fetch callback;
        // re-read it so the UI reflects the new message
        try {
          const raw = localStorage.getItem(PLAYGROUND_MSGS_KEY);
          const msgs = raw ? JSON.parse(raw) : [DEFAULT_MSG];
          setMessages(msgs);
        } catch { /* ignore */ }
        setIsProcessing(false);
        _pendingPromise = null;
      });
    }

    return () => {
      // Component is unmounting — clear setters so the pending fetch
      // won't try to call setState on the dead instance
      _mountedSetters = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(PLAYGROUND_MSGS_KEY, JSON.stringify(messages));
    } catch { /* quota */ }
  }, [messages]);

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Persist draft as user types
  const handleInputChange = (e) => {
    setInputPrompt(e.target.value);
    localStorage.setItem(PLAYGROUND_DRAFT_KEY, e.target.value);
  };

  const handleSend = () => {
    if (!inputPrompt.trim() || isProcessing) return;

    const userPrompt = inputPrompt.trim();
    const nowTime = new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' });

    // 1. Add user message to UI & localStorage immediately
    const userMsg = { sender: 'user', text: userPrompt, time: nowTime };
    setMessages(prev => [...prev, userMsg]);
    setInputPrompt('');
    localStorage.removeItem(PLAYGROUND_DRAFT_KEY);
    setIsProcessing(true);
    localStorage.setItem(PLAYGROUND_PENDING_KEY, '1');

    // 2. Fire the fetch at module level — will survive tab switches
    _pendingPromise = (async () => {
      let botMsg;
      try {
        const res = await fetch(`${API}/api/chat/interact`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            customer_id: 'HYP-64253',
            prompt: userPrompt,
          }),
        });
        const data = await res.json();
        botMsg = {
          sender: 'bot',
          text: data.response || 'تم استلام الطلب ومعالجته.',
          time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
        };
      } catch (err) {
        console.error('Playground API error:', err);
        botMsg = {
          sender: 'bot',
          text: 'تعذر الاتصال بالخادم لمعالجة الرسالة. يرجى التحقق من اتصال الخدمة.',
          time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
        };
      }

      // 3. Write to localStorage FIRST — so remount will find the message
      _appendToStorage(botMsg);
      localStorage.removeItem(PLAYGROUND_PENDING_KEY);

      // 4. Update UI only if the component is still/already mounted
      if (_mountedSetters) {
        _mountedSetters.setMessages(prev => [...prev, botMsg]);
        _mountedSetters.setIsProcessing(false);
      }

      _pendingPromise = null;
    })();
  };

  const handleReset = async () => {
    setMessages([DEFAULT_MSG]);
    localStorage.removeItem(PLAYGROUND_MSGS_KEY);
    localStorage.removeItem(PLAYGROUND_DRAFT_KEY);
    localStorage.removeItem(PLAYGROUND_PENDING_KEY);
    try {
      await fetch(`${API}/api/sessions/${sessionId}/reset`, { method: 'POST' });
    } catch (e) {
      console.error('Failed to reset session on backend', e);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, height: 'calc(100vh - 120px)', maxWidth: '100%' }}>

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
            بيئة الاختبار التفاعلية
          </h1>
        </div>

        <button
          onClick={handleReset}
          className="hcn-btn"
          style={{ gap: 8, fontSize: 13, height: 38, fontWeight: 600 }}
        >
          <RotateCcw size={15} />
          إعادة تعيين الجلسة
        </button>
      </div>

      {/* ── كارد المحادثة التفاعلية ── */}
      <div className="hcn-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden', minHeight: 0 }}>

        {/* قائمة الرسائل */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              {msg.sender === 'bot' && (
                <div style={{
                  width: 36, height: 36, borderRadius: 10, background: 'rgba(0, 167, 111, 0.12)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginLeft: 12, alignSelf: 'flex-start'
                }}>
                  <FlaskConical size={18} color="var(--primary)" />
                </div>
              )}
              <div
                className={msg.sender === 'user' ? 'hcn-bubble-user' : 'hcn-bubble-bot'}
                style={{
                  maxWidth: '75%',
                  background: msg.sender === 'user' ? 'var(--primary)' : 'var(--bg-paper)',
                  color: msg.sender === 'user' ? '#ffffff' : 'var(--text-primary)',
                  border: msg.sender === 'user' ? 'none' : '1px solid var(--border-color)',
                  borderRadius: 12,
                  padding: '14px 18px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                }}
              >
                {msg.sender === 'bot' && (
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)', marginBottom: 6 }}>
                    نظام المساعد الذكي
                  </div>
                )}
                {msg.sender === 'user' && (
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#ffffff', marginBottom: 6 }}>
                    أنت (مدير النظام)
                  </div>
                )}
                <p style={{ margin: 0, whiteSpace: 'pre-line', fontSize: 14, lineHeight: 1.6 }}>
                  {msg.text}
                </p>
                <span style={{ display: 'block', fontSize: 11, marginTop: 6, opacity: 0.7, textAlign: msg.sender === 'user' ? 'left' : 'right' }}>
                  {msg.time}
                </span>
              </div>
              {msg.sender === 'user' && (
                <div style={{
                  width: 36, height: 36, borderRadius: 10, background: 'rgba(79, 70, 229, 0.12)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginRight: 12, alignSelf: 'flex-start'
                }}>
                  <User size={18} color="#4F46E5" />
                </div>
              )}
            </div>
          ))}

          {isProcessing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(0, 167, 111, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FlaskConical size={18} color="var(--primary)" style={{ animation: 'spin 1.5s linear infinite' }} />
              </div>
              <div style={{ padding: '12px 18px', background: 'var(--bg-paper)', border: '1px solid var(--border-color)', borderRadius: 12, fontSize: 13, color: 'var(--text-secondary)' }}>
                جاري معالجة الطلب عبر المساعد الذكي...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* حقل الإدخال السفلي */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-color)', background: 'var(--bg-card)', display: 'flex', gap: 12, alignItems: 'center' }}>
          <input
            type="text"
            placeholder="اكتب استفسارك هنا لاختبار استجابة النظام..."
            value={inputPrompt}
            onChange={handleInputChange}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="hcn-input"
            style={{ flex: 1, height: 42, fontSize: 13 }}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing || !inputPrompt.trim()}
            className="hcn-btn-primary"
            style={{ height: 42, padding: '0 24px', fontSize: 13, fontWeight: 600, gap: 8 }}
          >
            إرسال <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
