/**
 * BlogList Page
 *
 * Public page displaying a grid of published blog posts.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getBlogPosts, type BlogPost } from '@/services/blogService';
import { Container } from '@/components/layout/Container';

export const BlogList: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const selectedTag = searchParams.get('tag') || undefined;

  useEffect(() => {
    loadPosts();
  }, [page, selectedTag]);

  const loadPosts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getBlogPosts(page, 12, selectedTag);
      setPosts(response.posts);
      setTotalPages(response.total_pages);
    } catch (err: any) {
      console.error('Failed to load blog posts:', err);
      setError(err.response?.data?.detail || 'Failed to load blog posts');
    } finally {
      setLoading(false);
    }
  };

  const handleTagClick = (tag: string) => {
    setSearchParams({ tag });
    setPage(1);
  };

  const clearTagFilter = () => {
    setSearchParams({});
    setPage(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Container className="py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Blog
          </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Insights, updates, and stories from the RoxyClub team.
        </p>
      </div>

      {/* Tag Filter */}
      {selectedTag && (
        <div className="mb-8 flex items-center justify-center gap-2">
          <span className="text-sm text-gray-600">Filtering by tag:</span>
          <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-sm font-medium">
            {selectedTag}
          </span>
          <button
            onClick={clearTagFilter}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear filter
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600"></div>
          <p className="mt-4 text-gray-600">Loading posts...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <p className="text-red-700">{error}</p>
          <button
            onClick={loadPosts}
            className="mt-2 text-red-600 hover:text-red-700 underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Posts Grid */}
      {!loading && !error && posts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">No blog posts found.</p>
        </div>
      )}

      {!loading && !error && posts.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {posts.map((post) => (
              <article
                key={post.id}
                onClick={() => navigate(`/blog/${post.slug}`)}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
              >
                {/* Cover Image */}
                {post.cover_image && (
                  <div className="h-48 overflow-hidden bg-gray-200">
                    <img
                      src={post.cover_image}
                      alt={post.title}
                      className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                )}

                {/* Content */}
                <div className="p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                    {post.title}
                  </h2>

                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {post.summary}
                  </p>

                  {/* Tags */}
                  {post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {post.tags.map((tag) => (
                        <button
                          key={tag}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTagClick(tag);
                          }}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium hover:bg-pink-100 hover:text-pink-700 transition-colors"
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Meta */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{formatDate(post.created_at)}</span>
                    <span>{post.views} views</span>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-12">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>

              <span className="px-4 py-2 text-gray-700">
                Page {page} of {totalPages}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
      </Container>
    </div>
  );
};

export default BlogList;

