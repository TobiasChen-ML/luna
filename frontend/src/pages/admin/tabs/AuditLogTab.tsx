import React, { useState, useEffect } from 'react';
import { 
  Search, RefreshCw, Loader2, X, ChevronLeft, ChevronRight, 
  FileText, Filter, Download, Eye
} from 'lucide-react';
import { api } from '@/services/api';

interface AuditLog {
  id: number;
  admin_id: string;
  admin_email: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  old_value: string | null;
  new_value: string | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata: string | null;
  created_at: string;
}

interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

const ACTION_LABELS: Record<string, string> = {
  character_create: '创建角色',
  character_update: '更新角色',
  character_delete: '删除角色',
  character_batch_delete: '批量删除角色',
  character_approve: '审核通过',
  character_reject: '审核拒绝',
  character_regenerate_images: '重新生成图片',
  credit_config_update: '更新积分配置',
  credit_adjust: '调整积分',
  credit_batch_adjust: '批量调整积分',
  credit_pack_create: '创建积分包',
  credit_pack_update: '更新积分包',
  credit_pack_delete: '删除积分包',
  subscription_plan_update: '更新订阅计划',
  user_ban: '封禁用户',
  user_unban: '解封用户',
  prompt_create: '创建提示词',
  prompt_update: '更新提示词',
  prompt_delete: '删除提示词',
  script_create: '创建剧本',
  script_update: '更新剧本',
  script_delete: '删除剧本',
  config_update: '更新配置',
  api_key_create: '创建API密钥',
  api_key_revoke: '撤销API密钥',
};

export default function AuditLogTab() {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  const [filters, setFilters] = useState({
    admin_id: '',
    action: '',
    resource_type: '',
    resource_id: '',
    start_date: '',
    end_date: '',
  });
  const [showFilters, setShowFilters] = useState(false);
  const [availableActions, setAvailableActions] = useState<string[]>([]);
  const [resourceTypes, setResourceTypes] = useState<string[]>([]);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    loadActions();
    loadResourceTypes();
  }, []);

  useEffect(() => {
    loadLogs();
  }, [page, limit]);

  const loadActions = async () => {
    try {
      const response = await api.get('/admin/audit/actions');
      setAvailableActions(response.data || []);
    } catch (error) {
      console.error('Failed to load actions:', error);
    }
  };

  const loadResourceTypes = async () => {
    try {
      const response = await api.get('/admin/audit/resource-types');
      setResourceTypes(response.data || []);
    } catch (error) {
      console.error('Failed to load resource types:', error);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        limit,
        offset: (page - 1) * limit,
      };
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params[key] = value;
        }
      });

      const response = await api.get<AuditLogListResponse>('/admin/audit/logs', { params });
      setLogs(response.data.logs || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
      setMessage({ type: 'error', text: '加载审计日志失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    setPage(1);
    loadLogs();
  };

  const clearFilters = () => {
    setFilters({
      admin_id: '',
      action: '',
      resource_type: '',
      resource_id: '',
      start_date: '',
      end_date: '',
    });
    setPage(1);
  };

  const totalPages = Math.ceil(total / limit);

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const formatJsonValue = (value: string | null) => {
    if (!value) return '-';
    try {
      const parsed = JSON.parse(value);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return value;
    }
  };

  const exportToCsv = () => {
    const headers = ['时间', '管理员', '操作', '资源类型', '资源ID', 'IP地址'];
    const rows = logs.map(log => [
      formatDateTime(log.created_at),
      log.admin_email,
      ACTION_LABELS[log.action] || log.action,
      log.resource_type || '-',
      log.resource_id || '-',
      log.ip_address || '-',
    ]);
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">操作日志</h2>
          <p className="text-zinc-400 mt-1">查看管理员操作记录</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
              showFilters ? 'bg-pink-600 text-white' : 'bg-zinc-800 text-zinc-400'
            }`}
          >
            <Filter className="w-4 h-4" />
            筛选
          </button>
          <button
            onClick={exportToCsv}
            disabled={logs.length === 0}
            className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            导出
          </button>
          <button onClick={loadLogs} className="p-2 hover:bg-zinc-800 rounded-lg">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
        }`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {showFilters && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm text-zinc-400 mb-1">操作类型</label>
              <select
                value={filters.action}
                onChange={(e) => handleFilterChange('action', e.target.value)}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              >
                <option value="">全部</option>
                {availableActions.map(action => (
                  <option key={action} value={action}>
                    {ACTION_LABELS[action] || action}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">资源类型</label>
              <select
                value={filters.resource_type}
                onChange={(e) => handleFilterChange('resource_type', e.target.value)}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              >
                <option value="">全部</option>
                {resourceTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">资源ID</label>
              <input
                type="text"
                value={filters.resource_id}
                onChange={(e) => handleFilterChange('resource_id', e.target.value)}
                placeholder="输入资源ID"
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">管理员ID</label>
              <input
                type="text"
                value={filters.admin_id}
                onChange={(e) => handleFilterChange('admin_id', e.target.value)}
                placeholder="输入管理员ID"
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">开始日期</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange('start_date', e.target.value)}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-1">结束日期</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange('end_date', e.target.value)}
                className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm"
              />
            </div>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm"
            >
              清除
            </button>
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm"
            >
              应用
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
        </div>
      ) : (
        <>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-zinc-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">时间</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">管理员</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">操作</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">资源</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">IP地址</th>
                    <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-800">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-zinc-800/30">
                      <td className="px-4 py-3 text-sm text-zinc-400">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white">{log.admin_email}</p>
                        <p className="text-zinc-500 text-xs">{log.admin_id}</p>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-pink-900/30 text-pink-300 rounded text-xs">
                          {ACTION_LABELS[log.action] || log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-white">{log.resource_type || '-'}</p>
                        <p className="text-zinc-500 text-xs truncate max-w-xs">{log.resource_id || '-'}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-400">{log.ip_address || '-'}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="p-2 hover:bg-zinc-700 rounded-lg"
                          title="查看详情"
                        >
                          <Eye className="w-4 h-4 text-zinc-400" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                        暂无操作日志
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-400">
                共 {total} 条记录，第 {page}/{totalPages} 页
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-50"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-4 py-2 bg-zinc-800 rounded-lg text-sm">
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-50"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 p-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">操作详情</h3>
              <button onClick={() => setSelectedLog(null)} className="p-2 hover:bg-zinc-800 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-zinc-400">时间</label>
                  <p className="text-white">{formatDateTime(selectedLog.created_at)}</p>
                </div>
                <div>
                  <label className="text-sm text-zinc-400">管理员</label>
                  <p className="text-white">{selectedLog.admin_email}</p>
                </div>
                <div>
                  <label className="text-sm text-zinc-400">操作类型</label>
                  <p className="text-white">{ACTION_LABELS[selectedLog.action] || selectedLog.action}</p>
                </div>
                <div>
                  <label className="text-sm text-zinc-400">资源类型</label>
                  <p className="text-white">{selectedLog.resource_type || '-'}</p>
                </div>
                <div>
                  <label className="text-sm text-zinc-400">资源ID</label>
                  <p className="text-white font-mono text-sm">{selectedLog.resource_id || '-'}</p>
                </div>
                <div>
                  <label className="text-sm text-zinc-400">IP地址</label>
                  <p className="text-white">{selectedLog.ip_address || '-'}</p>
                </div>
              </div>
              
              {selectedLog.old_value && (
                <div>
                  <label className="text-sm text-zinc-400 block mb-2">旧值</label>
                  <pre className="bg-zinc-800 p-3 rounded-lg text-sm text-zinc-300 overflow-auto max-h-40">
                    {formatJsonValue(selectedLog.old_value)}
                  </pre>
                </div>
              )}
              
              {selectedLog.new_value && (
                <div>
                  <label className="text-sm text-zinc-400 block mb-2">新值</label>
                  <pre className="bg-zinc-800 p-3 rounded-lg text-sm text-zinc-300 overflow-auto max-h-40">
                    {formatJsonValue(selectedLog.new_value)}
                  </pre>
                </div>
              )}

              {selectedLog.user_agent && (
                <div>
                  <label className="text-sm text-zinc-400 block mb-2">User Agent</label>
                  <p className="text-zinc-300 text-sm break-all">{selectedLog.user_agent}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
