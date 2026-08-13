import React, { useState } from 'react';
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

export default function App() {
  const [activeTab, setActiveTab] = useState('crm');

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':    return <OverviewTab setActiveTab={setActiveTab} />;
      case 'actions':     return <AgentActionLogsTab />;
      case 'sessions':    return <SessionsChatTab />;
      case 'analytics':   return <AnalyticsTab />;
      case 'crm':         return <CrmLookupTab />;
      case 'rag':         return <KnowledgeBaseTab />;
      case 'playground':  return <TestPlaygroundTab />;
      case 'permissions': return <PermissionsTab />;
      case 'settings':    return <SettingsTab />;
      default:            return <CrmLookupTab />;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-default)' }} dir="rtl">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main style={{
        flex: 1,
        padding: '40px 40px',
        overflowY: 'auto',
        maxHeight: '100vh',
        minWidth: 0,
        backgroundColor: 'var(--bg-default)'
      }}>
        {renderActiveTab()}
      </main>
    </div>
  );
}
