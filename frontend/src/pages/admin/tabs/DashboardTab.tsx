import React, { useState, useEffect } from 'react';
import { Users, BookOpen, MessageSquare, TrendingUp, Loader2, FileText, MessagesSquare } from 'lucide-react';
import { api } from '@/services/api';

interface Stat {
  label: string;
  value: number | string;
  change?: number;
  icon: React.ElementType;
  color: string;
}

interface DashboardStats {
  total_users: number;
  total_characters: number;
  total_stories: number;
  total_chats: number;
  total_messages: number;
}

export default function DashboardTab() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<Stat[]>([]);
  const [recentActivities, setRecentActivities] = useState<{ action: string; user: string; time: string }[]>([]);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const dashboardRes = await api.get('/admin/dashboard');
      const data: DashboardStats = dashboardRes.data?.stats || {
        total_users: 0,
        total_characters: 0,
        total_stories: 0,
        total_chats: 0,
        total_messages: 0,
      };

      setStats([
        {
          label: '总用户数',
          value: data.total_users,
          icon: Users,
          color: 'text-blue-400',
        },
        {
          label: '角色数量',
          value: data.total_characters,
          icon: BookOpen,
          color: 'text-pink-400',
        },
        {
          label: '故事数量',
          value: data.total_stories,
          icon: FileText,
          color: 'text-purple-400',
        },
        {
          label: '会话总数',
          value: data.total_chats,
          icon: MessageSquare,
          color: 'text-green-400',
        },
        {
          label: '消息总数',
          value: data.total_messages,
          icon: MessagesSquare,
          color: 'text-orange-400',
        },
      ]);

      setRecentActivities([
        { action: '系统运行正常', user: 'system', time: '刚刚' },
      ]);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
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
      <div>
        <h2 className="text-2xl font-bold text-white">仪表盘</h2>
        <p className="text-zinc-400 mt-1">系统概览和统计数据</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => (
          <div
            key={index}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6"
          >
            <div className="flex items-center justify-between">
              <stat.icon className={`w-8 h-8 ${stat.color}`} />
            </div>
            <div className="mt-4">
              <p className="text-2xl font-bold text-white">{stat.value}</p>
              <p className="text-zinc-400 text-sm mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">最近活动</h3>
          <div className="space-y-3">
            {recentActivities.length > 0 ? (
              recentActivities.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0"
                >
                  <div>
                    <p className="text-zinc-200 text-sm">{activity.action}</p>
                    <p className="text-zinc-500 text-xs">{activity.user}</p>
                  </div>
                  <span className="text-zinc-500 text-xs">{activity.time}</span>
                </div>
              ))
            ) : (
              <p className="text-zinc-500 text-sm">暂无活动记录</p>
            )}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">系统状态</h3>
          <div className="space-y-3">
            {[
              { name: 'API服务', status: 'running', color: 'text-green-400' },
              { name: '数据库', status: 'running', color: 'text-green-400' },
              { name: '存储服务', status: 'running', color: 'text-green-400' },
              { name: 'LLM服务', status: 'running', color: 'text-green-400' },
            ].map((service, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0"
              >
                <span className="text-zinc-200">{service.name}</span>
                <span className={`flex items-center gap-2 text-sm ${service.color}`}>
                  <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                  {service.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
