import React, { useState, useEffect } from 'react';
import { Search, Eye, Loader2, RefreshCw, X } from 'lucide-react';
import { api } from '@/services/api';

interface Order {
  id: string;
  user_id: string;
  user_email?: string;
  amount: number;
  currency: string;
  status: string;
  payment_method: string;
  created_at: string;
}

export default function OrdersTab() {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState<Order[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/api/orders');
      setOrders(response.data || []);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      setMessage({ type: 'error', text: '加载订单失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchOrders();
      return;
    }
    setLoading(true);
    try {
      const response = await api.get('/admin/api/orders', { params: { search: searchQuery } });
      setOrders(response.data || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-900/50 text-green-400';
      case 'pending': return 'bg-yellow-900/50 text-yellow-400';
      case 'failed': return 'bg-red-900/50 text-red-400';
      case 'refunded': return 'bg-zinc-700 text-zinc-400';
      default: return 'bg-zinc-700 text-zinc-400';
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
          <h2 className="text-2xl font-bold text-white">订单管理</h2>
          <p className="text-zinc-400 mt-1">查看和管理支付订单</p>
        </div>
        <button onClick={fetchOrders} className="p-2 hover:bg-zinc-800 rounded-lg">
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
            placeholder="搜索订单..."
            className="w-full pl-10 pr-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
          />
        </div>
        <button onClick={handleSearch} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">搜索</button>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">订单ID</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">用户</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">金额</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">支付方式</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">状态</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">创建时间</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-zinc-200 font-mono text-sm">{order.id.slice(0, 12)}...</td>
                <td className="px-4 py-3 text-zinc-400">{order.user_email || order.user_id}</td>
                <td className="px-4 py-3 text-white font-medium">
                  {order.currency === 'USD' ? '$' : ''}{order.amount.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-zinc-400">{order.payment_method}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(order.status)}`}>
                    {order.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-zinc-400 text-sm">{new Date(order.created_at).toLocaleString()}</td>
                <td className="px-4 py-3">
                  <button className="p-2 hover:bg-zinc-700 rounded-lg text-zinc-400" title="查看详情">
                    <Eye className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-zinc-500">暂无订单数据</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}