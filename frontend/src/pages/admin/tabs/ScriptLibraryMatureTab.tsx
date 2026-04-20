import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Loader2, X, Check, AlertTriangle, Filter,
  ChevronDown, Eye, EyeOff, ShieldAlert, TrendingUp,
  ArchiveX, CheckCircle, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { api } from '@/services/api';

interface ScriptItem {
  id: string;
  title: string;
  title_en?: string;
  summary?: string;
  age_rating: string;
  status: string;
  relation_types: string | string[];
  emotion_tones: string | string[];
  era?: string;
  character_gender?: string;
  popularity: number;
  created_at: string;
}

interface Stats {
  total: number;
  by_age_rating: Record<string, number>;
  by_status: Record<string, number>;
  mature_top_relations: { relation_types: string; count: number }[];
}

interface ListResponse {
  items: ScriptItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

type AgeRating = 'all' | 'mature' | '';
type StatusFilter = 'published' | 'draft' | 'archived' | '';

const AGE_RATING_LABELS: Record<string, string> = { all: '全年齡', mature: 'Mature' };
const AGE_RATING_COLORS: Record<string, string> = {
  all: 'bg-zinc-700 text-zinc-300',
  mature: 'bg-red-900/60 text-red-300 font-bold',
};
const STATUS_LABELS: Record<string, string> = {
  published: '已發布', draft: '草稿', archived: '已封存',
};
const STATUS_COLORS: Record<string, string> = {
  published: 'bg-green-900/50 text-green-400',
  draft: 'bg-zinc-700 text-zinc-400',
  archived: 'bg-zinc-800 text-zinc-500',
};

function parseJsonArray(val: string | string[] | undefined): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  try { return JSON.parse(val); } catch { return []; }
}

export default function ScriptLibraryMatureTab() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [items, setItems] = useState<ScriptItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [previewScript, setPreviewScript] = useState<ScriptItem | null>(null);

  // Filters
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [ageRatingFilter, setAgeRatingFilter] = useState<AgeRating>('mature');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('');
  const [relationFilter, setRelationFilter] = useState('');

  const pageSize = 50;

  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      const res = await api.get('/admin/script-library/stats');
      setStats(res.data);
    } catch (_err) {
      // stats are optional
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const fetchScripts = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number | undefined> = { page, page_size: pageSize };
      if (ageRatingFilter) params.age_rating = ageRatingFilter;
      if (statusFilter) params.status = statusFilter;
      if (relationFilter.trim()) params.relation_types = relationFilter.trim();
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await api.get<ListResponse>('/admin/script-library', { params });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 0);
    } catch (_err) {
      setMessage({ type: 'error', text: '載入劇本失敗' });
    } finally {
      setLoading(false);
    }
  }, [page, ageRatingFilter, statusFilter, relationFilter, searchQuery]);

  useEffect(() => { fetchStats(); }, [fetchStats]);
  useEffect(() => { fetchScripts(); }, [fetchScripts]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handlePublish = async (id: string) => {
    setSaving(true);
    try {
      await api.post(`/admin/script-library/${id}/publish`);
      showMessage('success', '已發布');
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '操作失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (id: string) => {
    setSaving(true);
    try {
      await api.post(`/admin/script-library/${id}/archive`);
      showMessage('success', '已封存');
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '操作失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleDowngrade = async (id: string) => {
    if (!confirm('確定要將此劇本從 Mature 降級為全年齡？')) return;
    setSaving(true);
    try {
      await api.post(`/admin/script-library/${id}/downgrade`);
      showMessage('success', '已降級為全年齡');
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '操作失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkPublish = async () => {
    if (!selectedIds.length) return;
    setSaving(true);
    try {
      await api.post('/admin/script-library/bulk/publish', { ids: selectedIds });
      showMessage('success', `已發布 ${selectedIds.length} 個劇本`);
      setSelectedIds([]);
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '批量操作失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkArchive = async () => {
    if (!selectedIds.length) return;
    if (!confirm(`確定要封存選中的 ${selectedIds.length} 個劇本？`)) return;
    setSaving(true);
    try {
      await api.post('/admin/script-library/bulk/archive', { ids: selectedIds });
      showMessage('success', `已封存 ${selectedIds.length} 個劇本`);
      setSelectedIds([]);
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '批量操作失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkDelete = async () => {
    if (!selectedIds.length) return;
    if (!confirm(`確定要刪除選中的 ${selectedIds.length} 個劇本？此操作無法撤銷。`)) return;
    setSaving(true);
    try {
      await api.post('/admin/script-library/bulk/delete', { ids: selectedIds });
      showMessage('success', `已刪除 ${selectedIds.length} 個劇本`);
      setSelectedIds([]);
      fetchScripts();
      fetchStats();
    } catch (_err) {
      showMessage('error', '批量刪除失敗');
    } finally {
      setSaving(false);
    }
  };

  const toggleSelect = (id: string) =>
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);

  const toggleSelectAll = () =>
    setSelectedIds(selectedIds.length === items.length ? [] : items.map(i => i.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-red-400" />
            劇本庫管理（含 Mature）
          </h2>
          <p className="text-zinc-400 mt-1">共 {total} 個劇本</p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
            showFilters ? 'bg-purple-600 text-white' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
          }`}
        >
          <Filter className="w-4 h-4" />
          篩選
          <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Stats Cards */}
      {!statsLoading && stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <p className="text-zinc-400 text-xs mb-1">總劇本數</p>
            <p className="text-2xl font-bold text-white">{stats.total.toLocaleString()}</p>
          </div>
          {Object.entries(stats.by_age_rating).map(([rating, count]) => (
            <div key={rating} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <p className="text-zinc-400 text-xs mb-1">{AGE_RATING_LABELS[rating] ?? rating}</p>
              <p className={`text-2xl font-bold ${rating === 'mature' ? 'text-red-400' : 'text-white'}`}>
                {count.toLocaleString()}
              </p>
            </div>
          ))}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 col-span-2 lg:col-span-1">
            <div className="flex items-center gap-1 text-zinc-400 text-xs mb-2">
              <TrendingUp className="w-3 h-3" />
              Mature 熱門關係
            </div>
            <div className="space-y-1">
              {stats.mature_top_relations.slice(0, 3).map((r) => (
                <div key={r.relation_types} className="flex justify-between text-xs">
                  <span className="text-zinc-400 truncate max-w-[120px]">{r.relation_types}</span>
                  <span className="text-zinc-300">{r.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-900/50 text-green-200' : 'bg-red-900/50 text-red-200'
        }`}>
          {message.type === 'success' ? <Check className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          {message.text}
          <button onClick={() => setMessage(null)} className="ml-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="bg-zinc-800/50 rounded-xl p-4 space-y-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-xs text-zinc-400 mb-1">搜索</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchScripts()}
                  placeholder="標題、摘要..."
                  className="w-full pl-10 pr-4 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="min-w-[130px]">
              <label className="block text-xs text-zinc-400 mb-1">年齡分級</label>
              <select
                value={ageRatingFilter}
                onChange={(e) => setAgeRatingFilter(e.target.value as AgeRating)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                <option value="all">全年齡</option>
                <option value="mature">Mature 🔞</option>
              </select>
            </div>
            <div className="min-w-[120px]">
              <label className="block text-xs text-zinc-400 mb-1">狀態</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none"
              >
                <option value="">全部</option>
                <option value="published">已發布</option>
                <option value="draft">草稿</option>
                <option value="archived">已封存</option>
              </select>
            </div>
            <div className="min-w-[160px]">
              <label className="block text-xs text-zinc-400 mb-1">關係類型</label>
              <input
                type="text"
                value={relationFilter}
                onChange={(e) => setRelationFilter(e.target.value)}
                placeholder="e.g. aunt_paternal_nephew"
                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-zinc-200 focus:border-pink-500 focus:outline-none text-sm"
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setSearchQuery(''); setAgeRatingFilter('mature'); setStatusFilter(''); setRelationFilter(''); }} className="px-4 py-2 text-zinc-400 hover:text-white text-sm">
              重置
            </button>
            <button onClick={fetchScripts} className="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg text-sm">
              套用篩選
            </button>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {selectedIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 p-4 bg-zinc-800/50 rounded-lg border border-zinc-700">
          <span className="text-sm text-zinc-300">已選擇 <span className="font-bold text-white">{selectedIds.length}</span> 個劇本</span>
          <button onClick={handleBulkPublish} disabled={saving} className="px-3 py-1.5 bg-green-700 hover:bg-green-600 rounded text-sm flex items-center gap-1 disabled:opacity-50">
            <CheckCircle className="w-3.5 h-3.5" /> 批量發布
          </button>
          <button onClick={handleBulkArchive} disabled={saving} className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded text-sm flex items-center gap-1 disabled:opacity-50">
            <ArchiveX className="w-3.5 h-3.5" /> 批量封存
          </button>
          <button onClick={handleBulkDelete} disabled={saving} className="px-3 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm flex items-center gap-1 disabled:opacity-50">
            <X className="w-3.5 h-3.5" /> 批量刪除
          </button>
          <button onClick={() => setSelectedIds([])} className="ml-auto px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded text-sm">
            取消選擇
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-zinc-800/50">
                <tr>
                  <th className="px-4 py-3 text-left w-10">
                    <input type="checkbox" checked={selectedIds.length === items.length && items.length > 0} onChange={toggleSelectAll} className="rounded border-zinc-600" />
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">標題</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">分級</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">關係類型</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300">狀態</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300 hidden lg:table-cell">熱度</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-zinc-300 hidden xl:table-cell">創建時間</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-zinc-300">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {items.map((item) => (
                  <tr key={item.id} className={`hover:bg-zinc-800/30 ${item.age_rating === 'mature' ? 'border-l-2 border-red-800' : ''}`}>
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selectedIds.includes(item.id)} onChange={() => toggleSelect(item.id)} className="rounded border-zinc-600" />
                    </td>
                    <td className="px-4 py-3 max-w-[220px]">
                      <p className="text-white font-medium truncate">{item.title}</p>
                      {item.title_en && <p className="text-zinc-500 text-xs truncate">{item.title_en}</p>}
                      <p className="text-zinc-600 text-xs font-mono">{item.id}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs ${AGE_RATING_COLORS[item.age_rating] ?? 'bg-zinc-700 text-zinc-300'}`}>
                        {item.age_rating === 'mature' ? '🔞 Mature' : (AGE_RATING_LABELS[item.age_rating] ?? item.age_rating)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {parseJsonArray(item.relation_types).slice(0, 2).map((r) => (
                          <span key={r} className="px-1.5 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs">{r}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs ${STATUS_COLORS[item.status] ?? 'bg-zinc-700 text-zinc-400'}`}>
                        {STATUS_LABELS[item.status] ?? item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-400 text-sm hidden lg:table-cell">{item.popularity}</td>
                    <td className="px-4 py-3 text-zinc-500 text-xs hidden xl:table-cell">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setPreviewScript(item)}
                          className="p-1.5 hover:bg-zinc-700 rounded text-zinc-400 hover:text-white"
                          title="預覽"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {item.status !== 'published' && (
                          <button
                            onClick={() => handlePublish(item.id)}
                            disabled={saving}
                            className="p-1.5 hover:bg-green-900/50 rounded text-green-400 hover:text-green-300"
                            title="發布"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                        {item.status !== 'archived' && (
                          <button
                            onClick={() => handleArchive(item.id)}
                            disabled={saving}
                            className="p-1.5 hover:bg-zinc-700 rounded text-zinc-400 hover:text-zinc-200"
                            title="封存"
                          >
                            <ArchiveX className="w-4 h-4" />
                          </button>
                        )}
                        {item.age_rating === 'mature' && (
                          <button
                            onClick={() => handleDowngrade(item.id)}
                            disabled={saving}
                            className="p-1.5 hover:bg-yellow-900/50 rounded text-yellow-400 hover:text-yellow-300"
                            title="降級為全年齡"
                          >
                            <EyeOff className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-zinc-500">
                      查無劇本資料
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-zinc-400">
            第 {page} / {totalPages} 頁，共 {total} 筆
          </span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-40">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-4 py-2 bg-zinc-800 rounded-lg text-sm text-zinc-300">{page}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="p-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg disabled:opacity-40">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewScript && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-zinc-900 border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-white font-semibold">{previewScript.title}</h3>
                <p className="text-zinc-500 text-xs font-mono">{previewScript.id}</p>
              </div>
              <button onClick={() => setPreviewScript(null)} className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-400">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded text-xs ${AGE_RATING_COLORS[previewScript.age_rating] ?? ''}`}>
                  {previewScript.age_rating === 'mature' ? '🔞 Mature' : (AGE_RATING_LABELS[previewScript.age_rating] ?? previewScript.age_rating)}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[previewScript.status] ?? ''}`}>
                  {STATUS_LABELS[previewScript.status] ?? previewScript.status}
                </span>
                {parseJsonArray(previewScript.relation_types).map(r => (
                  <span key={r} className="px-2 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs">{r}</span>
                ))}
              </div>
              {previewScript.summary && (
                <div>
                  <p className="text-xs text-zinc-500 mb-1">摘要</p>
                  <p className="text-zinc-300 text-sm leading-relaxed">{previewScript.summary}</p>
                </div>
              )}
              <div className="flex gap-3 pt-2">
                {previewScript.status !== 'published' && (
                  <button onClick={() => { handlePublish(previewScript.id); setPreviewScript(null); }} className="px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg text-sm">
                    發布
                  </button>
                )}
                {previewScript.status !== 'archived' && (
                  <button onClick={() => { handleArchive(previewScript.id); setPreviewScript(null); }} className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm">
                    封存
                  </button>
                )}
                {previewScript.age_rating === 'mature' && (
                  <button onClick={() => { handleDowngrade(previewScript.id); setPreviewScript(null); }} className="px-4 py-2 bg-yellow-800 hover:bg-yellow-700 rounded-lg text-sm">
                    降級為全年齡
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
