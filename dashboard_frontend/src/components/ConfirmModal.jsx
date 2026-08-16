import React from 'react';
import { AlertCircle, CheckCircle, Info, Trash2, Send } from 'lucide-react';
import './ConfirmModal.css';

export default function ConfirmModal({ 
  isOpen, 
  title, 
  message, 
  onConfirm, 
  onCancel, 
  type = 'danger', // 'danger' | 'info' | 'success' | 'primary'
  confirmText = 'تأكيد',
  cancelText = 'إلغاء'
}) {
  if (!isOpen) return null;

  const renderIcon = () => {
    switch(type) {
      case 'danger': return <Trash2 size={28} />;
      case 'success': return <CheckCircle size={28} />;
      case 'primary': return <Send size={28} />;
      case 'info':
      default: return <Info size={28} />;
    }
  };

  return (
    <div className="cm-overlay" onClick={onCancel}>
      <div className={`cm-card cm-type-${type}`} onClick={e => e.stopPropagation()}>
        <div className="cm-icon-wrapper">
          <div className="cm-icon-bg"></div>
          {renderIcon()}
        </div>
        <h3 className="cm-title">{title}</h3>
        <p className="cm-message">{message}</p>
        <div className="cm-actions">
          <button className="cm-btn-cancel" onClick={onCancel}>{cancelText}</button>
          <button className="cm-btn-confirm" onClick={onConfirm}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
