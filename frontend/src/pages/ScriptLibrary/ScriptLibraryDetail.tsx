import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { scriptLibraryService } from '../../services/scriptLibraryService';
import type { ScriptLibrary } from '../../types/scriptLibrary';

const ScriptLibraryDetail: React.FC = () => {
  const { scriptId } = useParams<{ scriptId: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  
  const [script, setScript] = useState<ScriptLibrary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (scriptId) {
      loadScript(scriptId);
    }
  }, [scriptId]);

  const loadScript = async (id: string) => {
    setLoading(true);
    try {
      const data = await scriptLibraryService.getScript(id);
      setScript(data);
    } catch (error) {
      console.error('Failed to load script:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/script-library');
  };

  const handleUseScript = () => {
    navigate(`/characters/create?scriptId=${scriptId}`);
  };

  if (loading) {
    return (
      <div className="script-detail-loading">
        <div className="spinner"></div>
        <p>{t('common.loading', '加载中...')}</p>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="script-detail-not-found">
        <h2>{t('scriptLibrary.notFound', '剧本未找到')}</h2>
        <button onClick={handleBack}>{t('common.back', '返回')}</button>
      </div>
    );
  }

  const isEnglish = i18n.language === 'en';
  const title = isEnglish && script.title_en ? script.title_en : script.title;
  const seed = script.script_seed;

  return (
    <div className="script-detail-page">
      <button className="back-button" onClick={handleBack}>
        ← {t('common.back', '返回')}
      </button>

      <header className="script-detail-header">
        <div className="script-title-section">
          <h1>{title}</h1>
          {script.age_rating === 'adult' && (
            <span className="age-badge adult">18+</span>
          )}
        </div>
        <p className="script-summary">{script.summary}</p>
        
        <div className="script-tags-row">
          {script.emotion_tones.map((tone) => (
            <span key={tone} className="tag tone-tag">{tone}</span>
          ))}
          {script.relation_types.map((type) => (
            <span key={type} className="tag relation-tag">{type}</span>
          ))}
        </div>

        <button className="use-script-btn" onClick={handleUseScript}>
          {t('scriptLibrary.useScript', '使用此剧本')}
        </button>
      </header>

      <section className="script-contrast-section">
        <h2>{t('scriptLibrary.contrastDesign', '反差设计')}</h2>
        <div className="contrast-cards">
          <div className="contrast-card surface">
            <h3>{t('scriptLibrary.surface', '表象')}</h3>
            <p>{script.contrast_surface}</p>
          </div>
          <div className="contrast-card truth">
            <h3>{t('scriptLibrary.truth', '真相')}</h3>
            <p>{script.contrast_truth}</p>
          </div>
          <div className="contrast-card hook">
            <h3>{t('scriptLibrary.hook', '情感钩子')}</h3>
            <p>{script.contrast_hook}</p>
          </div>
        </div>
      </section>

      {seed && (
        <>
          <section className="script-character-section">
            <h2>{t('scriptLibrary.character', '角色设定')}</h2>
            <div className="character-info">
              <div className="character-basic">
                <p><strong>{t('scriptLibrary.characterName', '姓名')}:</strong> {seed.character.name}</p>
                <p><strong>{t('scriptLibrary.characterAge', '年龄')}:</strong> {seed.character.age}</p>
                <p><strong>{t('scriptLibrary.characterProfession', '职业')}:</strong> {seed.character.profession}</p>
              </div>
              <div className="character-identity">
                <div className="identity-card surface">
                  <h4>{t('scriptLibrary.surfaceIdentity', '表象身份')}</h4>
                  <p>{seed.character.surface_identity}</p>
                </div>
                <div className="identity-card truth">
                  <h4>{t('scriptLibrary.trueIdentity', '真实身份')}</h4>
                  <p>{seed.character.true_identity}</p>
                </div>
              </div>
            </div>
          </section>

          <section className="script-progression-section">
            <h2>{t('scriptLibrary.storyProgression', '剧情推进')}</h2>
            <div className="progression-timeline">
              <div className="progression-item">
                <div className="progression-marker start">1</div>
                <div className="progression-content">
                  <h4>{t('scriptLibrary.progression.start', '开场')}</h4>
                  <p>{seed.progression.start}</p>
                </div>
              </div>
              <div className="progression-item">
                <div className="progression-marker build">2</div>
                <div className="progression-content">
                  <h4>{t('scriptLibrary.progression.build', '发展')}</h4>
                  <p>{seed.progression.build}</p>
                </div>
              </div>
              <div className="progression-item">
                <div className="progression-marker climax">3</div>
                <div className="progression-content">
                  <h4>{t('scriptLibrary.progression.climax', '高潮')}</h4>
                  <p>{seed.progression.climax}</p>
                </div>
              </div>
              <div className="progression-item">
                <div className="progression-marker resolve">4</div>
                <div className="progression-content">
                  <h4>{t('scriptLibrary.progression.resolve', '结局')}</h4>
                  <p>{seed.progression.resolve}</p>
                </div>
              </div>
            </div>
          </section>

          <section className="script-nodes-section">
            <h2>{t('scriptLibrary.keyNodes', '关键节点')}</h2>
            <div className="nodes-list">
              {seed.key_nodes.map((node, index) => (
                <div key={index} className="node-item">
                  <div className="node-header">
                    <h4>{node.name}</h4>
                    <span className="node-trigger">{node.trigger}</span>
                  </div>
                  <p>{node.description}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="script-endings-section">
            <h2>{t('scriptLibrary.endings', '多种结局')}</h2>
            <div className="endings-grid">
              <div className="ending-card good">
                <h4>🌟 {t('scriptLibrary.endingTypes.good', '好结局')}</h4>
                <p>{seed.endings.good}</p>
              </div>
              <div className="ending-card neutral">
                <h4>⚪ {t('scriptLibrary.endingTypes.neutral', '中性结局')}</h4>
                <p>{seed.endings.neutral}</p>
              </div>
              <div className="ending-card bad">
                <h4>💔 {t('scriptLibrary.endingTypes.bad', '坏结局')}</h4>
                <p>{seed.endings.bad}</p>
              </div>
              <div className="ending-card secret">
                <h4>🔮 {t('scriptLibrary.endingTypes.secret', '隐藏结局')}</h4>
                <p>{seed.endings.secret}</p>
              </div>
            </div>
          </section>
        </>
      )}

      <div className="script-meta-section">
        <p>
          <span>👁️ {script.popularity} {t('scriptLibrary.views', '次浏览')}</span>
          <span> | </span>
          <span>{t(`scriptLibrary.length.${script.length}`, script.length)}</span>
          {script.gender_target && (
            <>
              <span> | </span>
              <span>{t(`scriptLibrary.genderTarget.${script.gender_target}`, script.gender_target)}</span>
            </>
          )}
        </p>
      </div>
    </div>
  );
};

export default ScriptLibraryDetail;
