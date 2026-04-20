import React, { useState, useEffect } from 'react';
import { Loader2, RefreshCw, X } from 'lucide-react';
import { api } from '@/services/api';

interface Task {
  id: string;
  type: string;
  status: string;
  created_at: string;
  progress?: number;
}

export default function TasksTab() {
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await api.get('/admin/tasks');
      setTasks(response.data?.tasks || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-900/50 text-green-400';
      case 'running': return 'bg-blue-900/50 text-blue-400';
      case 'pending': return 'bg-yellow-900/50 text-yellow-400';
      case 'failed': return 'bg-red-900/50 text-red-400';
      default: return 'bg-zinc-700 text-zinc-400';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader2 className="w-8 h-8 text-pink-500 animate-spin" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">任务管理</h2>
          <p className="text-zinc-400 mt-1">查看异步任务状态</p>
        </div>
        <button onClick={fetchTasks} className="p-2 hover:bg-zinc-800 rounded-lg">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">任务ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">类型</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">进度</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {tasks.map((task) => (
              <tr key={task.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-zinc-200 font-mono text-sm">{task.id}</td>
                <td className="px-4 py-3 text-zinc-400">{task.type}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-zinc-700 rounded-full overflow-hidden">
                      <div className="h-full bg-pink-500 transition-all" style={{ width: `${task.progress || 0}%` }} />
                    </div>
                    <span className="text-zinc-400 text-sm">{task.progress || 0}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{new Date(task.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-zinc-500">暂无任务数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}