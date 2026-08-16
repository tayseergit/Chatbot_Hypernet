import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Users, Shield, Key, Edit, Trash2, CheckCircle, XCircle, UserPlus, ShieldPlus, AlertCircle
} from 'lucide-react';
import ConfirmModal from './ConfirmModal';

const API = 'http://localhost:8000/api';

export default function AdminsManagementTab() {
  const { admin, token } = useAuth();
  
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modals state
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [confirmAction, setConfirmAction] = useState({ isOpen: false, title: '', message: '', onConfirm: null });

  // Load Data
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [usersRes, rolesRes, permsRes] = await Promise.all([
        fetch(`${API}/admin/users`, { headers }),
        fetch(`${API}/admin/roles`, { headers }),
        fetch(`${API}/admin/permissions`, { headers })
      ]);
      
      if (usersRes.ok) setUsers(await usersRes.json());
      if (rolesRes.ok) setRoles(await rolesRes.json());
      if (permsRes.ok) setAvailablePermissions(await permsRes.json());
      
    } catch (err) {
      setError('فشل في تحميل البيانات.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteRole = (roleId) => {
    setConfirmAction({
      isOpen: true,
      title: 'تأكيد الحذف',
      message: 'هل أنت متأكد من حذف هذا الدور؟',
      onConfirm: async () => {
        setConfirmAction({ isOpen: false });
        try {
          const res = await fetch(`${API}/admin/roles/${roleId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || 'Error');
          setSuccess('تم الحذف بنجاح');
          fetchData();
        } catch (err) {
          setError(err.message);
        }
      }
    });
  };

  const handleDeleteUser = (userId) => {
    setConfirmAction({
      isOpen: true,
      title: 'تأكيد الحذف',
      message: 'هل أنت متأكد من حذف هذا المدير؟',
      onConfirm: async () => {
        setConfirmAction({ isOpen: false });
        try {
          const res = await fetch(`${API}/admin/users/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || 'Error');
          setSuccess('تم الحذف بنجاح');
          fetchData();
        } catch (err) {
          setError(err.message);
        }
      }
    });
  };

  if (loading) {
    return <div style={{ color: '#fff', textAlign: 'center', marginTop: 50 }}>جاري التحميل...</div>;
  }

  // Prevent non-super-admins from seeing the UI (extra frontend check)
  if (!admin?.permissions?.includes('manage_admins')) {
    return (
      <div style={{ padding: 40, color: '#ff4d4f', textAlign: 'center' }}>
        <h2>صلاحيات غير كافية</h2>
        <p>عذراً، هذه الصفحة مخصصة لمدراء النظام الرئيسيين فقط.</p>
      </div>
    );
  }

  return (
    <div style={{ color: 'var(--text-primary)', maxWidth: 1200, margin: '0 auto' }}>
      
      {error && (
        <div style={{ background: '#ff4d4f22', color: '#ff4d4f', padding: '12px 20px', borderRadius: 8, marginBottom: 20 }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ background: '#4caf5022', color: '#4caf50', padding: '12px 20px', borderRadius: 8, marginBottom: 20 }}>
          {success}
        </div>
      )}

      {/* --- Roles Section --- */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Shield size={24} /> أدوار الصلاحيات (Roles)</h2>
        <button 
          onClick={() => { setEditingRole(null); setShowRoleModal(true); }}
          style={{ background: '#00A76F', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', display: 'flex', gap: 8, alignItems: 'center' }}>
          <ShieldPlus size={18} /> إضافة دور جديد
        </button>
      </div>
      
      <div style={{ background: 'var(--bg-paper)', borderRadius: 12, boxShadow: 'var(--shadow-card)', overflow: 'hidden', marginBottom: 40 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
          <thead style={{ background: 'var(--bg-neutral)', borderBottom: '1px solid var(--border)' }}>
            <tr>
              <th style={{ padding: 16 }}>الدور</th>
              <th style={{ padding: 16 }}>الوصف</th>
              <th style={{ padding: 16 }}>عدد الصلاحيات</th>
              <th style={{ padding: 16, width: 100 }}>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {roles.map(r => (
              <tr key={r.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: 16 }}>{r.name}</td>
                <td style={{ padding: 16, color: 'var(--text-secondary)' }}>{r.description}</td>
                <td style={{ padding: 16 }}>
                  <span style={{ background: '#1976d244', color: '#64b5f6', padding: '4px 8px', borderRadius: 12, fontSize: 13 }}>
                    {r.permissions.length} صلاحيات
                  </span>
                </td>
                <td style={{ padding: 16 }}>
                  {r.name !== 'Super Admin' && r.name !== 'المدير الرئيسي' && (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button onClick={() => { setEditingRole(r); setShowRoleModal(true); }} style={{ background: 'transparent', border: 'none', color: '#64b5f6', cursor: 'pointer' }}><Edit size={18} /></button>
                      <button onClick={() => handleDeleteRole(r.id)} style={{ background: 'transparent', border: 'none', color: '#ff4d4f', cursor: 'pointer' }}><Trash2 size={18} /></button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* --- Users Section --- */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: 10 }}><Users size={24} /> مدراء النظام (Admins)</h2>
        <button 
          onClick={() => { setEditingUser(null); setShowUserModal(true); }}
          style={{ background: '#1976d2', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', display: 'flex', gap: 8, alignItems: 'center' }}>
          <UserPlus size={18} /> إضافة مدير
        </button>
      </div>

      <div style={{ background: 'var(--bg-panel)', borderRadius: 12, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'right' }}>
          <thead style={{ background: 'rgba(255,255,255,0.05)' }}>
            <tr>
              <th style={{ padding: 16 }}>اسم المستخدم</th>
              <th style={{ padding: 16 }}>الاسم الكامل</th>
              <th style={{ padding: 16 }}>الدور</th>
              <th style={{ padding: 16 }}>حالة الحساب</th>
              <th style={{ padding: 16, width: 100 }}>إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: 16, fontWeight: 'bold' }}>{u.username}</td>
                <td style={{ padding: 16, color: 'var(--text-secondary)' }}>{u.full_name || '-'}</td>
                <td style={{ padding: 16 }}>
                  {u.is_super_admin ? (
                    <span style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Shield size={14} /> مدير رئيسي
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-secondary)' }}>{u.role_name}</span>
                  )}
                </td>
                <td style={{ padding: 16 }}>
                  {u.is_active ? 
                    <span style={{ color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircle size={16}/> نشط</span> : 
                    <span style={{ color: 'var(--color-error)', display: 'flex', alignItems: 'center', gap: 4 }}><XCircle size={16}/> معطل</span>
                  }
                </td>
                <td style={{ padding: 16 }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => { setEditingUser(u); setShowUserModal(true); }} style={{ background: 'transparent', border: 'none', color: 'var(--color-primary)', cursor: 'pointer' }}><Edit size={18} /></button>
                    <button onClick={() => handleDeleteUser(u.id)} style={{ background: 'transparent', border: 'none', color: 'var(--color-error)', cursor: 'pointer' }}><Trash2 size={18} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Role Modal */}
      {showRoleModal && (
        <RoleModal 
          role={editingRole} 
          availablePermissions={availablePermissions}
          onClose={() => setShowRoleModal(false)}
          onSave={fetchData}
          token={token}
        />
      )}

      {/* User Modal */}
      {showUserModal && (
        <UserModal 
          user={editingUser} 
          roles={roles}
          availablePermissions={availablePermissions}
          onClose={() => setShowUserModal(false)}
          onSave={fetchData}
          token={token}
        />
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


// --- Modal Components Below ---

function RoleModal({ role, availablePermissions, onClose, onSave, token }) {
  const [name, setName] = useState(role ? role.name : '');
  const [desc, setDesc] = useState(role ? role.description : '');
  const [perms, setPerms] = useState(role ? role.permissions : []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const togglePerm = (pId) => {
    if (perms.includes(pId)) setPerms(perms.filter(p => p !== pId));
    else setPerms([...perms, pId]);
  };

  const handleSave = async () => {
    if (!name) return setError('الرجاء إدخال اسم الدور');
    setLoading(true);
    try {
      const url = role ? `${API}/admin/roles/${role.id}` : `${API}/admin/roles`;
      const method = role ? 'PUT' : 'POST';
      
      const res = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, description: desc, permissions: perms })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error');
      onSave();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalBase title={role ? 'تعديل الدور' : 'إضافة دور جديد'} onClose={onClose}>
      {error && <div style={{ color: 'var(--color-error)', marginBottom: 10 }}>{error}</div>}
      <div style={{ marginBottom: 15 }}>
        <label style={{ display: 'block', marginBottom: 5 }}>اسم الدور</label>
        <input value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
      </div>
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', marginBottom: 5 }}>الوصف</label>
        <input value={desc} onChange={e => setDesc(e.target.value)} style={inputStyle} />
      </div>
      
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', marginBottom: 10, fontWeight: 'bold' }}>الصلاحيات الممنوحة</label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {availablePermissions.map(p => (
            <div key={p.id} onClick={() => togglePerm(p.id)} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: 'var(--bg-neutral)', padding: 10, borderRadius: 8, cursor: 'pointer', border: perms.includes(p.id) ? '1px solid var(--color-primary)' : '1px solid var(--border)' }}>
              <input type="checkbox" checked={perms.includes(p.id)} readOnly style={{ marginTop: 4 }} />
              <div>
                <div style={{ fontWeight: 'bold', color: perms.includes(p.id) ? 'var(--color-primary)' : 'var(--text-primary)' }}>{p.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{p.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <button onClick={onClose} style={btnCancel}>إلغاء</button>
        <button onClick={handleSave} disabled={loading} style={btnSave}>{loading ? 'جاري الحفظ...' : 'حفظ'}</button>
      </div>
    </ModalBase>
  );
}

function UserModal({ user, roles, availablePermissions, onClose, onSave, token }) {
  const [username, setUsername] = useState(user ? user.username : '');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState(user ? user.full_name : '');
  const [email, setEmail] = useState(user ? user.email || '' : '');
  const [roleId, setRoleId] = useState(user ? (user.role_id || '') : '');
  const [customPerms, setCustomPerms] = useState(user ? (user.custom_permissions || []) : []);
  const [isActive, setIsActive] = useState(user ? user.is_active : true);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const toggleCustomPerm = (pId) => {
    if (customPerms.includes(pId)) setCustomPerms(customPerms.filter(p => p !== pId));
    else setCustomPerms([...customPerms, pId]);
  };

  const handleSave = async () => {
    if (!username || !fullName) return setError('الرجاء إدخال الحقول المطلوبة');
    if (!user && !password) return setError('الرجاء إدخال كلمة المرور للمدير الجديد');
    
    setLoading(true);
    try {
      const url = user ? `${API}/admin/users/${user.id}` : `${API}/admin/users`;
      const method = user ? 'PUT' : 'POST';
      
      const payload = {
        username,
        full_name: fullName,
        email: email || null,
        role_id: roleId ? parseInt(roleId) : null,
        custom_permissions: customPerms,
        is_active: isActive
      };
      if (password) payload.password = password;

      const res = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error');
      onSave();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ModalBase title={user ? 'تعديل بيانات المدير' : 'إضافة مدير جديد'} onClose={onClose}>
      {error && <div style={{ color: 'var(--color-error)', marginBottom: 10 }}>{error}</div>}
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 15, marginBottom: 15 }}>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>اسم المستخدم *</label>
          <input value={username} onChange={e => setUsername(e.target.value)} style={inputStyle} dir="ltr" />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>الاسم الكامل *</label>
          <input value={fullName} onChange={e => setFullName(e.target.value)} style={inputStyle} />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 15, marginBottom: 15 }}>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>كلمة المرور {user ? '(اتركه فارغاً لعدم التغيير)' : '*'}</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} style={inputStyle} dir="ltr" />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 5 }}>البريد الإلكتروني</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} style={inputStyle} dir="ltr" />
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
        <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} id="isActive" />
        <label htmlFor="isActive" style={{ cursor: 'pointer' }}>حساب مفعل (يسمح له بتسجيل الدخول)</label>
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 15, marginBottom: 15 }}>
        <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>الدور (Role)</label>
        <select value={roleId} onChange={e => setRoleId(e.target.value)} style={inputStyle}>
          <option value="">-- مستخدم مخصص (بدون دور) --</option>
          {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>
        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 5 }}>
          إذا تم اختيار دور معين، سيحصل المدير على صلاحيات هذا الدور.
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', marginBottom: 10, fontWeight: 'bold' }}>صلاحيات إضافية / مخصصة</label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, maxHeight: 150, overflowY: 'auto', paddingRight: 5 }}>
          {availablePermissions.map(p => {
            const inRole = roleId && roles.find(r => r.id === parseInt(roleId))?.permissions?.includes(p.id);
            return (
              <div key={p.id} onClick={() => !inRole && toggleCustomPerm(p.id)} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, background: 'var(--bg-neutral)', padding: 10, borderRadius: 8, cursor: inRole ? 'not-allowed' : 'pointer', opacity: inRole ? 0.5 : 1 }}>
                <input type="checkbox" checked={inRole || customPerms.includes(p.id)} readOnly style={{ marginTop: 4 }} />
                <div>
                  <div style={{ fontWeight: 'bold' }}>{p.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{inRole ? '(موروثة من الدور)' : p.description}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <button onClick={onClose} style={btnCancel}>إلغاء</button>
        <button onClick={handleSave} disabled={loading} style={btnSave}>{loading ? 'جاري الحفظ...' : 'حفظ'}</button>
      </div>
    </ModalBase>
  );
}


// Shared Styles & Utils
function ModalBase({ title, children, onClose }) {
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
      <div style={{ background: 'var(--bg-paper)', width: 600, maxWidth: '90%', borderRadius: 12, padding: 24, boxShadow: 'var(--shadow-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
        <h3 style={{ margin: '0 0 20px 0' }}>{title}</h3>
        {children}
      </div>
    </div>
  );
}

const inputStyle = {
  width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border-strong)', background: 'var(--bg-default)', color: 'var(--text-primary)', outline: 'none'
};

const btnCancel = {
  background: 'transparent', border: '1px solid var(--border-strong)', color: 'var(--text-primary)', padding: '8px 16px', borderRadius: 8, cursor: 'pointer'
};

const btnSave = {
  background: 'var(--primary)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontWeight: 'bold'
};
