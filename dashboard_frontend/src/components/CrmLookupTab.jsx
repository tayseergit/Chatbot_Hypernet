import React, { useState, useMemo } from 'react';
import {
  Search, Plus, Filter, MoreVertical, ChevronLeft, ChevronRight,
  User, Pencil, Wifi, Monitor, FileText, History, X,
  ShieldCheck, Phone, MapPin, Plug, Trash2, Package,
  CreditCard, Settings, Clock, RefreshCw, CheckCircle2,
} from 'lucide-react';

/* ─────────────── بيانات العملاء ─────────────── */
const CUSTOMERS = [
  {
    id: 'C001', username: 'ahmed.m@hypernet.iq', firstName: 'Ahmed', lastName: 'Mohamed',
    phone: '+964 770 123 4567', address: 'الكرادة، بغداد', notes: '',
    status: 'active', statusColor: 'var(--success)',
    plan: 'Gold 50Mbps Fiber', planPrice: 45000, userType: 'Fiber Access Point',
    balance: 125000, paidUntil: '2026-09-01', remainingDays: 21,
    parent: 'hypernet.iq', group: 'Gold',
    ipAddress: '192.168.1.104', lastOnline: '2026-08-11 10:29',
    iptv: 'بدون اشتراك', remainingDownload: '225.00 GB',
    invoices: [
      { id: 'INV-2002', date: '2026-07-01 08:00:00', type: 'تجديد', amount: 45000, desc: 'اشتراك شهري — يوليو 2026', createdBy: 'admin', paymentMethod: 'نقد', paid: true },
      { id: 'INV-2001', date: '2026-06-01 08:00:00', type: 'تجديد', amount: 45000, desc: 'اشتراك شهري — يونيو 2026', createdBy: 'admin', paymentMethod: 'نقد', paid: true },
    ],
    sessions: [
      { id: 'S-1001', start: '2026-08-11 10:00', end: '—', ip: '192.168.1.104', download: '1.2 GB', upload: '320 MB', status: 'نشط' },
    ],
  },
  {
    id: 'C002', username: 'fatima.ali@hypernet.iq', firstName: 'Fatima', lastName: 'Ali',
    phone: '+964 770 987 6543', address: 'المنصور، بغداد', notes: '',
    status: 'active', statusColor: 'var(--success)',
    plan: 'Silver 25Mbps Fiber', planPrice: 30000, userType: 'Fiber Access Point',
    balance: 75000, paidUntil: '2026-08-20', remainingDays: 9,
    parent: 'hypernet.iq', group: 'Silver',
    ipAddress: '192.168.1.112', lastOnline: '2026-08-11 10:15',
    iptv: 'بدون اشتراك', remainingDownload: '180.00 GB',
    invoices: [
      { id: 'INV-2003', date: '2026-06-01 08:00:00', type: 'تجديد', amount: 30000, desc: 'اشتراك شهري — يونيو 2026', createdBy: 'admin', paymentMethod: 'نقد', paid: true },
    ],
    sessions: [],
  },
  {
    id: 'C003', username: 'hassan.m@hypernet.iq', firstName: 'Hassan', lastName: 'Mahmoud',
    phone: '+964 780 555 1212', address: 'عينكاوه، أربيل', notes: '',
    status: 'active', statusColor: 'var(--warning)',
    plan: 'Platinum 100Mbps', planPrice: 75000, userType: 'Wireless Access Point',
    balance: 210000, paidUntil: '2026-10-15', remainingDays: 65,
    parent: 'hypernet.iq', group: 'Platinum',
    ipAddress: '192.168.2.45', lastOnline: '2026-08-11 09:00',
    iptv: 'مفعّل', remainingDownload: 'غير محدود',
    invoices: [
      { id: 'INV-2004', date: '2026-07-01 08:00:00', type: 'تجديد', amount: 75000, desc: 'اشتراك شهري — يوليو 2026', createdBy: 'admin', paymentMethod: 'تحويل', paid: true },
    ],
    sessions: [
      { id: 'S-1003', start: '2026-08-11 09:00', end: '—', ip: '192.168.2.45', download: '3.1 GB', upload: '890 MB', status: 'نشط' },
    ],
  },
  {
    id: 'C004', username: 'zainab.h@hypernet.iq', firstName: 'Zainab', lastName: 'Hussein',
    phone: '+964 750 444 8899', address: 'العشار، البصرة', notes: 'حساب معلّق',
    status: 'suspended', statusColor: 'var(--error)',
    plan: 'Bronze 10Mbps', planPrice: 20000, userType: 'Wireless Access Point',
    balance: 0, paidUntil: '2026-07-31', remainingDays: 0,
    parent: 'hypernet.iq', group: 'Bronze',
    ipAddress: '—', lastOnline: '2026-08-09 15:40',
    iptv: 'بدون اشتراك', remainingDownload: '0.00 GB',
    invoices: [
      { id: 'INV-2005', date: '2026-08-01 08:00:00', type: 'تجديد', amount: 20000, desc: 'اشتراك شهري — أغسطس 2026', createdBy: 'admin', paymentMethod: '—', paid: false },
    ],
    sessions: [],
  },
];

/* ─────────────── مكوّن: صف الجدول ─────────────── */
function TableRow({ cust, selected, onSelect, onOpen, dense }) {
  return (
    <tr>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onSelect(cust.id)}
          style={{ accentColor: 'var(--primary)', width: 18, height: 18, cursor: 'pointer' }}
        />
      </td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>
        <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: cust.statusColor }} />
      </td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>
        <span
          onClick={() => onOpen(cust)}
          style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: 14, cursor: 'pointer', textDecoration: 'none' }}
          onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
          onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}
        >
          {cust.username}
        </span>
      </td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>{cust.firstName}</td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>{cust.lastName}</td>
      <td style={{ padding: dense ? '10px 16px' : '16px', fontFamily: 'monospace' }}>{cust.paidUntil}</td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>{cust.parent}</td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>{cust.plan}</td>
      <td style={{ padding: dense ? '10px 16px' : '16px' }}>
        <span className={`hcn-badge ${cust.remainingDays === 0 ? 'hcn-badge-error' : cust.remainingDays < 10 ? 'hcn-badge-warning' : 'hcn-badge-success'}`}>
          {cust.remainingDays}
        </span>
      </td>
      <td style={{ padding: dense ? '10px 16px' : '16px', textAlign: 'left' }}>
        <button onClick={() => onOpen(cust)} className="hcn-btn-icon">
          <MoreVertical size={20} />
        </button>
      </td>
    </tr>
  );
}

/* ─────────────── مكوّن: نافذة التفاصيل ─────────────── */
const DETAIL_TABS = [
  { key: 'overview',  label: 'نظرة عامة', icon: Monitor },
  { key: 'invoices',  label: 'الفواتير',   icon: FileText },
  { key: 'sessions',  label: 'الجلسات',    icon: Wifi },
  { key: 'history',   label: 'السجل',      icon: History },
];

function DetailModal({ cust, onClose }) {
  const [tab, setTab] = useState('overview');

  if (!cust) return null;

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1200,
      background: 'rgba(33, 43, 54, 0.48)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      padding: '40px 16px', overflowY: 'auto',
    }}>
      <div className="hcn-card animate-scale-in" style={{ width: '100%', maxWidth: 860, display: 'flex', flexDirection: 'column' }}>

        {/* ── Breadcrumb ── */}
        <div style={{ padding: '24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={onClose} className="hcn-btn-icon" style={{ width: 32, height: 32 }}>
            <ChevronLeft size={20} />
          </button>
          <span style={{ fontSize: 14, color: 'var(--text-disabled)' }}>لوحة التحكم</span>
          <span style={{ color: 'var(--text-disabled)' }}>›</span>
          <span style={{ fontSize: 14, color: 'var(--text-secondary)', cursor: 'pointer' }}>العملاء</span>
          <span style={{ color: 'var(--text-disabled)' }}>›</span>
          <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600 }}>{cust.username}</span>
          <div style={{ flex: 1 }} />
          <button onClick={onClose} className="hcn-btn-icon" style={{ width: 32, height: 32 }}>
            <X size={20} />
          </button>
        </div>

        {/* ── Tabs ── */}
        <div className="hcn-tabs-container">
          {DETAIL_TABS.map(t => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`hcn-tab ${active ? 'active' : ''}`}
              >
                <Icon size={18} />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* ── Tab Content ── */}
        <div style={{ padding: '0 24px 32px' }}>

          {/* نظرة عامة */}
          {tab === 'overview' && (
            <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 32 }}>
              {/* اليسار: Avatar + Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                {/* Avatar */}
                <div className="hcn-card" style={{ padding: '24px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, boxShadow: 'var(--shadow-card)', border: '1px solid var(--border)' }}>
                  <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--bg-neutral)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <User size={40} color="var(--text-disabled)" />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, width: '100%' }}>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{cust.firstName} {cust.lastName}</div>
                    <div style={{ fontSize: 14, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}><Phone size={14} /> {cust.phone}</div>
                    <div style={{ fontSize: 14, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}><MapPin size={14} /> {cust.address}</div>
                  </div>
                  <span className={`hcn-badge ${cust.status === 'active' ? 'hcn-badge-success' : 'hcn-badge-error'}`}>
                    {cust.status === 'active' ? 'نشط' : 'موقوف'}
                  </span>
                </div>

                {/* أزرار الإجراءات */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  {[
                    { label: 'قطع الاتصال', icon: Plug,      color: 'var(--error)' },
                    { label: 'حذف',         icon: Trash2,    color: 'var(--error)' },
                    { label: 'تفعيل باقة',  icon: Package,   color: 'var(--success)' },
                    { label: 'إصدار فاتورة',icon: CreditCard,color: 'var(--info)' },
                    { label: 'إرسال إعدادات',icon: Settings, color: 'var(--text-secondary)' },
                    { label: 'تمديد المدة', icon: RefreshCw, color: '#8B5CF6' },
                  ].map(btn => {
                    const Icon = btn.icon;
                    return (
                      <button
                        key={btn.label}
                        onClick={() => alert(`${btn.label}: ${cust.username}`)}
                        style={{
                          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                          padding: '12px', borderRadius: '12px', border: '1px solid var(--border)',
                          background: 'transparent', cursor: 'pointer', fontFamily: 'inherit',
                          fontSize: 13, color: 'var(--text-primary)', fontWeight: 600, transition: 'all 0.2s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-neutral)'; e.currentTarget.style.borderColor = btn.color; e.currentTarget.style.color = btn.color; }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                      >
                        <Icon size={20} color={btn.color} />
                        {btn.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* اليمين: حقول التفاصيل */}
              <div className="hcn-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', border: '1px solid var(--border)', boxShadow: 'none' }}>
                {[
                  { label: 'اسم المستخدم',      value: cust.username },
                  { label: 'نوع المستخدم',       value: cust.userType },
                  { label: 'الرصيد',             value: `${cust.balance.toLocaleString()} د.ع` },
                  { label: 'الباقة',             value: cust.plan },
                  { label: 'تاريخ الانتهاء',     value: cust.paidUntil },
                  { label: 'المجموعة',           value: cust.group },
                  { label: 'سعر الباقة',        value: `${cust.planPrice.toLocaleString()} د.ع/شهر` },
                  { label: 'اشتراك IPTV',        value: cust.iptv },
                  { label: 'التنزيل المتبقي',    value: cust.remainingDownload },
                  { label: 'الأيام المتبقية',    value: `${cust.remainingDays} يوم` },
                  { label: 'المشرف الأعلى',      value: cust.parent },
                  { label: 'آخر اتصال',          value: cust.lastOnline },
                ].map((field, i) => (
                  <div key={field.label} style={{
                    display: 'flex', alignItems: 'center',
                    padding: '16px 0',
                    borderBottom: i === 11 ? 'none' : '1px dashed var(--border)',
                  }}>
                    <span style={{ width: 200, fontSize: 14, color: 'var(--text-secondary)', fontWeight: 500 }}>
                      {field.label}
                    </span>
                    <span style={{ fontSize: 14, color: 'var(--text-primary)', fontWeight: 600, flex: 1 }}>{field.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* الفواتير */}
          {tab === 'invoices' && (
            <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border)' }}>
              <table className="hcn-table">
                <thead>
                  <tr>
                    {['رقم الفاتورة', 'التاريخ', 'النوع', 'المبلغ', 'الوصف', 'بواسطة', 'طريقة الدفع', 'مدفوع'].map(h => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cust.invoices.map(inv => (
                    <tr key={inv.id}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{inv.id}</td>
                      <td style={{ fontFamily: 'monospace' }}>{inv.date}</td>
                      <td>{inv.type}</td>
                      <td style={{ fontWeight: 700 }}>{inv.amount.toLocaleString()}</td>
                      <td>{inv.desc}</td>
                      <td>{inv.createdBy}</td>
                      <td>{inv.paymentMethod}</td>
                      <td>
                        {inv.paid
                          ? <CheckCircle2 size={22} color="var(--success)" />
                          : <span style={{ display: 'inline-block', width: 22, height: 22, borderRadius: '50%', border: '2px solid var(--border)' }} />
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* الجلسات */}
          {tab === 'sessions' && (
            <div className="hcn-table-wrapper" style={{ border: '1px solid var(--border)' }}>
              {cust.sessions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-disabled)', fontSize: 15 }}>
                  لا توجد جلسات نشطة
                </div>
              ) : (
                <table className="hcn-table">
                  <thead>
                    <tr>
                      {['رقم الجلسة', 'البداية', 'النهاية', 'عنوان IP', 'تنزيل', 'رفع', 'الحالة'].map(h => (
                        <th key={h}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cust.sessions.map(s => (
                      <tr key={s.id}>
                        <td style={{ fontFamily: 'monospace' }}>{s.id}</td>
                        <td style={{ fontFamily: 'monospace' }}>{s.start}</td>
                        <td>{s.end}</td>
                        <td style={{ fontFamily: 'monospace' }}>{s.ip}</td>
                        <td>{s.download}</td>
                        <td>{s.upload}</td>
                        <td>
                          <span className="hcn-badge hcn-badge-success">{s.status}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {/* السجل */}
          {tab === 'history' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { action: 'تسجيل دخول', time: '2026-08-11 10:29', by: 'system' },
                { action: 'تجديد اشتراك', time: '2026-07-01 08:00', by: 'admin' },
                { action: 'إنشاء الحساب', time: '2026-01-15 09:00', by: 'admin' },
              ].map((log, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px', background: 'var(--bg-paper)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                  <Clock size={20} color="var(--text-disabled)" />
                  <span style={{ fontSize: 15, color: 'var(--text-primary)', flex: 1, fontWeight: 600 }}>{log.action}</span>
                  <span style={{ fontSize: 13, fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{log.time}</span>
                  <span style={{ fontSize: 14, color: 'var(--primary)', fontWeight: 600 }}>{log.by}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─────────────── المكوّن الرئيسي ─────────────── */
export default function CrmLookupTab() {
  const [search, setSearch]               = useState('');
  const [selected, setSelected]           = useState([]);
  const [openCustomer, setOpenCustomer]   = useState(null);
  const [showFilter, setShowFilter]       = useState(false);
  const [dense, setDense]                 = useState(false);
  const [page, setPage]                   = useState(0);
  const [rowsPerPage]                     = useState(5);
  const [filterStatus, setFilterStatus]   = useState('All');
  const [filterPlan, setFilterPlan]       = useState('All');
  const [activeTab, setActiveTab]         = useState('all');

  const filtered = useMemo(() =>
    CUSTOMERS.filter(c => {
      const q = search.toLowerCase();
      const matchSearch = !q ||
        c.username.toLowerCase().includes(q) ||
        c.firstName.toLowerCase().includes(q) ||
        c.lastName.toLowerCase().includes(q) ||
        c.id.toLowerCase().includes(q);
      const matchStatus = filterStatus === 'All' || c.status === filterStatus.toLowerCase();
      const matchPlan   = filterPlan === 'All' || c.plan.includes(filterPlan);
      return matchSearch && matchStatus && matchPlan;
    }), [search, filterStatus, filterPlan]);

  const paginated   = filtered.slice(page * rowsPerPage, (page + 1) * rowsPerPage);
  const totalPages  = Math.ceil(filtered.length / rowsPerPage);

  const toggleSelect = (id) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const toggleAll = () =>
    setSelected(selected.length === paginated.length ? [] : paginated.map(c => c.id));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', position: 'relative' }}>

      {/* ── رأس الصفحة ── */}
      <div className="hcn-page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 className="hcn-title" style={{ marginBottom: 8 }}>قائمة العملاء</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text-disabled)' }}>
            <span>لوحة التحكم</span>
            <span>•</span>
            <span>العملاء</span>
            <span>•</span>
            <span style={{ color: 'var(--text-primary)' }}>القائمة</span>
          </div>
        </div>
        <button className="hcn-btn-primary" onClick={() => alert('إضافة عميل جديد')}>
          <Plus size={20} /> عميل جديد
        </button>
      </div>

      {/* ── Card الجدول ── */}
      <div className="hcn-card">
        {/* Tab Bar */}
        <div className="hcn-tabs-container" style={{ margin: 0, padding: '0 24px', borderBottom: '1px solid var(--border)' }}>
          <button className={`hcn-tab ${activeTab === 'all' ? 'active' : ''}`} onClick={() => setActiveTab('all')}>
            الكل <span className="hcn-tab-badge">{CUSTOMERS.length}</span>
          </button>
          <button className={`hcn-tab ${activeTab === 'active' ? 'active' : ''}`} onClick={() => setActiveTab('active')}>
            نشط <span className="hcn-tab-badge">{CUSTOMERS.filter(c=>c.status==='active').length}</span>
          </button>
          <button className={`hcn-tab ${activeTab === 'suspended' ? 'active' : ''}`} onClick={() => setActiveTab('suspended')}>
            موقوف <span className="hcn-tab-badge">{CUSTOMERS.filter(c=>c.status==='suspended').length}</span>
          </button>
        </div>

        {/* شريط البحث و الفلتر */}
        <div style={{ padding: '20px 24px', display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 500 }}>
            <Search size={20} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-disabled)' }} />
            <input
              type="text"
              placeholder="بحث..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0); }}
              className="hcn-input"
              style={{ paddingRight: 44 }}
            />
          </div>
          <button
            onClick={() => setShowFilter(v => !v)}
            className="hcn-btn-outlined"
            style={{ color: showFilter ? 'var(--primary)' : 'var(--text-secondary)', borderColor: showFilter ? 'var(--primary)' : 'var(--border-strong)' }}
          >
            <Filter size={18} /> فلتر
          </button>
        </div>

        {/* الجدول */}
        <div className="hcn-table-wrapper">
          <table className={`hcn-table ${dense ? 'hcn-table-dense' : ''}`}>
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
                {['الحالة', 'اسم المستخدم', 'الاسم الأول', 'الاسم الأخير', 'تاريخ الانتهاء', 'المشرف', 'الباقة', 'الأيام المتبقية', ''].map(h => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-disabled)', fontSize: 15 }}>
                    لا توجد بيانات
                  </td>
                </tr>
              ) : paginated.map(cust => (
                <TableRow
                  key={cust.id}
                  cust={cust}
                  selected={selected.includes(cust.id)}
                  onSelect={toggleSelect}
                  onOpen={setOpenCustomer}
                  dense={dense}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* ذيل الجدول */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', borderTop: '1px solid var(--border)' }}>
          {/* Dense Toggle */}
          <label style={{ display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer', fontSize: 14, color: 'var(--text-primary)', userSelect: 'none' }}>
            <button
              onClick={() => setDense(!dense)}
              className="hcn-toggle"
              style={{ background: dense ? 'var(--primary)' : 'var(--text-disabled)' }}
            >
              <div className="hcn-toggle-thumb" style={{ left: dense ? 22 : 2 }} />
            </button>
            مضغوط
          </label>

          {/* Pagination */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              الصفوف في الصفحة: <strong style={{ color: 'var(--text-primary)' }}>{rowsPerPage}</strong>
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {page * rowsPerPage + 1}–{Math.min((page + 1) * rowsPerPage, filtered.length)} من {filtered.length}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="hcn-btn-icon"
              >
                <ChevronRight size={24} />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="hcn-btn-icon"
              >
                <ChevronLeft size={24} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── لوحة الفلتر (تنزلق من اليسار) ── */}
      {showFilter && (
        <>
          <div onClick={() => setShowFilter(false)} style={{ position: 'fixed', inset: 0, zIndex: 900, background: 'rgba(33, 43, 54, 0.48)' }} />
          <div className="animate-slide-in" style={{
            position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 1000,
            width: 320, background: 'var(--bg-paper)', boxShadow: '4px 0 24px rgba(0,0,0,0.12)',
            display: 'flex', flexDirection: 'column',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '24px', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontWeight: 700, fontSize: 18 }}>خيارات الفلتر</span>
              <button onClick={() => setShowFilter(false)} className="hcn-btn-icon">
                <X size={20} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>الحالة</label>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="hcn-input">
                  <option value="All">الكل</option>
                  <option value="active">نشط</option>
                  <option value="suspended">موقوف</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>الباقة</label>
                <select value={filterPlan} onChange={e => setFilterPlan(e.target.value)} className="hcn-input">
                  <option value="All">الكل</option>
                  <option value="Gold">Gold</option>
                  <option value="Silver">Silver</option>
                  <option value="Platinum">Platinum</option>
                  <option value="Bronze">Bronze</option>
                </select>
              </div>
            </div>

            <div style={{ padding: '24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 12 }}>
              <button
                onClick={() => { setFilterStatus('All'); setFilterPlan('All'); setPage(0); }}
                className="hcn-btn-outlined" style={{ flex: 1 }}
              >
                مسح
              </button>
              <button
                onClick={() => { setPage(0); setShowFilter(false); }}
                className="hcn-btn-primary" style={{ flex: 1 }}
              >
                تطبيق
              </button>
            </div>
          </div>
        </>
      )}

      {/* ── نافذة التفاصيل ── */}
      {openCustomer && (
        <DetailModal cust={openCustomer} onClose={() => setOpenCustomer(null)} />
      )}
    </div>
  );
}
