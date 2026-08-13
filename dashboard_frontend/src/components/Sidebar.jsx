import React from 'react';
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  BarChart3,
  Users,
  BookOpen,
  Settings,
  FlaskConical,
  Wifi,
  ShieldCheck,
} from 'lucide-react';

const sections = [
  {
    title: 'نظرة عامة',
    items: [
      { id: 'overview',    label: 'الرئيسية',           icon: LayoutDashboard },
      { id: 'analytics',   label: 'الإحصائيات',        icon: BarChart3 },
      { id: 'sessions',    label: 'المحادثات والجلسات',icon: MessageSquare },
    ]
  },
  {
    title: 'الإدارة',
    items: [
      { id: 'crm',         label: 'العملاء',           icon: Users },
      { id: 'actions',     label: 'سجل العمليات',        icon: FileText },
      { id: 'rag',         label: 'قاعدة المعرفة',      icon: BookOpen },
      { id: 'permissions', label: 'الصلاحيات',          icon: ShieldCheck },
      { id: 'playground',  label: 'بيئة الاختبار',      icon: FlaskConical },
      { id: 'settings',    label: 'الإعدادات',           icon: Settings },
    ]
  }
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="hcn-sidebar">
      {/* Brand Header */}
      <div style={{
        padding: '24px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: 'var(--primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Wifi size={18} color="#fff" />
        </div>
        <div>
          <div style={{
            fontWeight: 700,
            fontSize: 16,
            color: 'var(--text-primary)',
            letterSpacing: '1px',
          }}>
            HYPERNET
          </div>
        </div>
      </div>

      {/* User Profile Card */}
      <div style={{ padding: '0 20px 24px' }}>
        <div style={{
          background: 'rgba(145, 158, 171, 0.12)',
          borderRadius: 12,
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'var(--primary)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: 16,
          }}>
            A
          </div>
          <div>
            <div style={{ color: 'var(--text-primary)', fontSize: 14, fontWeight: 700 }}>Admin</div>
            <div style={{ color: 'var(--sidebar-text)', fontSize: 12 }}>admin@hypernet.sy</div>
          </div>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ padding: '0 20px', flex: 1, overflowY: 'auto' }}>
        {sections.map((section, idx) => (
          <div key={idx} style={{ marginBottom: 24 }}>
            <div style={{
              fontSize: 11,
              fontWeight: 700,
              color: 'var(--sidebar-text)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              marginBottom: 12,
              padding: '0 8px',
            }}>
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 16,
                    padding: '12px 16px',
                    borderRadius: 8,
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: 14,
                    fontWeight: isActive ? 600 : 500,
                    fontFamily: 'inherit',
                    color: isActive ? 'var(--sidebar-active)' : 'var(--sidebar-text)',
                    background: isActive ? 'rgba(0, 167, 111, 0.08)' : 'transparent',
                    transition: 'all 0.2s',
                    textAlign: 'right',
                    marginBottom: 4,
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'var(--sidebar-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <Icon size={20} strokeWidth={isActive ? 2.5 : 2} color={isActive ? 'var(--sidebar-active)' : 'var(--sidebar-text)'} />
                  <span style={{ flex: 1 }}>{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* System Status Footer */}
      <div style={{
        padding: '24px 20px',
      }}>
        <div style={{
          background: 'rgba(145, 158, 171, 0.08)',
          borderRadius: 12,
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--sidebar-text)', fontSize: 13, fontWeight: 500 }}>System API</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--primary)', fontWeight: 600, fontSize: 12 }}>
              <span className="hcn-dot hcn-dot-green hcn-dot-pulse" style={{ width: 6, height: 6 }} />
              Online
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
