import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { scriptLibraryService } from '../../services/scriptLibraryService';
import type { 
  ScriptLibrary, 
  ScriptLibraryListResponse, 
  ScriptTagsByCategory, 
  ScriptTag,
  ScriptLibraryFilter 
} from '../../types/scriptLibrary';
import ScriptLibraryCard from './ScriptLibraryCard';
import ScriptLibraryFilterPanel from './ScriptLibraryFilterPanel';

const ScriptLibraryList: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [scripts, setScripts] = useState<ScriptLibrary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [tags, setTags] = useState<ScriptTagsByCategory | null>(null);
  
  const [filter, setFilter] = useState<ScriptLibraryFilter>({
    emotion_tones: searchParams.get('emotion_tones')?.split(',').filter(Boolean) || [],
    relation_types: searchParams.get('relation_types')?.split(',').filter(Boolean) || [],
    contrast_types: searchParams.get('contrast_types')?.split(',').filter(Boolean) || [],
    era: searchParams.get('era') || undefined,
    gender_target: searchParams.get('gender_target') || undefined,
    character_gender: searchParams.get('character_gender') || undefined,
    profession: searchParams.get('profession') || undefined,
    age_rating: searchParams.get('age_rating') || undefined,
    length: searchParams.get('length') || undefined,
    search: searchParams.get('search') || undefined,
    page: parseInt(searchParams.get('page') || '1'),
    page_size: 20,
  });

  useEffect(() => {
    loadTags();
  }, []);

  useEffect(() => {
    loadScripts();
  }, [filter]);

  const loadTags = async () => {
    try {
      const tagsData = await scriptLibraryService.getAllTags();
      setTags(tagsData);
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const loadScripts = async () => {
    setLoading(true);
    try {
      const response: ScriptLibraryListResponse = await scriptLibraryService.listScripts(filter);
      setScripts(response.items);
      setTotal(response.total);
      setPage(response.page);
    } catch (error) {
      console.error('Failed to load scripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = useCallback((newFilter: Partial<ScriptLibraryFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter, page: 1 }));
    
    const params = new URLSearchParams();
    Object.entries({ ...filter, ...newFilter }).forEach(([key, value]) => {
      if (value && (Array.isArray(value) ? value.length > 0 : true)) {
        params.set(key, Array.isArray(value) ? value.join(',') : String(value));
      }
    });
    setSearchParams(params);
  }, [filter, setSearchParams]);

  const handlePageChange = (newPage: number) => {
    setFilter(prev => ({ ...prev, page: newPage }));
    window.scrollTo(0, 0);
  };

  const totalPages = Math.ceil(total / (filter.page_size || 20));

  return (
    <div className="script-library-page">
      <div className="script-library-header">
        <h1>{t('scriptLibrary.title', '剧本库')}</h1>
        <p>{t('scriptLibrary.subtitle', '探索AI驱动的互动故事')}</p>
      </div>

      <div className="script-library-search">
        <input
          type="text"
          placeholder={t('scriptLibrary.searchPlaceholder', '搜索剧本...')}
          value={filter.search || ''}
          onChange={(e) => handleFilterChange({ search: e.target.value || undefined })}
          className="search-input"
        />
      </div>

      <div className="script-library-content">
        <aside className="script-library-sidebar">
          {tags && (
            <ScriptLibraryFilterPanel
              tags={tags}
              filter={filter}
              onChange={handleFilterChange}
            />
          )}
        </aside>

        <main className="script-library-main">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>{t('common.loading', '加载中...')}</p>
            </div>
          ) : scripts.length === 0 ? (
            <div className="empty-state">
              <p>{t('scriptLibrary.noResults', '没有找到匹配的剧本')}</p>
            </div>
          ) : (
            <>
              <div className="scripts-count">
                {t('scriptLibrary.resultsCount', { count: total, defaultValue: `共 ${total} 个剧本` })}
              </div>
              
              <div className="scripts-grid">
                {scripts.map((script) => (
                  <ScriptLibraryCard key={script.id} script={script} />
                ))}
              </div>

              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() => handlePageChange(page - 1)}
                    disabled={page <= 1}
                    className="pagination-btn"
                  >
                    {t('common.previous', '上一页')}
                  </button>
                  
                  <span className="pagination-info">
                    {page} / {totalPages}
                  </span>
                  
                  <button
                    onClick={() => handlePageChange(page + 1)}
                    disabled={page >= totalPages}
                    className="pagination-btn"
                  >
                    {t('common.next', '下一页')}
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default ScriptLibraryList;
