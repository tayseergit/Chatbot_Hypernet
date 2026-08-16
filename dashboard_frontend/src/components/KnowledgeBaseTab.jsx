import React, { useState, useEffect } from 'react';
import {
  BookOpen, Search, UploadCloud, RefreshCw, Plus, Trash2, Edit3,
  Download, FileText, Phone, Wifi, Tv, DollarSign, X, AlertCircle,
  Save, CheckCircle2, Loader2, Filter, Layers, Check
} from 'lucide-react';
import { usePasswordAuth, PasswordPromptModal } from './PasswordPromptModal';
import ConfirmModal from './ConfirmModal';
import { useAuth } from '../context/AuthContext';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORY_MAP = {
  ALL: 'كافة الأقسام',
  dsl_router: 'إعدادات الراوتر والشبكة',
  dsl_speed_change: 'السرعات والباقات الشهرية',
  dsl_troubleshooting: 'الدعم الفني والأعطال',
  billing: 'الفواتير والاشتراكات',
  services: 'الخدمات المضافة',
  iptv_service: 'خدمة البث الرقمي IPTV',
  static_ip: 'العناوين الثابتة Static IP',
  wireless_packages: 'الإنترنت اللاسلكي',
  contacts: 'أقسام ووسائل التواصل',
  general: 'استفسارات عامة'
};

export default function KnowledgeBaseTab() {
  const [activeSubTab, setActiveSubTab] = useState('qa');

  // Global Stats
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [reindexing, setReindexing] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);
  const [confirmAction, setConfirmAction] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

  // 1. Q&A State
  const [qaList, setQaList] = useState([]);
  const [qaLoading, setQaLoading] = useState(false);
  const [qaSearch, setQaSearch] = useState('');
  const [qaCategory, setQaCategory] = useState('ALL');
  const [qaPage, setQaPage] = useState(1);
  const qaPerPage = 10;

  // Modal State (Add / Edit Q&A)
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [editIndex, setEditIndex] = useState(null);
  const [formData, setFormData] = useState({ category: 'general', question: '', answer: '' });
  const [savingQa, setSavingQa] = useState(false);

  // 2. Company Info State
  const [companyData, setCompanyData] = useState(null);
  const [companyLoading, setCompanyLoading] = useState(false);
  const [savingCompany, setSavingCompany] = useState(false);
  const [companySubTab, setCompanySubTab] = useState('adsl_monthly');

  // 3. PDF Guides State
  const [pdfList, setPdfList] = useState([]);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [uploadingPdf, setUploadingPdf] = useState(false);

  // 4. Semantic Search Tester State

  const { requireAuth, modalProps } = usePasswordAuth();
  const { hasPermission } = useAuth();
  const canEdit = hasPermission('edit_knowledge_base');

  const showToast = (type, text) => {
    setToastMsg({ type, text });
    setTimeout(() => setToastMsg(null), 3500);
  };

  // Fetch Stats
  const fetchStats = () => {
    fetch(`${API}/api/rag/stats`)
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setStatsLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch RAG stats:', err);
        setStatsLoading(false);
      });
  };

  // Fetch Q&A items
  const fetchQA = () => {
    setQaLoading(true);
    const params = new URLSearchParams();
    if (qaSearch) params.append('search', qaSearch);
    if (qaCategory && qaCategory !== 'ALL') params.append('category', qaCategory);

    fetch(`${API}/api/rag/qa?${params.toString()}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setQaList(data.items || []);
        setQaLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch QA items:', err);
        setQaLoading(false);
      });
  };

  // Fetch Company Info
  const fetchCompanyInfo = () => {
    setCompanyLoading(true);
    fetch(`${API}/api/rag/company-info`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setCompanyData(data || {});
        setCompanyLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch company info:', err);
        setCompanyLoading(false);
      });
  };

  // Fetch PDF list
  const fetchPDFs = () => {
    setPdfLoading(true);
    fetch(`${API}/api/rag/pdfs`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setPdfList(data || []);
        setPdfLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch PDFs:', err);
        setPdfLoading(false);
      });
  };

  useEffect(() => {
    fetchStats();
    fetchQA();
    fetchCompanyInfo();
    fetchPDFs();
  }, []);

  useEffect(() => {
    fetchQA();
    setQaPage(1);
  }, [qaSearch, qaCategory]);

  // Re-index all sources
  const handleReindex = async () => {
    setReindexing(true);
    try {
      const res = await fetch(`${API}/api/rag/reindex`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      showToast('success', 'تمت مزامنة البيانات وتحديث قاعدة المعرفة بنجاح');
      fetchStats();
      fetchQA();
      fetchPDFs();
    } catch (e) {
      showToast('error', `تعذرت المزامنة: ${e.message}`);
    } finally {
      setReindexing(false);
    }
  };

  // Save / Update Q&A
  const handleSaveQA = (e) => {
    e.preventDefault();
    if (!formData.question.trim() || !formData.answer.trim()) {
      showToast('error', 'يرجى إدخال السؤال والإجابة المعتمدة');
      return;
    }
    requireAuth(modalMode === 'add' ? 'إضافة سؤال جديد' : 'تعديل السؤال المحدد', async () => {
      setSavingQa(true);
      try {
        const url = modalMode === 'add' ? `${API}/api/rag/qa` : `${API}/api/rag/qa/${editIndex}`;
        const method = modalMode === 'add' ? 'POST' : 'PUT';
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showToast('success', modalMode === 'add' ? 'تمت إضافة السؤال بنجاح' : 'تم تعديل السؤال بنجاح');
        setModalOpen(false);
        fetchQA();
        fetchStats();
      } catch (e) {
        showToast('error', `تعذر الحفظ: ${e.message}`);
      } finally {
        setSavingQa(false);
      }
    });
  };

  // Delete Q&A
  const handleDeleteQA = (id) => {
    setConfirmAction({
      isOpen: true,
      title: 'تأكيد الحذف',
      message: 'هل ترغب في تأكيد حذف هذا السجل؟',
      onConfirm: async () => {
        setConfirmAction({ isOpen: false });
        requireAuth('حذف سؤال من قاعدة المعرفة', async () => {
          try {
            const res = await fetch(`${API}/api/rag/qa/${id}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            showToast('success', 'تم حذف السجل بنجاح');
            fetchQA();
            fetchStats();
          } catch (e) {
            showToast('error', `تعذر الحذف: ${e.message}`);
          }
        });
      }
    });
  };

  // Save Company Info Changes
  const handleSaveCompany = () => {
    // Basic validation: ensure no empty fields
    for (const [key, value] of Object.entries(companyData)) {
      if (Array.isArray(value)) {
        for (const item of value) {
          for (const val of Object.values(item)) {
            if (val === undefined || val === null || String(val).trim() === '') {
              showToast('error', 'يرجى تعبئة جميع الحقول أو حذف الأسطر الفارغة قبل الحفظ');
              return;
            }
          }
        }
      }
    }

    requireAuth('حفظ تعديلات الباقات والخدمات الرسمية', async () => {
      setSavingCompany(true);
      try {
        const res = await fetch(`${API}/api/rag/company-info`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(companyData)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showToast('success', 'تم حفظ التغييرات بنجاح');
        fetchStats();
      } catch (e) {
        showToast('error', `تعذر حفظ البيانات: ${e.message}`);
      } finally {
        setSavingCompany(false);
      }
    });
  };

  // Upload PDF Guide
  const handlePdfUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast('error', 'يرجى اختيار ملف بصيغة PDF');
      return;
    }
    requireAuth(`رفع ملف ${file.name}`, async () => {
      const data = new FormData();
      data.append('file', file);
      setUploadingPdf(true);
      try {
        const res = await fetch(`${API}/api/rag/pdfs/upload`, {
          method: 'POST',
          body: data
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showToast('success', `تم رفع الدليل ${file.name} بنجاح`);
        fetchPDFs();
        fetchStats();
      } catch (e) {
        showToast('error', `تعذر رفع الملف: ${e.message}`);
      } finally {
        setUploadingPdf(false);
        e.target.value = null;
      }
    });
  };

  // Delete PDF
  const handleDeletePdf = (filename) => {
    setConfirmAction({
      isOpen: true,
      title: 'تأكيد الحذف',
      message: `هل ترغب في تأكيد حذف الملف "${filename}"؟`,
      onConfirm: async () => {
        setConfirmAction({ isOpen: false });
        requireAuth(`حذف ملف ${filename}`, async () => {
          try {
            const res = await fetch(`${API}/api/rag/pdfs/${encodeURIComponent(filename)}`, {
              method: 'DELETE'
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            showToast('success', 'تم حذف الملف بنجاح');
            fetchPDFs();
            fetchStats();
          } catch (e) {
            showToast('error', `تعذر الحذف: ${e.message}`);
          }
        });
      }
    });
  };

  // Semantic Tester
  

  const paginatedQa = qaList.slice((qaPage - 1) * qaPerPage, qaPage * qaPerPage);
  const totalPages = Math.ceil(qaList.length / qaPerPage) || 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: '100%', overflow: 'hidden' }}>

      <PasswordPromptModal {...modalProps} />

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
            قاعدة المعرفة
          </h1>
        </div>

        <button type="button"
          onClick={handleReindex}
          disabled={reindexing}
          className="hcn-btn-primary"
          style={{ gap: 8, padding: '9px 18px', fontSize: 13, fontWeight: 600 }}
        >
          {reindexing ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {reindexing ? 'جاري المزامنة...' : 'مزامنة وتحديث البيانات'}
        </button>
      </div>

      {toastMsg && (
        <div style={{
          padding: '11px 16px',
          borderRadius: 'var(--radius-md)',
          background: toastMsg.type === 'success' ? 'var(--success-bg)' : 'var(--error-bg)',
          color: toastMsg.type === 'success' ? 'var(--success)' : 'var(--error)',
          fontWeight: 600,
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          border: `1px solid ${toastMsg.type === 'success' ? 'rgba(34,197,94,0.25)' : 'rgba(255,86,48,0.25)'}`
        }}>
          {toastMsg.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {toastMsg.text}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 14 }}>
        <div className="hcn-card" style={{ padding: '16px 20px', borderRight: '4px solid var(--primary)' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>بنك الأسئلة الشائعة</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
            {stats?.sources?.qa ?? qaList.length ?? 0} سؤالاً
          </div>
        </div>

        <div className="hcn-card" style={{ padding: '16px 20px', borderRight: '4px solid #10B981' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>الباقات والخدمات</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
            {stats?.sources?.company_info ?? 0} باقة وخدمة
          </div>
        </div>

        <div className="hcn-card" style={{ padding: '16px 20px', borderRight: '4px solid #06B6D4' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>الأدلة والكتيبات الفنية</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
            {stats?.pdf_count ?? pdfList.length ?? 0} أدلة PDF
          </div>
        </div>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        padding: '6px',
        flexWrap: 'wrap'
      }}>
        {[
          { key: 'qa', label: `بنك الأسئلة (${qaList.length})`, icon: BookOpen },
          { key: 'company', label: 'الباقات والخدمات الرسمية', icon: DollarSign },
          { key: 'pdfs', label: `الأدلة والكتيبات الفنية (${pdfList.length})`, icon: FileText },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.key;
          return (
            <button type="button"
              key={tab.key}
              onClick={() => setActiveSubTab(tab.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
                transition: 'all 0.15s ease',
                background: isActive ? 'var(--primary)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)'
              }}
            >
              <Icon size={15} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeSubTab === 'qa' && (
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', gap: 10, flex: 1, minWidth: 280 }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={16} style={{ position: 'absolute', right: 12, top: 11, color: 'var(--text-disabled)' }} />
                <input
                  type="text"
                  placeholder="البحث في الأسئلة أو الإجابات..."
                  value={qaSearch}
                  onChange={(e) => setQaSearch(e.target.value)}
                  className="hcn-input"
                  style={{ paddingRight: 36, paddingLeft: 12, paddingTop: 4, paddingBottom: 4, width: '100%', height: 38, fontSize: 13 }}
                />
              </div>

              <select
                value={qaCategory}
                onChange={(e) => setQaCategory(e.target.value)}
                className="hcn-input"
                style={{ width: 210, height: 38, fontSize: 13, padding: '4px 12px' }}
              >
                {Object.entries(CATEGORY_MAP).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            {canEdit && (
              <button type="button"
                onClick={() => {
                  setModalMode('add');
                  setFormData({ category: 'general', question: '', answer: '' });
                  setModalOpen(true);
                }}
                className="hcn-btn-primary"
                style={{ gap: 6, height: 38, fontSize: 13, fontWeight: 600 }}
              >
                <Plus size={16} />
                إضافة سؤال جديد
              </button>
            )}
          </div>

          <div className="hcn-table-wrapper" style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
            <table className="hcn-table" style={{ width: '100%', tableLayout: 'fixed' }}>
              <thead>
                <tr>
                  <th style={{ width: '5%', textAlign: 'center' }}>#</th>
                  <th style={{ width: '18%' }}>القسم</th>
                  <th style={{ width: '32%' }}>السؤال</th>
                  <th style={{ width: '35%' }}>الإجابة المعتمدة</th>
                  {canEdit && <th style={{ width: '10%', textAlign: 'center' }}>الإجراءات</th>}
                </tr>
              </thead>
              <tbody>
                {qaLoading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: 40 }}>
                      <Loader2 className="animate-spin" size={24} style={{ margin: '0 auto', color: 'var(--primary)' }} />
                    </td>
                  </tr>
                ) : paginatedQa.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: 40, color: 'var(--text-disabled)', fontSize: 13 }}>
                      لا توجد نتائج مطابقة لمعايير البحث.
                    </td>
                  </tr>
                ) : (
                  paginatedQa.map((item) => (
                    <tr key={item.id}>
                      <td style={{ textAlign: 'center', color: 'var(--text-disabled)', fontFamily: 'monospace', fontSize: 12 }}>
                        {item.id + 1}
                      </td>
                      <td>
                        <span className="hcn-badge" style={{ background: 'rgba(99,102,241,0.12)', color: 'var(--primary)', fontSize: 11, whiteSpace: 'nowrap' }}>
                          {CATEGORY_MAP[item.category] || item.category}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 13, wordBreak: 'break-word' }}>
                        {item.question}
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.5, wordBreak: 'break-word' }}>
                        {item.answer}
                      </td>
                      {canEdit && (
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'inline-flex', gap: 4 }}>
                            <button type="button"
                              onClick={() => {
                                setModalMode('edit');
                                setEditIndex(item.id);
                                setFormData({ category: item.category, question: item.question, answer: item.answer });
                                setModalOpen(true);
                              }}
                              className="hcn-btn-ghost"
                              style={{ padding: 6, color: 'var(--primary)' }}
                              title="تعديل"
                            >
                              <Edit3 size={15} />
                            </button>
                            <button type="button"
                              onClick={() => handleDeleteQA(item.id)}
                              className="hcn-btn-ghost"
                              style={{ padding: 6, color: 'var(--error)' }}
                              title="حذف"
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: 'var(--text-secondary)' }}>
            <div>عرض {paginatedQa.length} من إجمالي {qaList.length} سجل</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <button type="button"
                disabled={qaPage <= 1}
                onClick={() => setQaPage(p => p - 1)}
                className="hcn-btn-outlined"
                style={{ padding: '4px 12px', fontSize: 12 }}
              >
                السابق
              </button>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)', padding: '0 6px' }}>{qaPage} / {totalPages}</span>
              <button type="button"
                disabled={qaPage >= totalPages}
                onClick={() => setQaPage(p => p + 1)}
                className="hcn-btn-outlined"
                style={{ padding: '4px 12px', fontSize: 12 }}
              >
                التالي
              </button>
            </div>
          </div>
        </div>
      )}

      {activeSubTab === 'company' && (
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, borderBottom: '1px solid var(--border-color)', paddingBottom: 12 }}>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {[
                { key: 'adsl_monthly', label: 'باقات ADSL الشهرية', icon: Wifi },
                { key: 'adsl_topup', label: 'باقات الشحن ADSL', icon: Plus },
                { key: 'wifi_outdoor_monthly', label: 'باقات WIFI', icon: Wifi },
                { key: 'wifi_outdoor_topup', label: 'شحن WIFI', icon: Plus },
                { key: 'services', label: 'الخدمات والرسوم', icon: RefreshCw },
                { key: 'iptv_packages', label: 'باقات IPTV', icon: Tv },
                { key: 'contacts', label: 'بيانات التواصل', icon: Phone },
              ].map(sub => {
                const Icon = sub.icon;
                const isSubActive = companySubTab === sub.key;
                return (
                  <button type="button"
                    key={sub.key}
                    onClick={() => setCompanySubTab(sub.key)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      padding: '6px 14px',
                      borderRadius: 'var(--radius-sm)',
                      border: isSubActive ? '1px solid var(--primary)' : '1px solid var(--border-color)',
                      background: isSubActive ? 'rgba(99,102,241,0.12)' : 'var(--bg-paper)',
                      color: isSubActive ? 'var(--primary)' : 'var(--text-secondary)',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    <Icon size={14} />
                    {sub.label}
                  </button>
                );
              })}
            </div>

            {canEdit && (
              <button type="button"
                onClick={handleSaveCompany}
                disabled={savingCompany}
                className="hcn-btn-primary"
                style={{ gap: 6, background: '#10B981', height: 36, fontSize: 13, fontWeight: 600 }}
              >
                {savingCompany ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                {savingCompany ? 'جاري الحفظ...' : 'حفظ التغييرات'}
              </button>
            )}
          </div>

          {companyLoading ? (
            <div style={{ textAlign: 'center', padding: 30 }}><Loader2 className="animate-spin" size={24} style={{ color: 'var(--primary)' }} /></div>
          ) : !companyData ? (
            <div style={{ textAlign: 'center', padding: 30, color: 'var(--text-disabled)' }}>لا توجد بيانات متاحة.</div>
          ) : (
            <div>
              {companySubTab === 'adsl_monthly' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>باقات ADSL الشهرية</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.adsl_monthly = [...(next.adsl_monthly || []), { speed: '', quota: '', price: '', speed_after_quota: '' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة باقة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>السرعة</th>
                          <th>حجم الباقة</th>
                          <th>السعر (ل.س)</th>
                          <th>السرعة بعد استهلاك الحجم</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.adsl_monthly || []).map((pkg, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.speed}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_monthly[idx].speed = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.quota}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_monthly[idx].quota = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.price}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_monthly[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.speed_after_quota}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_monthly[idx].speed_after_quota = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.adsl_monthly.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'wifi_outdoor_monthly' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>باقات WIFI Outdoor الشهرية</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.wifi_outdoor_monthly = [...(next.wifi_outdoor_monthly || []), { package: '', speed: '', quota: '', price: '', type: '' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة باقة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>اسم الباقة</th>
                          <th>السرعة</th>
                          <th>حجم الباقة</th>
                          <th>السعر (ل.س)</th>
                          <th>النوع</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.wifi_outdoor_monthly || []).map((pkg, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.package || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly[idx].package = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.speed || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly[idx].speed = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.quota || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly[idx].quota = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.price || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={pkg.type || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly[idx].type = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_monthly.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'adsl_topup' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>باقات الشحن الإضافي (Topup)</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.adsl_topup = [...(next.adsl_topup || []), { quota: '', price: '' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة شحنة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>حجم الباقة الإضافية</th>
                          <th>السعر (ل.س)</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.adsl_topup || []).map((t, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={t.quota}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_topup[idx].quota = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={t.price}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.adsl_topup[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.adsl_topup.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'wifi_outdoor_topup' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>باقات شحن WIFI الإضافية</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.wifi_outdoor_topup = [...(next.wifi_outdoor_topup || []), { quota: '10 GB', price: '100' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة شحنة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>حجم الباقة الإضافية</th>
                          <th>السعر (ل.س)</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.wifi_outdoor_topup || []).map((t, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={t.quota || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_topup[idx].quota = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={t.price || ''}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_topup[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.wifi_outdoor_topup.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'services' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>الخدمات الإضافية والرسوم</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.services = [...(next.services || []), { name: 'خدمة جديدة', price: '50', notes: 'ملاحظة' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة خدمة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>اسم الخدمة</th>
                          <th>السعر (ل.س)</th>
                          <th>ملاحظات وتفاصيل</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.services || []).map((srv, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={srv.name}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.services[idx].name = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={srv.price}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.services[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={srv.notes}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.services[idx].notes = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.services.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'iptv_packages' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>باقات البث الرقمي (IPTV)</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.iptv_packages = [...(next.iptv_packages || []), { name: 'PRO SPORT', price: '175', channels: '80 قناة' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة باقة
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>اسم الباقة</th>
                          <th>السعر (ل.س)</th>
                          <th>القنوات المتاحة</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.iptv_packages || []).map((iptv, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={iptv.name}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.iptv_packages[idx].name = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={iptv.price}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.iptv_packages[idx].price = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={iptv.channels}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.iptv_packages[idx].channels = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.iptv_packages.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {companySubTab === 'contacts' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>بيانات وأقسام التواصل</span>
                    {canEdit && (<button type="button"
                      onClick={() => {
                        const next = { ...companyData };
                        next.contacts = [...(next.contacts || []), { department: 'قسم جديد', number: '011-0000' }];
                        setCompanyData(next);
                      }}
                      className="hcn-btn-outlined"
                      style={{ fontSize: 12, padding: '4px 10px', gap: 4 }}
                    >
                      <Plus size={14} /> إضافة رقم
                    </button>)}
                  </div>
                  <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                    <table className="hcn-table">
                      <thead>
                        <tr>
                          <th>القسم المعني</th>
                          <th>رقم الهاتف / الواتساب</th>
                          {canEdit && <th style={{ width: 60, textAlign: 'center' }}>حذف</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {(companyData.contacts || []).map((c, idx) => (
                          <tr key={idx}>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={c.department}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.contacts[idx].department = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="hcn-input"
                                style={{ height: 32, fontSize: 12 }}
                                value={c.number}
                                disabled={!canEdit}
                                onChange={(e) => {
                                  const next = { ...companyData };
                                  next.contacts[idx].number = e.target.value;
                                  setCompanyData(next);
                                }}
                              />
                            </td>
                            {canEdit && (<td style={{ textAlign: 'center' }}>
                              <button type="button"
                                onClick={() => {
                                  const next = { ...companyData };
                                  next.contacts.splice(idx, 1);
                                  setCompanyData(next);
                                }}
                                className="hcn-btn-ghost"
                                style={{ color: 'var(--error)', padding: 4 }}
                              >
                                <Trash2 size={15} />
                              </button>
                            </td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeSubTab === 'pdfs' && (
        <div className="hcn-card" style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: '20px' }}>
          {canEdit && (
            <div style={{
              border: '2px dashed var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '24px 20px',
              textAlign: 'center',
              background: 'var(--bg-paper)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 8
            }}>
              <UploadCloud size={30} style={{ color: 'var(--primary)' }} />
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                  إرفاق دليل أو كتيب فني جديد (PDF)
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  الملفات المدعومة: PDF فقط — يتم اعتماد المحتوى الفني تلقائياً
                </div>
              </div>

              <label className="hcn-btn-primary" style={{ cursor: 'pointer', gap: 6, marginTop: 4, height: 34, fontSize: 12, fontWeight: 600 }}>
                {uploadingPdf ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
                {uploadingPdf ? 'جاري الرفع...' : 'اختيار ملف PDF'}
                <input
                  type="file"
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={handlePdfUpload}
                  disabled={uploadingPdf}
                />
              </label>
            </div>
          )}

          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>الأدلة الفنية المعتمدة ({pdfList.length})</div>

          {pdfLoading ? (
            <div style={{ textAlign: 'center', padding: 30 }}><Loader2 className="animate-spin" size={24} style={{ color: 'var(--primary)' }} /></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {pdfList.map((pdf, idx) => (
                <div
                  key={idx}
                  style={{
                    border: '1px solid var(--border-color)',
                    borderRadius: 'var(--radius-md)',
                    padding: 14,
                    background: 'var(--bg-paper)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: 12
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(0, 167, 111, 0.1)',
                      color: 'var(--primary)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <FileText size={18} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: 13, color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                        {pdf.title}
                      </div>
                      <div style={{ display: 'flex', gap: 6, fontSize: 11, color: 'var(--text-disabled)', marginTop: 3 }}>
                        <span>{pdf.size_kb} KB</span>
                        <span>•</span>
                        <span style={{ color: 'var(--success)' }}>معتمد</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: 10 }}>
                    <a
                      href={`${API}/api/rag/pdfs/download/${encodeURIComponent(pdf.filename)}`}
                      target="_blank"
                      rel="noreferrer"
                      className="hcn-btn-outlined"
                      style={{ fontSize: 11, padding: '4px 10px', gap: 4 }}
                    >
                      <Download size={13} /> تحميل / معاينة
                    </a>

                    {canEdit && (
                      <button type="button"
                        onClick={() => handleDeletePdf(pdf.filename)}
                        className="hcn-btn-ghost"
                        style={{ color: 'var(--error)', fontSize: 11, padding: '4px 8px', gap: 4 }}
                      >
                        <Trash2 size={13} /> حذف
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
{modalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 16
        }}>
          <div className="hcn-card" style={{ width: '100%', maxWidth: 520, display: 'flex', flexDirection: 'column', gap: 16, padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                {modalMode === 'add' ? 'إضافة سؤال جديد' : 'تعديل السؤال المعتمد'}
              </h3>
              <button type="button" onClick={() => setModalOpen(false)} className="hcn-btn-ghost" style={{ padding: 4 }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveQA} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--text-secondary)' }}>القسم والتصنيف</label>
                <select
                  className="hcn-input"
                  style={{ width: '100%', minHeight: 40, padding: '8px 12px', fontSize: 13 }}
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  {Object.entries(CATEGORY_MAP).filter(([k]) => k !== 'ALL').map(([k, label]) => (
                    <option key={k} value={k}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--text-secondary)' }}>نص السؤال</label>
                <input
                  type="text"
                  className="hcn-input"
                  style={{ width: '100%', minHeight: 40, padding: '8px 12px', fontSize: 13 }}
                  placeholder="أدخل صيغة السؤال..."
                  value={formData.question}
                  onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, marginBottom: 4, color: 'var(--text-secondary)' }}>الإجابة المعتمدة</label>
                <textarea
                  className="hcn-input"
                  style={{ width: '100%', minHeight: 100, resize: 'vertical', fontFamily: 'inherit', fontSize: 13 }}
                  placeholder="أدخل نص الإجابة المعتمدة..."
                  value={formData.answer}
                  onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
                <button type="button" onClick={() => setModalOpen(false)} className="hcn-btn-outlined" style={{ fontSize: 13, height: 34 }}>
                  إلغاء
                </button>
                <button type="submit" disabled={savingQa} className="hcn-btn-primary" style={{ gap: 6, fontSize: 13, height: 34, fontWeight: 600 }}>
                  {savingQa ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
                  {savingQa ? 'جاري الحفظ...' : (modalMode === 'add' ? 'إضافة' : 'حفظ التعديلات')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={confirmAction.isOpen}
        title={confirmAction.title}
        message={confirmAction.message}
        type="danger"
        confirmText="تأكيد الحذف"
        onConfirm={confirmAction.onConfirm}
        onCancel={() => setConfirmAction({ isOpen: false })}
      />

    </div>
  );
}
