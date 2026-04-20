/**
 * BlogPost Page
 *
 * Public page displaying a single blog post with full content.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBlogPost, type BlogPost as BlogPostType } from '@/services/blogService';
import { MarkdownView } from '@/components/blog/MarkdownView';
import { Container } from '@/components/layout/Container';

export const BlogPost: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();

  const [post, setPost] = useState<BlogPostType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      navigate('/blog');
      return;
    }

    loadPost();
  }, [slug]);

  const loadPost = async () => {
    if (!slug) return;

    try {
      setLoading(true);
      setError(null);
      const postData = await getBlogPost(slug);
      setPost(postData);
    } catch (err: any) {
      console.error('Failed to load blog post:', err);
      if (err.response?.status === 404) {
        setError('Blog post not found');
      } else {
        setError(err.response?.data?.detail || 'Failed to load blog post');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-white">
      <Container className="py-12">
        {/* Loading State */}
        {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600"></div>
          <p className="mt-4 text-gray-600">Loading post...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-red-900 mb-2">Error</h2>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={() => navigate('/blog')}
              className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors"
            >
              Back to Blog
            </button>
          </div>
        </div>
      )}

      {/* Post Content */}
      {!loading && !error && post && (
        <article className="max-w-4xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => navigate('/blog')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Blog
          </button>

          {/* Cover Image */}
          {post.cover_image && (
            <div className="mb-8 rounded-lg overflow-hidden shadow-lg">
              <img
                src={post.cover_image}
                alt={post.title}
                className="w-full h-auto"
              />
            </div>
          )}

          {/* Header */}
          <header className="mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              {post.title}
            </h1>

            <p className="text-xl text-gray-600 mb-4">{post.summary}</p>

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-4">
              <span>{formatDate(post.created_at)}</span>
              <span>•</span>
              <span>{post.views} views</span>
            </div>

            {/* Tags */}
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {post.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-sm font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </header>

          {/* Divider */}
          <hr className="border-gray-200 mb-8" />

          {/* Content */}
          <div className="mb-12">
            <MarkdownView content={post.content} />
          </div>

          {/* Footer */}
          <footer className="border-t border-gray-200 pt-8">
            <button
              onClick={() => navigate('/blog')}
              className="px-6 py-3 bg-pink-600 text-white rounded-lg hover:bg-pink-700 transition-colors"
            >
              View More Posts
            </button>
          </footer>
        </article>
      )}
      </Container>
    </div>
  );
};

export default BlogPost;
