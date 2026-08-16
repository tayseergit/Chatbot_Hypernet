import React from 'react';
import { useAuth } from '../context/AuthContext';
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
  Megaphone,
  LogOut,
  KeyRound,
  UserCog
} from 'lucide-react';

const sections = [
  {
    title: 'نظرة عامة',
    items: [
      { id: 'overview', label: 'الرئيسية', icon: LayoutDashboard },
      { id: 'analytics', label: 'الإحصائيات', icon: BarChart3, requirePerm: 'view_dashboard' },
      { id: 'sessions', label: 'المحادثات', icon: MessageSquare, requirePerm: 'view_chat_sessions' },
    ]
  },
  {
    title: 'الإدارة',
    items: [
      { id: 'crm', label: 'المشتركين', icon: Users, requirePerm: 'view_system_logs' },
      { id: 'notifications', label: 'بث الإشعارات', icon: Megaphone, requirePerm: 'manage_agent_settings' },
      { id: 'rag', label: 'قاعدة المعرفة', icon: BookOpen, requirePerm: 'view_knowledge_base' },
      { id: 'permissions', label: 'الصلاحيات', icon: ShieldCheck, requirePerm: 'manage_agent_settings' },
      { id: 'admins', label: 'إدارة المدراء', icon: UserCog, requirePerm: 'manage_admins' },
      { id: 'playground', label: 'بيئة الاختبار', icon: FlaskConical, requirePerm: 'use_playground' },
    ]
  }
];

export default function Sidebar({ activeTab, setActiveTab }) {
  const { admin, logout } = useAuth();

  const getRoleLabel = (role) => {
    switch (role) {
      case 'super_admin': return 'مدير عام النظام';
      case 'admin': return 'مدير النظام';
      case 'operator': return 'مشغّل لوحة التحكم';
      default: return 'مسؤول معتمد';
    }
  };

  const getInitial = () => {
    if (admin?.full_name && admin.full_name.trim().length > 0) {
      return admin.full_name.trim().charAt(0).toUpperCase();
    }
    if (admin?.username) {
      return admin.username.charAt(0).toUpperCase();
    }
    return 'A';
  };

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
          width: 34,
          height: 34,
          borderRadius: 10,
          background: 'linear-gradient(135deg, #00A76F 0%, #007850 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: '0 4px 12px rgba(0, 167, 111, 0.35)',
        }}>
          <Wifi size={19} color="#fff" />
        </div>
        <div>
          <div style={{
            fontWeight: 800,
            fontSize: 16,
            color: 'var(--text-primary)',
            letterSpacing: '1px',
          }}>
            HYPERNET
          </div>
        </div>
      </div>

      {/* Authenticated Admin Profile Card */}
      <div style={{ padding: '0 20px 20px' }}>
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: 14,
          padding: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          transition: 'background 0.2s',
          cursor: 'pointer',
        }}
          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'}
        >
          <div style={{
            width: 38,
            height: 38,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #00A76F 0%, #0284c7 100%)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: 15,
            flexShrink: 0,
            boxShadow: '0 2px 8px rgba(0, 167, 111, 0.25)',
          }}>
            {getInitial()}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{
              color: 'var(--text-primary)',
              fontSize: 13,
              fontWeight: 700,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {admin?.full_name || admin?.username || 'مدير النظام'}
            </div>
            <div style={{
              color: 'var(--text-disabled)',
              fontSize: 11,
              marginTop: 2,
            }}>
              مسؤول النظام
            </div>
          </div>

          <button
            onClick={(e) => { e.stopPropagation(); logout(true); }}
            title="تسجيل الخروج"
            style={{
              background: 'transparent',
              color: 'var(--text-disabled)',
              border: 'none',
              padding: '6px',
              borderRadius: '50%',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
              e.currentTarget.style.color = '#ef4444';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.color = 'var(--text-disabled)';
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>

      {/* Nav Items */}
      <nav style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 24, flex: 1 }}>
        {sections.map((section, idx) => {
          const visibleItems = section.items.filter(item => {
            if (item.requirePerm) {
              return admin?.permissions?.includes(item.requirePerm);
            }
            return true;
          });

          if (visibleItems.length === 0) return null;

          return (
            <div key={idx}>
              <div style={{
                fontSize: 12,
                fontWeight: 700,
                color: '#64748b',
                marginBottom: 10,
                paddingRight: 12,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {section.title}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {visibleItems.map(item => {
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
            </div>
          );
        })}
      </nav>


    </aside>
  );
}
