import React, { useState } from 'react';
import { MessageSquare, Search, Eye, User, Cpu } from 'lucide-react';

const SESSIONS = [
  {
    id: 'sess-101', customer: 'C001 - Ahmed Mohamed', phone: '+964 770 123 4567',
    intent: 'check_balance', confidence: '98%', time: '10:29 ص', authenticated: true,
    plan: 'Gold 50Mbps Fiber', lastMessage: 'مرحبا، أريد الاستفسار عن رصيد حسابي C001',
    agentDecision: 'النية: check_balance — أداة get_balance تم تنفيذها — الرصيد 125,000 د.ع.',
    chatHistory: [
      { sender: 'user', text: 'مرحبا، أريد الاستفسار عن رصيد حسابي C001', time: '10:29 ص' },
      { sender: 'bot',  text: 'أهلاً بك Ahmed Mohamed! رصيد حسابك الحالي: 125,000 دينار عراقي. الاشتراك ساري حتى 2026-09-01.', time: '10:29 ص', toolUsed: 'get_balance' },
    ],
  },
  {
    id: 'sess-102', customer: 'C002 - Fatima Ali', phone: '+964 770 987 6543',
    intent: 'troubleshoot_slow_speed', confidence: '94%', time: '10:15 ص', authenticated: true,
    plan: 'Silver 25Mbps Fiber', lastMessage: 'مرحبا، الإنترنت بطيء جداً اليوم',
    agentDecision: 'النية: troubleshoot_slow_speed — RAG تطابق KB-01 — إرشادات إعادة تشغيل الراوتر.',
    chatHistory: [
      { sender: 'user', text: 'مرحبا، الإنترنت بطيء جداً اليوم', time: '10:15 ص' },
      { sender: 'bot',  text: 'أهلاً Fatima! حاولي إعادة تشغيل الراوتر وإيقاف تشغيله لمدة 30 ثانية لتحديث الاتصال. إذا استمرت المشكلة سنرفع لك تذكرة دعم فني.', time: '10:15 ص', toolUsed: 'rag_service' },
    ],
  },
  {
    id: 'sess-103', customer: 'مستخدم غير مسجّل', phone: 'غير محدد',
    intent: 'check_package', confidence: '91%', time: '09:45 ص', authenticated: false,
    plan: 'غير مشترك', lastMessage: 'ما هي الباقات المتاحة وأسعارها؟',
    agentDecision: 'النية: check_package — RAG تطابق KB-02 — قائمة الباقات والأسعار.',
    chatHistory: [
      { sender: 'user', text: 'ما هي الباقات المتاحة وأسعارها؟', time: '09:45 ص' },
      { sender: 'bot',  text: 'أهلاً! لدينا الباقات التالية:\n1. ذهبية 50Mbps — 45,000 د.ع/شهر\n2. فضية 25Mbps — 30,000 د.ع/شهر\n3. برونزية 10Mbps — 20,000 د.ع/شهر', time: '09:45 ص', toolUsed: 'rag_service' },
    ],
  },
];

export default function SessionsChatTab() {
  const [selectedSessionId, setSelectedSessionId] = useState('sess-101');
  const [searchTerm, setSearchTerm]               = useState('');
  const [filterAuth, setFilterAuth]               = useState('ALL');

  const activeSession = SESSIONS.find(s => s.id === selectedSessionId) || SESSIONS[0];

  const filteredSessions = SESSIONS.filter(s => {
    const matchSearch =
      s.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.intent.toLowerCase().includes(searchTerm.toLowerCase());
    const matchAuth = filterAuth === 'ALL' ||
      (filterAuth === 'AUTH' && s.authenticated) ||
      (filterAuth === 'GUEST' && !s.authenticated);
    return matchSearch && matchAuth;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, height: 'calc(100vh - 64px)' }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0, paddingBottom: 16 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            مراقبة المحادثات المباشرة
            <span className="hcn-badge hcn-badge-success">للقراءة فقط</span>
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>المحادثات المباشرة</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <span className="hcn-badge hcn-badge-info" style={{ padding: '8px 16px', fontSize: 13, gap: 6 }}>
            <Eye size={16} /> وضع المشرف
          </span>
          <span className="hcn-badge hcn-badge-success" style={{ padding: '8px 16px', fontSize: 13, gap: 6 }}>
            <span className="hcn-dot hcn-dot-green hcn-dot-pulse" /> 42 جلسة نشطة
          </span>
        </div>
      </div>

      {/* ── اللوحة المزدوجة ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24, flex: 1, minHeight: 0, overflow: 'hidden' }}>

        {/* قائمة الجلسات */}
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', padding: 24, overflow: 'hidden' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 16 }}>
            <div style={{ position: 'relative' }}>
              <Search size={20} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }} />
              <input
                type="text"
                placeholder="بحث في الجلسات..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="hcn-input"
                style={{ paddingRight: 44 }}
              />
            </div>
            <div className="hcn-pill-group" style={{ width: '100%', display: 'flex' }}>
              {[
                { key: 'ALL',   label: 'الكل' },
                { key: 'AUTH',  label: 'موثّق' },
                { key: 'GUEST', label: 'ضيف' },
              ].map((m) => (
                <button key={m.key} className={`hcn-pill ${filterAuth === m.key ? 'active-primary' : ''}`} onClick={() => setFilterAuth(m.key)} style={{ flex: 1 }}>
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12, paddingRight: 4 }}>
            {filteredSessions.map((sess) => {
              const isActive = sess.id === selectedSessionId;
              return (
                <div
                  key={sess.id}
                  onClick={() => setSelectedSessionId(sess.id)}
                  style={{
                    padding: '16px', borderRadius: 12,
                    border: `1px solid ${isActive ? 'var(--primary)' : 'var(--border)'}`,
                    background: isActive ? 'var(--primary-bg)' : 'var(--bg-paper)',
                    cursor: 'pointer', transition: 'all 0.2s',
                    boxShadow: isActive ? 'var(--shadow-card)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 14, color: isActive ? 'var(--primary)' : 'var(--text-primary)' }}>{sess.customer}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-disabled)', fontFamily: 'monospace' }}>{sess.time}</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, color: 'var(--info)', fontWeight: 700, fontFamily: 'monospace' }}>{sess.intent}</span>
                    <span className={`hcn-badge ${sess.authenticated ? 'hcn-badge-success' : 'hcn-badge-warning'}`} style={{ fontSize: 11 }}>
                      {sess.authenticated ? 'موثّق' : 'ضيف'}
                    </span>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: 0 }}>
                    "{sess.lastMessage}"
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* عرض المحادثة */}
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          {/* رأس المحادثة */}
          <div style={{ padding: '24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--info-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={24} color="var(--info)" />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontWeight: 700, fontSize: 16 }}>{activeSession.customer}</span>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>({activeSession.phone})</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>جلسة: <strong style={{ color: 'var(--info)', fontFamily: 'monospace' }}>{activeSession.id}</strong></span>
                  <span style={{ color: 'var(--text-disabled)' }}>•</span>
                  <span style={{ color: 'var(--text-secondary)' }}>النية: <strong style={{ color: 'var(--success)' }}>{activeSession.intent}</strong></span>
                  <span style={{ color: 'var(--text-disabled)' }}>•</span>
                  <span style={{ color: 'var(--text-secondary)' }}>الثقة: <strong style={{ color: '#8B5CF6' }}>{activeSession.confidence}</strong></span>
                </div>
              </div>
            </div>
            <span className={`hcn-badge ${activeSession.authenticated ? 'hcn-badge-success' : 'hcn-badge-warning'}`} style={{ padding: '8px 16px', fontSize: 13 }}>
              {activeSession.authenticated ? 'مستخدم موثّق' : 'ضيف (غير موثّق)'}
            </span>
          </div>

          {/* الرسائل */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
            {activeSession.chatHistory.map((msg, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: msg.sender === 'user' ? 'flex-start' : 'flex-end' }}>
                <div
                  className={msg.sender === 'user' ? 'hcn-bubble-user' : 'hcn-bubble-bot'}
                  style={{ maxWidth: '70%' }}
                >
                  {msg.sender === 'bot' && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, paddingBottom: 12, borderBottom: '1px dashed rgba(255,255,255,0.2)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: 13, opacity: 0.9 }}>
                        نظام الردود التلقائية
                      </div>
                      {msg.toolUsed && (
                        <span style={{ fontSize: 11, background: 'rgba(0,0,0,0.15)', color: '#fff', padding: '4px 8px', borderRadius: 6, fontFamily: 'monospace', fontWeight: 700 }}>
                          {msg.toolUsed}
                        </span>
                      )}
                    </div>
                  )}
                  <p style={{ margin: 0, whiteSpace: 'pre-line', fontSize: 14, lineHeight: 1.6 }}>{msg.text}</p>
                  <span style={{ display: 'block', fontSize: 11, marginTop: 8, opacity: 0.7, textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                    {msg.time}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* ذيل التتبع */}
          <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-neutral)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: 'rgba(139, 92, 246, 0.16)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Cpu size={16} color="#8B5CF6" />
                </div>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                  {activeSession.agentDecision}
                </span>
              </div>
              <span className="hcn-badge hcn-badge-success" style={{ fontSize: 11 }}>مسجّل</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
