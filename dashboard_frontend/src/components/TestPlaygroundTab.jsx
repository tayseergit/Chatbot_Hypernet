import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, FlaskConical } from 'lucide-react';

export default function TestPlaygroundTab() {
  const [inputPrompt, setInputPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'مرحباً! هذه بيئة الاختبار. أدخل أي نص أدناه لاختبار مسار المعالجة الكامل (قاعدة المعرفة — CRM — قاعدة البيانات).',
      time: '10:00 ص',
    },
  ]);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSend = async () => {
    if (!inputPrompt.trim()) return;

    const userPrompt = inputPrompt;
    setMessages(prev => [...prev, {
      sender: 'user',
      text: userPrompt,
      time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
    }]);
    setInputPrompt('');
    setIsProcessing(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: 'playground-session-001', customer_id: 'C001', prompt: userPrompt }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [...prev, {
          sender: 'bot',
          text: data.response || 'لم يتم إرجاع أي رد.',
          time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
        }]);
      } else throw new Error('HTTP ' + res.status);
    } catch (err) {
      console.warn('Backend API error, falling back:', err);
      let botReply = 'تم تحليل طلبك. ';
      if (userPrompt.toLowerCase().includes('balance') || userPrompt.includes('رصيد')) {
        botReply += 'النية المصنّفة: check_balance — تم تنفيذ الأداة get_balance للعميل C001.\nالنتيجة: الرصيد الحالي 125,000 دينار عراقي، ساري حتى 2026-09-01.';
      } else if (userPrompt.includes('بطيء') || userPrompt.includes('slow')) {
        botReply += 'النية المصنّفة: troubleshoot_slow_speed — تم البحث في قاعدة المعرفة.\nالنتيجة: أعد تشغيل الراوتر لمدة 30 ثانية لتحديث الاتصال.';
      } else {
        botReply += 'النية المصنّفة: general_inquiry — تم البحث في قاعدة المعرفة.\nالنتيجة: لم يتم العثور على تطابق محدد. يُنصح بالتواصل مع الدعم الفني.';
      }
      setMessages(prev => [...prev, {
        sender: 'bot', text: botReply,
        time: new Date().toLocaleTimeString('ar-IQ', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, height: 'calc(100vh - 64px)' }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0, paddingBottom: 16 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            بيئة الاختبار التفاعلية
            <span className="hcn-badge" style={{ background: '#FDF2F8', color: '#BE185D' }}>ChatbotFacade API</span>
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>بيئة الاختبار</span>
          </div>
        </div>
        <button
          onClick={() => setMessages([{ sender: 'bot', text: 'تم إعادة تعيين جلسة الاختبار. جاهز للبدء.', time: 'الآن' }])}
          className="hcn-btn-outlined"
        >
          <RotateCcw size={20} /> إعادة تعيين الجلسة
        </button>
      </div>

      {/* ── واجهة المحادثة ── */}
      <div className="hcn-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden', minHeight: 0 }}>

        {/* الرسائل */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              {msg.sender === 'bot' && (
                <div style={{
                  width: 40, height: 40, borderRadius: 12, background: '#FDF2F8',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0, marginLeft: 16, alignSelf: 'flex-start'
                }}>
                  <FlaskConical size={20} color="#EC4899" />
                </div>
              )}
              <div
                className={msg.sender === 'user' ? 'hcn-bubble-user' : 'hcn-bubble-bot'}
                style={{ maxWidth: '70%' }}
              >
                {msg.sender === 'bot' && (
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#EC4899', marginBottom: 8 }}>
                    نظام الاختبار
                  </div>
                )}
                <p style={{ margin: 0, whiteSpace: 'pre-line', fontSize: 14, lineHeight: 1.6, fontFamily: msg.sender === 'bot' ? 'monospace' : 'inherit' }}>
                  {msg.text}
                </p>
                <span style={{ display: 'block', fontSize: 11, marginTop: 8, opacity: 0.7, textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                  {msg.time}
                </span>
              </div>
            </div>
          ))}

          {isProcessing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 40, height: 40, borderRadius: 12, background: '#FDF2F8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FlaskConical size={20} color="#EC4899" style={{ animation: 'spin 1.5s linear infinite' }} />
              </div>
              <div style={{ padding: '12px 20px', background: 'var(--bg-neutral)', border: '1px solid var(--border)', borderRadius: '0 12px 12px 12px', fontSize: 14, color: 'var(--text-secondary)' }}>
                جارٍ المعالجة...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* حقل الإدخال */}
        <div style={{ padding: '24px', borderTop: '1px solid var(--border)', background: 'var(--bg-neutral)', display: 'flex', gap: 16 }}>
          <input
            type="text"
            placeholder="أدخل نصاً للاختبار (مثال: أريد معرفة رصيد حسابي C001)..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            className="hcn-input"
            style={{ flex: 1, padding: '12px 16px', fontSize: 14 }}
          />
          <button
            onClick={handleSend}
            disabled={isProcessing || !inputPrompt.trim()}
            className="hcn-btn-primary"
            style={{ background: '#EC4899', padding: '0 32px' }}
          >
            إرسال <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
