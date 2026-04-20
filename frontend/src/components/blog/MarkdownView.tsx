/**
 * MarkdownView Component
 *
 * Renders Markdown content with proper styling using @tailwindcss/typography.
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewProps {
  content: string;
  className?: string;
}

export const MarkdownView: React.FC<MarkdownViewProps> = ({ content, className = '' }) => {
  return (
    <div className={`prose prose-slate max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Custom rendering for images to handle lazy loading
          img: ({ node: _node, ...props }) => (
            <img
              {...props}
              loading="lazy"
              className="rounded-lg shadow-md"
              alt={props.alt || 'Blog image'}
            />
          ),
          // Custom rendering for links to open in new tab
          a: ({ node: _node, ...props }) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-pink-600 hover:text-pink-700 underline"
            />
          ),
          // Custom rendering for code blocks
          code: ({ className, children, ...props }) => {
            return (
              <code
                className={className || "bg-gray-100 text-pink-600 px-1 py-0.5 rounded text-sm"}
                {...props}
              >
                {children}
              </code>
            );
          },
          // Custom rendering for pre blocks
          pre: ({ children }) => (
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
              {children}
            </pre>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
