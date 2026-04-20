import React, { useState, useEffect } from 'react';
import { Search, Ban, CheckCircle, Loader2, RefreshCw, X } from 'lucide-react';
import { api } from '@/services/api';

interface User {
  id: string;
  email: string;
  display_name?: string;
  is_admin: boolean;
  is_banned: boolean;
  created_at: string;
  subscription_tier?: string;
}

export default function UsersTab() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/api/users');
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setMessage({ type: 'error', text: '加载用户失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchUsers();
      return;
    }
    setLoading(true);
    try {
      const response = await api.get('/admin/api/users', { params: { search: searchQuery } });
      setUsers(response.data || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleBan = async (userId: string, currentlyBanned: boolean) => {
    try {
      await api.post(`/admin/api/users/${userId}/${currentlyBanned ? 'unban' : 'ban'}`);
      setMessage({ type: 'success', text: currentlyBanned ? '已解封用户' : '已封禁用户' });
      fetchUsers();
    } catch (error) {
      setMessage({ type: 'error', text: '操作失败' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">用户管理</h2>
          <p className="text-zinc-400 mt-1">管理平台用户和权限</p>
        </div>
        <button onClick={fetchUsers} className="p-2 hover:bg-zinc-800 rounded-lg">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
        }`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索用户..."
            className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        </div>
        <button onClick={handleSearch} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">搜索</button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">用户</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">角色</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">订阅</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">注册时间</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3">
                  <div>
                    <p className="text-white font-medium">{user.display_name || user.email}</p>
                    <p className="text-zinc-500 text-sm">{user.email}</p>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {user.is_admin ? (
                    <span className="px-2 py-1 rounded-full text-xs bg-pink-900/50 text-pink-400">管理员</span>
                  ) : (
                    <span className="px-2 py-1 rounded-full text-xs bg-zinc-700 text-zinc-400">用户</span>
                  )}
                </td>
                <td className="px-4 py-3 text-zinc-400">{user.subscription_tier || 'free'}</td>
                <td className="px-4 py-3">
                  {user.is_banned ? (
                    <span className="px-2 py-1 rounded-full text-xs bg-red-900/50 text-red-400">已封禁</span>
                  ) : (
                    <span className="px-2 py-1 rounded-full text-xs bg-green-900/50 text-green-400">正常</span>
                  )}
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{new Date(user.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => handleToggleBan(user.id, user.is_banned)}
                      className={`p-2 hover:bg-zinc-700 rounded-lg ${user.is_banned ? 'text-green-400' : 'text-red-400'}`}
                      title={user.is_banned ? '解封' : '封禁'}
                    >
                      {user.is_banned ? <CheckCircle className="w-4 h-4" /> : <Ban className="w-4 h-4" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-zinc-500">暂无用户数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}