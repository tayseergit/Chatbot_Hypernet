import React, { useState } from 'react';
import { Settings, Database, Save, CheckCircle2, Server } from 'lucide-react';

export default function SettingsTab() {
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [model, setModel]         = useState('llama3');
  const [dbHost, setDbHost]       = useState('localhost:3306');
  const [dbName, setDbName]       = useState('isp_chatbot');
  const [saved, setSaved]         = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32, maxWidth: 960, margin: '0 auto', width: '100%' }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12 }}>
            إعدادات النظام
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>الإعدادات</span>
          </div>
        </div>
        <button onClick={handleSave} className="hcn-btn-primary">
          {saved ? <CheckCircle2 size={20} /> : <Save size={20} />}
          {saved ? 'تم الحفظ!' : 'حفظ التغييرات'}
        </button>
      </div>

      {saved && (
        <div className="animate-slide-in" style={{ padding: '16px 24px', borderRadius: 12, background: 'var(--success-bg)', color: 'var(--success)', border: '1px solid rgba(0, 171, 85, 0.2)', fontWeight: 700, fontSize: 14 }}>
          تم حفظ الإعدادات بنجاح
        </div>
      )}

      {/* ── إعدادات النموذج ── */}
      <div className="hcn-card" style={{ padding: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, paddingBottom: 24, borderBottom: '1px solid var(--border)' }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(139, 92, 246, 0.16)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Server size={24} color="#8B5CF6" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--text-primary)', marginBottom: 4 }}>إعدادات النموذج اللغوي</div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>عنوان Ollama والنموذج المستخدم</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              عنوان Ollama
            </label>
            <input type="text" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} className="hcn-input font-mono-data" style={{ padding: '12px 16px', fontSize: 14 }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              النموذج المختار
            </label>
            <select value={model} onChange={(e) => setModel(e.target.value)} className="hcn-input font-mono-data" style={{ padding: '12px 16px', fontSize: 14 }}>
              <option value="llama3">llama3:latest</option>
              <option value="mistral">mistral:7b</option>
              <option value="qwen">qwen2:7b</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 24, padding: '16px 20px', borderRadius: 12, background: 'var(--success-bg)', border: '1px solid rgba(0, 171, 85, 0.2)' }}>
          <span className="hcn-dot hcn-dot-green hcn-dot-pulse" />
          <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--success)' }}>النموذج اللغوي — متصل ويستجيب</span>
        </div>
      </div>

      {/* ── إعدادات قاعدة البيانات ── */}
      <div className="hcn-card" style={{ padding: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24, paddingBottom: 24, borderBottom: '1px solid var(--border)' }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--success-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Database size={24} color="var(--success)" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--text-primary)', marginBottom: 4 }}>قاعدة البيانات وسجل العمليات</div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>إعدادات الاتصال وخيارات التسجيل</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24 }}>
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>اسم قاعدة البيانات</label>
            <input type="text" value={dbName} onChange={(e) => setDbName(e.target.value)} className="hcn-input font-mono-data" style={{ padding: '12px 16px', fontSize: 14 }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>عنوان الخادم</label>
            <input type="text" value={dbHost} onChange={(e) => setDbHost(e.target.value)} className="hcn-input font-mono-data" style={{ padding: '12px 16px', fontSize: 14 }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>سجل العمليات</label>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(0, 171, 85, 0.2)', background: 'var(--success-bg)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--success)', fontWeight: 700, fontSize: 14 }}>
                <CheckCircle2 size={16} /> مفعّل
              </span>
              <code style={{ fontSize: 12, color: 'var(--text-secondary)', background: 'var(--bg-paper)', border: '1px solid var(--border)', padding: '4px 8px', borderRadius: 6, fontWeight: 700 }}>
                agent_action_logs
              </code>
            </div>
          </div>
        </div>
      </div>

      {/* ── معلومات النظام ── */}
      <div className="hcn-card" style={{ padding: 32 }}>
        <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 24, color: 'var(--text-primary)' }}>معلومات النظام</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { label: 'إطار الخادم',    value: 'FastAPI 0.110+' },
            { label: 'النموذج اللغوي', value: 'Ollama (محلي)' },
            { label: 'قاعدة المعرفة',  value: 'ChromaDB (RAG)' },
            { label: 'الواجهة الأمامية', value: 'React + Vite' },
            { label: 'قاعدة البيانات', value: 'SQLite / MySQL' },
            { label: 'الإصدار',        value: 'v2.0 — إنتاج' },
          ].map((item) => (
            <div key={item.label} style={{ padding: '16px 20px', background: 'var(--bg-neutral)', borderRadius: 12, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {item.label}
              </div>
              <div style={{ fontWeight: 700, fontSize: 14, fontFamily: 'monospace', color: 'var(--text-primary)' }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
