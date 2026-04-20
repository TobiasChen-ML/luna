/**
 * Blog Service
 *
 * API client for blog post operations.
 */

import { api } from './api';

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  cover_image?: string;
  tags: string[];
  views: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface BlogPostListResponse {
  posts: BlogPost[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}


/**
 * Get a paginated list of published blog posts.
 */
export const getBlogPosts = async (
  page: number = 1,
  pageSize: number = 10,
  tag?: string
): Promise<BlogPostListResponse> => {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (tag) {
    params.tag = tag;
  }

  const response = await api.get('/api/blog', { params });
  return response.data;
};

/**
 * Get a single blog post by slug.
 */
export const getBlogPost = async (slug: string): Promise<BlogPost> => {
  const response = await api.get(`/api/blog/${slug}`);
  return response.data;
};

