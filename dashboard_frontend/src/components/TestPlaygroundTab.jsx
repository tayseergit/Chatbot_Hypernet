import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, FlaskConical, Bot, User, CheckCircle2 } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function TestPlaygroundTab() {
  const [inputPrompt, setInputPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'مرحباً بك في بيئة الاختبار. يمكنك إدخال أي استفسار أو أمر لتجربة استجابة البوت وقاعدة المعرفة والخدمات التلقائية.',
      time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSend = async () => {
    if (!inputPrompt.trim() || isProcessing) return;

    const userPrompt = inputPrompt.trim();
    const nowTime = new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' });
    
    setMessages(prev => [...prev, {
      sender: 'user',
      text: userPrompt,
      time: nowTime,
    }]);
    setInputPrompt('');
    setIsProcessing(true);

    try {
      const res = await fetch(`${API}/api/chat/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'playground_admin_session',
          customer_id: 'HYP-64253',
          prompt: userPrompt
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: data.response || 'تم استلام الطلب ومعالجته.',
          time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
        }]);
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      console.error('Error contacting chat interact API:', err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'تعذر الاتصال بالخادم لمعالجة الرسالة. يرجى التحقق من اتصال الخدمة.',
        time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    setMessages([
      {
        sender: 'bot',
        text: 'تمت إعادة ضبط جلسة الاختبار. يمكنك البدء بإرسال الرسائل الآن.',
        time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
      }
    ]);
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
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
            <span>اختبار مباشر لنموذج الذكاء الاصطناعي وخدمات المشتركين وقاعدة المعرفة</span>
          </div>
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
                <p style={{ margin: 0, whiteSpace: 'pre-line', fontSize: 14, lineHeight: 1.6 }}>
                  {msg.text}
                </p>
                <span style={{ display: 'block', fontSize: 11, marginTop: 6, opacity: 0.7, textAlign: msg.sender === 'user' ? 'left' : 'right' }}>
                  {msg.time}
                </span>
              </div>
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
            onChange={(e) => setInputPrompt(e.target.value)}
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
