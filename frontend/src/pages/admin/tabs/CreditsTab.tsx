import React, { useState, useEffect } from 'react';
import { Loader2, Save, Plus, Trash2, Edit, Users, Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/services/api';

interface CreditConfig {
  message_cost: number;
  voice_cost: number;
  image_cost: number;
  video_cost: number;
  voice_call_per_minute: number;
  signup_bonus_credits: number;
  premium_monthly_credits: number;
}

interface CreditPack {
  id: string;
  pack_id?: string;
  name: string;
  credits: number;
  price_cents: number;
  bonus_credits: number;
  total_credits: number;
  is_popular: boolean;
  is_active: boolean;
  display_order: number;
}

interface SubscriptionPlan {
  period: string;
  price_cents: number;
  monthly_equivalent_cents: number;
  discount_percent: number;
  is_active: boolean;
  display_order: number;
}

interface Transaction {
  id: number;
  user_id: string;
  transaction_type: string;
  amount: number;
  balance_after: number;
  usage_type: string | null;
  credit_source: string | null;
  description: string | null;
  created_at: string;
}

interface BatchResult {
  user_id: string;
  success: boolean;
  error: string | null;
  new_balance: number | null;
}

export default function CreditsTab() {
  const [activeSection, setActiveSection] = useState<'config' | 'plans' | 'packs' | 'adjust' | 'transactions'>('config');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [config, setConfig] = useState<CreditConfig>({
    message_cost: 0.1,
    voice_cost: 0.2,
    image_cost: 2,
    video_cost: 4,
    voice_call_per_minute: 3,
    signup_bonus_credits: 10,
    premium_monthly_credits: 100,
  });

  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [packs, setPacks] = useState<CreditPack[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionsTotal, setTransactionsTotal] = useState(0);

  const [adjustUserId, setAdjustUserId] = useState('');
  const [adjustAmount, setAdjustAmount] = useState('');
  const [adjustDescription, setAdjustDescription] = useState('');

  const [adjustMode, setAdjustMode] = useState<'single' | 'batch'>('single');
  const [batchUserIds, setBatchUserIds] = useState('');
  const [batchAmount, setBatchAmount] = useState('');
  const [batchDescription, setBatchDescription] = useState('');
  const [batchResults, setBatchResults] = useState<BatchResult[]>([]);
  const [batchLoading, setBatchLoading] = useState(false);

  const [editingPack, setEditingPack] = useState<CreditPack | null>(null);
  const [newPack, setNewPack] = useState<Partial<CreditPack>>({
    pack_id: '',
    name: '',
    credits: 100,
    price_cents: 999,
    bonus_credits: 0,
    is_popular: false,
    display_order: 1,
  });
  const [showNewPackForm, setShowNewPackForm] = useState(false);

  useEffect(() => {
    loadData();
  }, [activeSection]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeSection === 'config') {
        const res = await api.get('/admin/credits/config');
        setConfig(res.data);
      } else if (activeSection === 'plans') {
        const res = await api.get('/admin/credits/plans');
        setPlans(res.data);
      } else if (activeSection === 'packs') {
        const res = await api.get('/admin/credits/packs');
        setPacks(res.data);
      } else if (activeSection === 'transactions') {
        const res = await api.get('/admin/credits/transactions?limit=50');
        setTransactions(res.data.transactions);
        setTransactionsTotal(res.data.total);
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to load data' });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await api.put('/admin/credits/config', config);
      setMessage({ type: 'success', text: 'Configuration saved' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const updatePlan = async (period: string, data: Partial<SubscriptionPlan>) => {
    try {
      await api.put(`/admin/credits/plans/${period}`, data);
      setMessage({ type: 'success', text: 'Plan updated' });
      loadData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update plan' });
    }
  };

  const createPack = async () => {
    if (!newPack.pack_id || !newPack.name || !newPack.credits || !newPack.price_cents) {
      setMessage({ type: 'error', text: 'Please fill all required fields' });
      return;
    }
    try {
      await api.post('/admin/credits/packs', {
        pack_id: newPack.pack_id,
        name: newPack.name,
        credits: newPack.credits,
        price_cents: newPack.price_cents,
        bonus_credits: newPack.bonus_credits || 0,
        is_popular: newPack.is_popular || false,
        display_order: newPack.display_order || 1,
      });
      setMessage({ type: 'success', text: 'Pack created' });
      setShowNewPackForm(false);
      setNewPack({ pack_id: '', name: '', credits: 100, price_cents: 999, bonus_credits: 0, is_popular: false, display_order: 1 });
      loadData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to create pack' });
    }
  };

  const updatePack = async (packId: string, data: Partial<CreditPack>) => {
    try {
      await api.put(`/admin/credits/packs/${packId}`, data);
      setMessage({ type: 'success', text: 'Pack updated' });
      setEditingPack(null);
      loadData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update pack' });
    }
  };

  const deletePack = async (packId: string) => {
    if (!confirm('Are you sure you want to delete this pack?')) return;
    try {
      await api.delete(`/admin/credits/packs/${packId}`);
      setMessage({ type: 'success', text: 'Pack deleted' });
      loadData();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to delete pack' });
    }
  };

  const adjustCredits = async () => {
    if (!adjustUserId || !adjustAmount || !adjustDescription) {
      setMessage({ type: 'error', text: 'Please fill all fields' });
      return;
    }
    try {
      await api.post('/admin/credits/adjust', {
        user_id: adjustUserId,
        amount: parseFloat(adjustAmount),
        description: adjustDescription,
      });
      setMessage({ type: 'success', text: 'Credits adjusted' });
      setAdjustUserId('');
      setAdjustAmount('');
      setAdjustDescription('');
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to adjust credits' });
    }
  };

  const handleBatchAdjust = async () => {
    const userIds = batchUserIds
      .split(/[\n,]+/)
      .map(id => id.trim())
      .filter(id => id.length > 0);

    if (userIds.length === 0) {
      setMessage({ type: 'error', text: 'Please enter at least one user ID' });
      return;
    }

    if (!batchAmount || !batchDescription) {
      setMessage({ type: 'error', text: 'Please fill amount and description' });
      return;
    }

    setBatchLoading(true);
    setBatchResults([]);

    try {
      const res = await api.post('/admin/credits/batch-adjust', {
        user_ids: userIds,
        amount: parseFloat(batchAmount),
        description: batchDescription,
      });

      setBatchResults(res.data.results || []);
      setMessage({
        type: 'success',
        text: `Batch adjustment completed: ${res.data.success_count} success, ${res.data.failure_count} failures`,
      });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to batch adjust credits' });
    } finally {
      setBatchLoading(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setBatchUserIds(text);
    };
    reader.readAsText(file);
  };

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Credit System Management</h2>
        <div className="flex gap-2">
          {(['config', 'plans', 'packs', 'adjust', 'transactions'] as const).map((section) => (
            <button
              key={section}
              onClick={() => setActiveSection(section)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                activeSection === section
                  ? 'bg-pink-600 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              {section === 'config' && '消耗配置'}
              {section === 'plans' && '订阅计划'}
              {section === 'packs' && '充值包'}
              {section === 'adjust' && '用户调整'}
              {section === 'transactions' && '交易记录'}
            </button>
          ))}
        </div>
      </div>

      {message && (
        <div className={`p-3 rounded-lg flex items-center justify-between ${message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'}`}>
          {message.text}
          <button onClick={() => setMessage(null)} className="p-1 hover:bg-white/10 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
        </div>
      ) : (
        <>
          {activeSection === 'config' && (
            <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">消耗配置</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">文本消息消耗</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.message_cost}
                    onChange={(e) => setConfig({ ...config, message_cost: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">语音生成消耗</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.voice_cost}
                    onChange={(e) => setConfig({ ...config, voice_cost: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">图片生成消耗</label>
                  <input
                    type="number"
                    value={config.image_cost}
                    onChange={(e) => setConfig({ ...config, image_cost: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">视频生成消耗</label>
                  <input
                    type="number"
                    value={config.video_cost}
                    onChange={(e) => setConfig({ ...config, video_cost: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">实时通话/分钟</label>
                  <input
                    type="number"
                    value={config.voice_call_per_minute}
                    onChange={(e) => setConfig({ ...config, voice_call_per_minute: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">注册奖励</label>
                  <input
                    type="number"
                    value={config.signup_bonus_credits}
                    onChange={(e) => setConfig({ ...config, signup_bonus_credits: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm text-zinc-400 mb-1">订阅每月credits</label>
                  <input
                    type="number"
                    value={config.premium_monthly_credits}
                    onChange={(e) => setConfig({ ...config, premium_monthly_credits: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={saveConfig}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save
                </button>
              </div>
            </div>
          )}

          {activeSection === 'plans' && (
            <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">订阅计划</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-zinc-400 border-b border-zinc-800">
                      <th className="pb-3">周期</th>
                      <th className="pb-3">总价</th>
                      <th className="pb-3">月均</th>
                      <th className="pb-3">折扣</th>
                      <th className="pb-3">状态</th>
                    </tr>
                  </thead>
                  <tbody className="text-white">
                    {plans.map((plan) => (
                      <tr key={plan.period} className="border-b border-zinc-800/50">
                        <td className="py-3">{plan.period}</td>
                        <td className="py-3">
                          <input
                            type="number"
                            value={plan.price_cents}
                            onChange={(e) => updatePlan(plan.period, { price_cents: parseInt(e.target.value) })}
                            className="w-24 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-sm"
                          />
                        </td>
                        <td className="py-3">{formatPrice(plan.monthly_equivalent_cents)}</td>
                        <td className="py-3">{plan.discount_percent}%</td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs ${plan.is_active ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                            {plan.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeSection === 'packs' && (
            <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Credit充值包</h3>
                <button
                  onClick={() => setShowNewPackForm(!showNewPackForm)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm"
                >
                  <Plus className="w-4 h-4" /> 新增
                </button>
              </div>

              {showNewPackForm && (
                <div className="mb-4 p-4 bg-zinc-800 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <input
                      type="text"
                      placeholder="Pack ID (pack_100)"
                      value={newPack.pack_id}
                      onChange={(e) => setNewPack({ ...newPack, pack_id: e.target.value })}
                      className="px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white text-sm"
                    />
                    <input
                      type="text"
                      placeholder="Name"
                      value={newPack.name}
                      onChange={(e) => setNewPack({ ...newPack, name: e.target.value })}
                      className="px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Credits"
                      value={newPack.credits}
                      onChange={(e) => setNewPack({ ...newPack, credits: parseInt(e.target.value) })}
                      className="px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white text-sm"
                    />
                    <input
                      type="number"
                      placeholder="Price (cents)"
                      value={newPack.price_cents}
                      onChange={(e) => setNewPack({ ...newPack, price_cents: parseInt(e.target.value) })}
                      className="px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-white text-sm"
                    />
                  </div>
                  <div className="mt-3 flex gap-2">
                    <label className="flex items-center gap-2 text-sm text-zinc-300">
                      <input
                        type="checkbox"
                        checked={newPack.is_popular}
                        onChange={(e) => setNewPack({ ...newPack, is_popular: e.target.checked })}
                        className="rounded"
                      />
                      Popular
                    </label>
                    <button onClick={createPack} className="px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm">
                      Create
                    </button>
                    <button onClick={() => setShowNewPackForm(false)} className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded text-sm">
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-zinc-400 border-b border-zinc-800">
                      <th className="pb-3">ID</th>
                      <th className="pb-3">名称</th>
                      <th className="pb-3">Credits</th>
                      <th className="pb-3">价格</th>
                      <th className="pb-3">热门</th>
                      <th className="pb-3">状态</th>
                      <th className="pb-3">操作</th>
                    </tr>
                  </thead>
                  <tbody className="text-white">
                    {packs.map((pack) => (
                      <tr key={pack.id} className="border-b border-zinc-800/50">
                        <td className="py-3 text-sm text-zinc-400">{pack.id}</td>
                        <td className="py-3">{pack.name}</td>
                        <td className="py-3">{pack.credits}</td>
                        <td className="py-3">{formatPrice(pack.price_cents)}</td>
                        <td className="py-3">
                          {pack.is_popular && <span className="px-2 py-0.5 bg-pink-900/50 text-pink-300 rounded text-xs">Popular</span>}
                        </td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs ${pack.is_active ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                            {pack.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="py-3">
                          <div className="flex gap-1">
                            <button
                              onClick={() => updatePack(pack.pack_id || pack.id, { is_active: !pack.is_active })}
                              className="p-1 hover:bg-zinc-700 rounded"
                            >
                              <Edit className="w-4 h-4 text-zinc-400" />
                            </button>
                            <button
                              onClick={() => deletePack(pack.pack_id || pack.id)}
                              className="p-1 hover:bg-zinc-700 rounded"
                            >
                              <Trash2 className="w-4 h-4 text-red-400" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeSection === 'adjust' && (
            <div className="space-y-6">
              <div className="flex gap-2">
                <button
                  onClick={() => setAdjustMode('single')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium ${
                    adjustMode === 'single' ? 'bg-pink-600 text-white' : 'bg-zinc-800 text-zinc-400'
                  }`}
                >
                  单用户调整
                </button>
                <button
                  onClick={() => setAdjustMode('batch')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
                    adjustMode === 'batch' ? 'bg-pink-600 text-white' : 'bg-zinc-800 text-zinc-400'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  批量调整
                </button>
              </div>

              {adjustMode === 'single' ? (
                <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">用户Credit调整</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm text-zinc-400 mb-1">用户ID</label>
                      <input
                        type="text"
                        value={adjustUserId}
                        onChange={(e) => setAdjustUserId(e.target.value)}
                        placeholder="User ID (UUID)"
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-zinc-400 mb-1">调整数量</label>
                      <input
                        type="number"
                        step="0.1"
                        value={adjustAmount}
                        onChange={(e) => setAdjustAmount(e.target.value)}
                        placeholder="+100 or -50"
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-zinc-400 mb-1">原因</label>
                      <input
                        type="text"
                        value={adjustDescription}
                        onChange={(e) => setAdjustDescription(e.target.value)}
                        placeholder="Adjustment reason"
                        className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        onClick={adjustCredits}
                        className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium"
                      >
                        调整
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">批量Credit调整</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <label className="text-sm text-zinc-400">用户ID列表</label>
                          <label className="flex items-center gap-2 text-xs text-zinc-500 cursor-pointer hover:text-zinc-300">
                            <Upload className="w-3 h-3" />
                            <span>上传CSV/TXT</span>
                            <input
                              type="file"
                              accept=".csv,.txt"
                              onChange={handleFileUpload}
                              className="hidden"
                            />
                          </label>
                        </div>
                        <textarea
                          value={batchUserIds}
                          onChange={(e) => setBatchUserIds(e.target.value)}
                          placeholder="每行一个用户ID，或用逗号分隔&#10;支持最多100个用户"
                          rows={6}
                          className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm font-mono resize-none"
                        />
                        <p className="text-xs text-zinc-500 mt-1">
                          {batchUserIds.split(/[\n,]+/).filter(id => id.trim()).length} 个用户
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm text-zinc-400 mb-1">调整数量</label>
                          <input
                            type="number"
                            step="0.1"
                            value={batchAmount}
                            onChange={(e) => setBatchAmount(e.target.value)}
                            placeholder="+100 or -50"
                            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-zinc-400 mb-1">原因</label>
                          <input
                            type="text"
                            value={batchDescription}
                            onChange={(e) => setBatchDescription(e.target.value)}
                            placeholder="Adjustment reason"
                            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white"
                          />
                        </div>
                      </div>
                      <button
                        onClick={handleBatchAdjust}
                        disabled={batchLoading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm font-medium disabled:opacity-50"
                      >
                        {batchLoading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            处理中...
                          </>
                        ) : (
                          <>
                            <Users className="w-4 h-4" />
                            批量调整
                          </>
                        )}
                      </button>
                    </div>

                    {batchResults.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-zinc-400 mb-2">处理结果</h4>
                        <div className="bg-zinc-800 rounded-lg max-h-80 overflow-auto">
                          <table className="w-full text-sm">
                            <thead className="sticky top-0 bg-zinc-700">
                              <tr>
                                <th className="px-3 py-2 text-left text-zinc-300">用户ID</th>
                                <th className="px-3 py-2 text-left text-zinc-300">状态</th>
                                <th className="px-3 py-2 text-right text-zinc-300">新余额</th>
                              </tr>
                            </thead>
                            <tbody>
                              {batchResults.map((result, idx) => (
                                <tr key={idx} className="border-t border-zinc-700">
                                  <td className="px-3 py-2 font-mono text-xs text-zinc-300">
                                    {result.user_id}
                                  </td>
                                  <td className="px-3 py-2">
                                    {result.success ? (
                                      <span className="flex items-center gap-1 text-green-400">
                                        <CheckCircle className="w-3 h-3" />
                                        成功
                                      </span>
                                    ) : (
                                      <span className="flex items-center gap-1 text-red-400">
                                        <AlertCircle className="w-3 h-3" />
                                        {result.error || '失败'}
                                      </span>
                                    )}
                                  </td>
                                  <td className="px-3 py-2 text-right text-zinc-300">
                                    {result.new_balance ?? '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeSection === 'transactions' && (
            <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">交易记录 ({transactionsTotal})</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-zinc-400 border-b border-zinc-800">
                      <th className="pb-3">时间</th>
                      <th className="pb-3">用户ID</th>
                      <th className="pb-3">类型</th>
                      <th className="pb-3">金额</th>
                      <th className="pb-3">余额</th>
                      <th className="pb-3">用途</th>
                      <th className="pb-3">描述</th>
                    </tr>
                  </thead>
                  <tbody className="text-white">
                    {transactions.map((tx) => (
                      <tr key={tx.id} className="border-b border-zinc-800/50">
                        <td className="py-3 text-sm text-zinc-400">
                          {new Date(tx.created_at).toLocaleString()}
                        </td>
                        <td className="py-3">{tx.user_id}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            tx.transaction_type === 'usage' ? 'bg-red-900/50 text-red-300' :
                            tx.transaction_type === 'signup_bonus' ? 'bg-green-900/50 text-green-300' :
                            tx.transaction_type === 'purchase' ? 'bg-blue-900/50 text-blue-300' :
                            'bg-zinc-800 text-zinc-300'
                          }`}>
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td className={`py-3 ${tx.amount >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {tx.amount >= 0 ? '+' : ''}{tx.amount}
                        </td>
                        <td className="py-3">{tx.balance_after}</td>
                        <td className="py-3 text-zinc-400">{tx.usage_type || '-'}</td>
                        <td className="py-3 text-zinc-400 text-sm truncate max-w-xs">{tx.description || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
