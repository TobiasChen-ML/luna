import { api } from './api';

export interface FactoryTemplate {
  id: string;
  name: string;
  description?: string;
  cover_image_url?: string;
  category?: string;
  is_official: boolean;
  sort_order?: number;
  data: Record<string, unknown>;
  clone_count: number;
  created_at?: string;
  updated_at?: string;
}

interface ListTemplatesResponse {
  items: FactoryTemplate[];
  total: number;
}

export const templateService = {
  async listTemplates(params?: {
    limit?: number;
    offset?: number;
    category?: string;
    is_official?: boolean;
  }): Promise<FactoryTemplate[]> {
    const response = await api.get<ListTemplatesResponse>('/templates', { params });
    return response.data.items ?? [];
  },

  async getTemplate(id: string): Promise<FactoryTemplate | null> {
    try {
      const response = await api.get<FactoryTemplate>(`/templates/${id}`);
      return response.data;
    } catch (err) {
      if (import.meta.env.DEV) console.warn('[templateService] getTemplate failed', err);
      return null;
    }
  },
};
