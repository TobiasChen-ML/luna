import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { ScriptLibrary } from '../../types/scriptLibrary';

interface ScriptLibraryCardProps {
  script: ScriptLibrary;
}

const ScriptLibraryCard: React.FC<ScriptLibraryCardProps> = ({ script }) => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  
  const isEnglish = i18n.language === 'en';
  const title = isEnglish && script.title_en ? script.title_en : script.title;

  const handleClick = () => {
    navigate(`/script-library/${script.id}`);
  };

  const getEmotionToneLabel = (tone: string): string => {
    const labels: Record<string, string> = {
      angst: t('scriptLibrary.tones.angst', '虐恋'),
      sweet: t('scriptLibrary.tones.sweet', '甜宠'),
      healing: t('scriptLibrary.tones.healing', '治愈'),
      comedy: t('scriptLibrary.tones.comedy', '搞笑'),
      suspense: t('scriptLibrary.tones.suspense', '悬疑'),
      thriller: t('scriptLibrary.tones.thriller', '惊悚'),
      tragedy: t('scriptLibrary.tones.tragedy', '悲剧'),
      harem: t('scriptLibrary.tones.harem', '后宫'),
      revenge: t('scriptLibrary.tones.revenge', '复仇'),
      rebirth: t('scriptLibrary.tones.rebirth', '重生'),
      ethical: t('scriptLibrary.tones.ethical', '伦理'),
      dark: t('scriptLibrary.tones.dark', '暗黑'),
    };
    return labels[tone] || tone;
  };

  return (
    <div className="script-card" onClick={handleClick}>
      <div className="script-card-header">
        <h3 className="script-title">{title}</h3>
        {script.age_rating === 'adult' && (
          <span className="age-badge adult">18+</span>
        )}
      </div>

      <p className="script-summary">{script.summary}</p>

      <div className="script-contrast">
        <div className="contrast-item">
          <span className="contrast-label">{t('scriptLibrary.surface', '表象')}:</span>
          <span className="contrast-value">{script.contrast_surface}</span>
        </div>
        <div className="contrast-item">
          <span className="contrast-label">{t('scriptLibrary.truth', '真相')}:</span>
          <span className="contrast-value">{script.contrast_truth}</span>
        </div>
        <div className="contrast-hook">
          <span className="hook-icon">💡</span>
          {script.contrast_hook}
        </div>
      </div>

      <div className="script-tags">
        {script.emotion_tones.slice(0, 2).map((tone) => (
          <span key={tone} className="tag tone-tag">
            {getEmotionToneLabel(tone)}
          </span>
        ))}
        {script.relation_types.slice(0, 2).map((type) => (
          <span key={type} className="tag relation-tag">
            {type}
          </span>
        ))}
      </div>

      <div className="script-meta">
        <span className="meta-item">
          <span className="meta-icon">👁️</span>
          {script.popularity}
        </span>
        <span className="meta-item">
          <span className="meta-icon">📝</span>
          {t(`scriptLibrary.length.${script.length}`, script.length)}
        </span>
        {script.gender_target && (
          <span className="meta-item">
            {t(`scriptLibrary.genderTarget.${script.gender_target}`, script.gender_target)}
          </span>
        )}
      </div>
    </div>
  );
};

export default ScriptLibraryCard;
