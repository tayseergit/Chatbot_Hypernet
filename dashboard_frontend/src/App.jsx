import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginView from './components/LoginView';
import Sidebar from './components/Sidebar';
import OverviewTab from './components/OverviewTab';
import AgentActionLogsTab from './components/AgentActionLogsTab';
import SessionsChatTab from './components/SessionsChatTab';
import AnalyticsTab from './components/AnalyticsTab';
import CrmLookupTab from './components/CrmLookupTab';
import KnowledgeBaseTab from './components/KnowledgeBaseTab';
import TestPlaygroundTab from './components/TestPlaygroundTab';
import SettingsTab from './components/SettingsTab';
import PermissionsTab from './components/PermissionsTab';
import BroadcastTab from './components/BroadcastTab';

function DashboardContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  if (isLoading) {
    return (
      <div
        dir="rtl"
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-default)',
          color: '#ffffff',
          fontFamily: "'Cairo', sans-serif",
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              border: '3px solid rgba(0, 167, 111, 0.2)',
              borderTopColor: '#00A76F',
              borderRadius: '50%',
              margin: '0 auto 16px',
              animation: 'spin 0.8s linear infinite',
            }}
          />
          <div style={{ fontSize: '15px', color: '#94a3b8' }}>جاري التحقق من أمان الجلسة...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':      return <OverviewTab setActiveTab={setActiveTab} />;
      case 'sessions':      return <SessionsChatTab />;
      case 'analytics':     return <AnalyticsTab />;
      case 'crm':           return <CrmLookupTab />;
      case 'notifications': return <BroadcastTab />;
      case 'rag':           return <KnowledgeBaseTab />;
      case 'playground':    return <TestPlaygroundTab />;
      case 'permissions':   return <PermissionsTab />;
      case 'settings':      return <SettingsTab />;
      default:              return <OverviewTab setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-default)' }} dir="rtl">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main
        style={{
          flex: 1,
          padding: '40px 40px',
          overflowY: 'auto',
          maxHeight: '100vh',
          minWidth: 0,
          backgroundColor: 'var(--bg-default)',
        }}
      >
        {renderActiveTab()}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
