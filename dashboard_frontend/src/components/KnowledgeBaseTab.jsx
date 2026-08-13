import React, { useState } from 'react';
import { BookOpen, Search, UploadCloud, Cpu, Database } from 'lucide-react';

const KB_CATEGORIES = [
  {
    tag: 'الشبكة والراوتر', tagColor: 'var(--info)', tagBg: 'var(--info-bg)',
    count: 14, title: 'استكشاف أخطاء WiFi والراوتر',
    desc: 'إرشادات إعادة تشغيل الراوتر، إعداد WiFi، واستكشاف مشاكل السرعة.',
  },
  {
    tag: 'الباقات والأسعار', tagColor: 'var(--success)', tagBg: 'var(--success-bg)',
    count: 8, title: 'خطط الإنترنت والاشتراكات',
    desc: 'أسعار باقات الألياف والواير لس، السرعات، حدود البيانات، وشروط التجديد.',
  },
  {
    tag: 'الدعم والفواتير', tagColor: 'var(--warning)', tagBg: 'var(--warning-bg)',
    count: 12, title: 'الدعم الفني والمدفوعات',
    desc: 'بوابات الدفع، خطوات رفع تذاكر الدعم، ومواعيد زيارات الفنيين.',
  },
];

export default function KnowledgeBaseTab() {
  const [query, setQuery]             = useState('');
  const [searchResult, setSearchResult] = useState(null);

  const handleSearch = () => {
    if (!query.trim()) return;
    setSearchResult({
      query,
      matchedSnippet: 'KB-01: إجراء إعادة تشغيل الراوتر',
      similarity: 0.96,
      contextText: 'افصل كابل الطاقة عن الراوتر لمدة 30 ثانية لتحديث الاتصال بالبوابة الرئيسية...',
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 0 }}>
        <div>
           <h1 className="hcn-title" style={{ marginBottom: 8 }}>قاعدة المعرفة</h1>
           <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>قاعدة المعرفة RAG</span>
          </div>
        </div>
        <button
          onClick={() => alert('تم إعادة فهرسة قاعدة المعرفة بنجاح!')}
          className="hcn-btn-primary"
          style={{ background: '#8B5CF6' }}
        >
          <UploadCloud size={20} /> إعادة الفهرسة
        </button>
      </div>

      {/* ── إحصائيات ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
        {[
          { label: 'إجمالي المستندات', value: '34',    icon: Database, iconColor: '#8B5CF6', iconBg: 'rgba(139, 92, 246, 0.16)' },
          { label: 'أبعاد المتجه',      value: '4,096', icon: Cpu,      iconColor: 'var(--info)', iconBg: 'var(--info-bg)' },
          { label: 'متوسط التطابق',     value: '0.91',  icon: Search,   iconColor: 'var(--success)', iconBg: 'var(--success-bg)' },
          { label: 'عمليات بحث/يوم',    value: '4,120', icon: BookOpen, iconColor: 'var(--warning)', iconBg: 'var(--warning-bg)' },
        ].map((s) => (
          <div key={s.label} className="hcn-card" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '24px' }}>
             <div style={{ width: 64, height: 64, borderRadius: '50%', background: s.iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
               <s.icon size={32} color={s.iconColor} />
             </div>
             <div>
                <div className="hcn-stat-label" style={{ marginBottom: 8 }}>{s.label}</div>
                <div className="hcn-stat-value">{s.value}</div>
             </div>
          </div>
        ))}
      </div>

      {/* ── اختبار البحث المتجه ── */}
      <div className="hcn-card" style={{ padding: 32 }}>
         <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(139, 92, 246, 0.16)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Search size={24} color="#8B5CF6" />
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>اختبار بحث المتجهات</h2>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, marginBottom: searchResult ? 24 : 0 }}>
          <input
            type="text"
            placeholder="أدخل نصاً للبحث (مثال: كيف أعيد تشغيل الراوتر؟)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="hcn-input"
            style={{ flex: 1, padding: '12px 16px', fontSize: 14 }}
          />
          <button
            onClick={handleSearch}
            className="hcn-btn-primary"
            style={{ background: '#8B5CF6', padding: '0 32px' }}
          >
            <Cpu size={20} /> بحث
          </button>
        </div>

        {searchResult && (
          <div className="animate-fade-in" style={{ padding: '24px', background: 'var(--bg-neutral)', border: '1px solid var(--border)', borderRadius: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <span style={{ fontWeight: 700, color: '#8B5CF6', fontSize: 14 }}>نتيجة التطابق</span>
              <span className="hcn-badge hcn-badge-success" style={{ fontSize: 13, padding: '6px 12px' }}>
                درجة التشابه: {searchResult.similarity}
              </span>
            </div>
            <div style={{ fontSize: 14, marginBottom: 12 }}>
              <strong style={{ color: 'var(--text-primary)' }}>المستند المطابق:</strong>{' '}
              <code style={{ background: 'var(--bg-paper)', border: '1px solid var(--border)', padding: '4px 8px', borderRadius: 6, color: '#8B5CF6', fontWeight: 700 }}>
                {searchResult.matchedSnippet}
              </code>
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: 1.6, padding: '16px', background: 'var(--bg-paper)', borderRadius: 8, border: '1px dashed var(--border)' }}>
              "{searchResult.contextText}"
            </div>
          </div>
        )}
      </div>

      {/* ── بطاقات الفئات ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
        {KB_CATEGORIES.map((cat) => (
          <div key={cat.tag} className="hcn-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <span className="hcn-badge" style={{ background: cat.tagBg, color: cat.tagColor, fontSize: 12, padding: '4px 10px' }}>
                {cat.tag}
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontFamily: 'monospace', fontWeight: 700 }}>
                {cat.count} مقطع
              </span>
            </div>
            <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)', marginBottom: 8 }}>{cat.title}</div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{cat.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
