import React from 'react';
import { useTranslation } from 'react-i18next';
import type { ScriptTagsByCategory, ScriptLibraryFilter } from '../../types/scriptLibrary';

interface ScriptLibraryFilterPanelProps {
  tags: ScriptTagsByCategory;
  filter: ScriptLibraryFilter;
  onChange: (filter: Partial<ScriptLibraryFilter>) => void;
}

const ScriptLibraryFilterPanel: React.FC<ScriptLibraryFilterPanelProps> = ({
  tags,
  filter,
  onChange,
}) => {
  const { t, i18n } = useTranslation();
  const isEnglish = i18n.language === 'en';

  const getTagName = (tag: { name: string; name_en?: string }): string => {
    return isEnglish && tag.name_en ? tag.name_en : tag.name;
  };

  const handleTagClick = (
    category: keyof ScriptLibraryFilter,
    tagId: string
  ) => {
    const currentValues = (filter[category] as string[]) || [];
    const newValues = currentValues.includes(tagId)
      ? currentValues.filter((v) => v !== tagId)
      : [...currentValues, tagId];
    
    onChange({ [category]: newValues.length > 0 ? newValues : undefined });
  };

  const handleSingleSelect = (
    category: keyof ScriptLibraryFilter,
    value: string | undefined
  ) => {
    onChange({ [category]: value });
  };

  const clearAllFilters = () => {
    onChange({
      emotion_tones: undefined,
      relation_types: undefined,
      contrast_types: undefined,
      era: undefined,
      gender_target: undefined,
      character_gender: undefined,
      profession: undefined,
      age_rating: undefined,
      length: undefined,
    });
  };

  const hasActiveFilters = 
    (filter.emotion_tones?.length || 0) > 0 ||
    (filter.relation_types?.length || 0) > 0 ||
    (filter.contrast_types?.length || 0) > 0 ||
    filter.era ||
    filter.gender_target ||
    filter.character_gender ||
    filter.profession ||
    filter.age_rating ||
    filter.length;

  const renderTagGroup = (
    title: string,
    tagList: { id: string; name: string; name_en?: string }[],
    category: keyof ScriptLibraryFilter,
    isMultiSelect: boolean = true
  ) => {
    if (!tagList || tagList.length === 0) return null;

    const selectedValues = (filter[category] as string[]) || [];

    return (
      <div className="filter-group">
        <h4 className="filter-group-title">{title}</h4>
        <div className="filter-tags">
          {tagList.map((tag) => {
            const isSelected = isMultiSelect
              ? selectedValues.includes(tag.id)
              : selectedValues[0] === tag.id;

            return (
              <button
                key={tag.id}
                className={`filter-tag ${isSelected ? 'selected' : ''}`}
                onClick={() =>
                  isMultiSelect
                    ? handleTagClick(category, tag.id)
                    : handleSingleSelect(category, isSelected ? undefined : tag.id)
                }
              >
                {getTagName(tag)}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="filter-panel">
      <div className="filter-header">
        <h3>{t('scriptLibrary.filters', '筛选')}</h3>
        {hasActiveFilters && (
          <button className="clear-filters" onClick={clearAllFilters}>
            {t('common.clearAll', '清除全部')}
          </button>
        )}
      </div>

      {renderTagGroup(
        t('scriptLibrary.filterCategories.emotionTones', '情感基调'),
        tags.emotion_tones,
        'emotion_tones'
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.relationTypes', '关系类型'),
        tags.relation_types,
        'relation_types'
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.contrastTypes', '反差类型'),
        tags.contrast_types,
        'contrast_types'
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.eras', '时代背景'),
        tags.eras,
        'era',
        false
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.professions', '职业背景'),
        tags.professions,
        'profession',
        false
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.genderTarget', '性别向'),
        tags.gender_targets,
        'gender_target',
        false
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.characterGender', '角色性别'),
        tags.character_genders,
        'character_gender',
        false
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.length', '剧情长度'),
        tags.lengths,
        'length',
        false
      )}

      {renderTagGroup(
        t('scriptLibrary.filterCategories.ageRating', '年龄向'),
        tags.age_ratings,
        'age_rating',
        false
      )}
    </div>
  );
};

export default ScriptLibraryFilterPanel;
