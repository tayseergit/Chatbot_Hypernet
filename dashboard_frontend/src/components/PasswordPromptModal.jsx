import React, { useState, useEffect } from 'react';

const API = 'http://localhost:8000/api';
const UNLOCK_DURATION = 15 * 60 * 1000; // 15 minutes

export function usePasswordAuth() {
  const [modalState, setModalState] = useState({
    isOpen: false,
    actionName: '',
    onSuccess: null,
  });

  const requireAuth = (actionName, onSuccess) => {
    const unlockedUntil = sessionStorage.getItem('action_unlocked_until');
    if (unlockedUntil && Date.now() < parseInt(unlockedUntil, 10)) {
      const adminUsername = sessionStorage.getItem('unlocked_admin') || 'admin';
      onSuccess(adminUsername);
      return;
    }

    setModalState({
      isOpen: true,
      actionName,
      onSuccess: (admin) => {
        sessionStorage.setItem('action_unlocked_until', Date.now() + UNLOCK_DURATION);
        sessionStorage.setItem('unlocked_admin', admin);
        setModalState({ isOpen: false, actionName: '', onSuccess: null });
        onSuccess(admin);
      }
    });
  };

  const closeModal = () => {
    setModalState({ isOpen: false, actionName: '', onSuccess: null });
  };

  return {
    requireAuth,
    modalProps: {
      isOpen: modalState.isOpen,
      actionName: modalState.actionName,
      onSuccess: modalState.onSuccess,
      onClose: closeModal
    }
  };
}

export function PasswordPromptModal({ isOpen, onClose, onSuccess, actionName }) {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setPassword('');
      setError('');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/verify-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'كلمة المرور غير صحيحة');
      }
      const data = await res.json();
      const adminName = (data.admin && data.admin.username) ? data.admin.username : (data.admin || 'admin');
      if (onSuccess) onSuccess(adminName);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.5)', zIndex: 10000,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{ background: '#fff', padding: 32, borderRadius: 4, width: 420, maxWidth: '90%', boxShadow: '0 8px 24px rgba(0,0,0,0.2)', borderTop: '4px solid #1976d2' }}>
        <h3 style={{ marginTop: 0, marginBottom: 16, color: '#333', fontSize: 18, fontWeight: 'bold' }}>تأكيد الهوية مطلوب</h3>
        <p style={{ fontSize: 14, color: '#555', marginBottom: 24, lineHeight: 1.6 }}>
          أنت تحاول <strong>{actionName}</strong>.<br/>الرجاء إدخال كلمة المرور الخاصة بحساب المسؤول لإتمام العملية.
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="كلمة المرور"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '100%', padding: '12px 14px', border: '1px solid #ccc', borderRadius: 4, marginBottom: 12, fontFamily: 'inherit', fontSize: 14 }}
            autoFocus
          />
          {error && <div style={{ color: '#d32f2f', fontSize: 13, marginBottom: 16, fontWeight: 'bold' }}>{error}</div>}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
            <button type="button" onClick={onClose} style={{ padding: '8px 16px', border: '1px solid #ccc', background: '#f9f9f9', borderRadius: 4, cursor: 'pointer', fontWeight: 'bold', color: '#555' }}>إلغاء</button>
            <button type="submit" disabled={loading || !password} style={{ padding: '8px 24px', border: 'none', background: '#1976d2', color: '#fff', borderRadius: 4, cursor: loading || !password ? 'not-allowed' : 'pointer', opacity: loading || !password ? 0.7 : 1, fontWeight: 'bold' }}>
              {loading ? 'جاري التحقق...' : 'متابعة'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
