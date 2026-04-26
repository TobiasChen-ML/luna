/**
 * Gallery Page - Display all user's generated media
 * Shows images and videos across all characters with filters
 */
import { useEffect, useState } from 'react';
import { Image as ImageIcon, Video, Filter, X, Download, Share2, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';
import { Button } from '@/components/common';
import { claimShareReward, share } from '@/utils/share';
import { useAuth } from '@/contexts/AuthContext';

interface GalleryItem {
  id: string;
  image_url?: string;
  video_url?: string;
  created_at: string;
  content?: string;
  character_name?: string;
  character_id?: string;
  character_image_url?: string;
  session_id?: string;
}

type MediaType = 'all' | 'image' | 'video';
type SortBy = 'newest' | 'oldest' | 'character';

export function GalleryPage() {
  const navigate = useNavigate();
  const { isAuthenticated, refreshUser } = useAuth();
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<GalleryItem | null>(null);

  // Filters
  const [mediaType, setMediaType] = useState<MediaType>('all');
  const [sortBy, setSortBy] = useState<SortBy>('newest');
  const [characterFilter, setCharacterFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Character list for filter dropdown
  const [characters, setCharacters] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    fetchGallery();
  }, [mediaType]);

  useEffect(() => {
    applyFilters();
  }, [items, sortBy, characterFilter]);

  const fetchGallery = async () => {
    setLoading(true);
    try {
      const [chatRes, mediaRes] = await Promise.allSettled([
        api.get(`/chat/gallery`, { params: { media_type: mediaType, limit: 200 } }),
        api.get(`/images/my-media`, { params: { limit: 200 } }),
      ]);

      const chatItems: GalleryItem[] = chatRes.status === 'fulfilled' && Array.isArray(chatRes.value.data)
        ? chatRes.value.data
        : [];

      const mediaItems: GalleryItem[] = mediaRes.status === 'fulfilled' && Array.isArray(mediaRes.value.data)
        ? (mediaRes.value.data as Array<Record<string, unknown>>).map((item) => ({
            id: item['id'] as string,
            image_url: item['image_url'] as string | undefined,
            video_url: item['video_url'] as string | undefined,
            created_at: (item['created_at'] as string) || new Date().toISOString(),
            content: item['prompt'] as string | undefined,
            character_name: item['character_name'] as string | undefined,
            character_id: item['character_id'] as string | undefined,
          }))
        : [];

      // Merge, deduplicate by id
      const seen = new Set<string>();
      const merged: GalleryItem[] = [];
      for (const item of [...chatItems, ...mediaItems]) {
        if (item.id && !seen.has(item.id)) {
          seen.add(item.id);
          merged.push(item);
        }
      }

      // Apply media type filter
      const filtered = mediaType === 'all'
        ? merged
        : mediaType === 'video'
          ? merged.filter((i) => i.video_url)
          : merged.filter((i) => i.image_url && !i.video_url);

      setItems(filtered);

      const uniqueChars = new Map<string, string>();
      filtered.forEach((item: GalleryItem) => {
        if (item.character_id && item.character_name) {
          uniqueChars.set(item.character_id, item.character_name);
        }
      });
      setCharacters(
        Array.from(uniqueChars.entries()).map(([id, name]) => ({ id, name }))
      );
    } catch (err) {
      console.error('Failed to fetch gallery:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...items];

    // Filter by character
    if (characterFilter !== 'all') {
      filtered = filtered.filter(item => item.character_id === characterFilter);
    }

    // Sort
    if (sortBy === 'newest') {
      filtered.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    } else if (sortBy === 'oldest') {
      filtered.sort((a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    } else if (sortBy === 'character') {
      filtered.sort((a, b) =>
        (a.character_name || '').localeCompare(b.character_name || '')
      );
    }

    setFilteredItems(filtered);
  };

  const handleDownload = async (item: GalleryItem) => {
    const url = item.video_url || item.image_url;
    if (!url) return;

    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${item.character_name || 'media'}-${item.id}.${
        item.video_url ? 'mp4' : 'png'
      }`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleShare = async (item: GalleryItem) => {
    const url = item.video_url || item.image_url;
    if (!url) return;

    const didShare = await share({
      title: `AI Generated by ${item.character_name}`,
      text: item.content || 'Check out this AI-generated media!',
      url,
    });

    if (!didShare || !isAuthenticated) return;

    const reward = await claimShareReward(`gallery:${item.id}`, 'gallery_media', {
      media_type: item.video_url ? 'video' : 'image',
      character_id: item.character_id,
    });
    if (reward?.granted) {
      await refreshUser();
    }
  };

  return (
    <div className="text-white">
      {/* Header */}
      <header className="sticky top-14 z-30 bg-zinc-900/95 backdrop-blur-sm border-b border-zinc-800">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-heading font-bold">My Gallery</h1>
              <p className="text-sm text-zinc-400 mt-1">
                {filteredItems.length} {mediaType === 'all' ? 'items' : `${mediaType}s`}
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter size={16} />
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </Button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="mt-4 p-4 bg-zinc-800/50 rounded-lg border border-zinc-700 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Media Type Filter */}
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Media Type
                </label>
                <select
                  value={mediaType}
                  onChange={(e) => setMediaType(e.target.value as MediaType)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                >
                  <option value="all">All Media</option>
                  <option value="image">Images Only</option>
                  <option value="video">Videos Only</option>
                </select>
              </div>

              {/* Sort By */}
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortBy)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                >
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="character">By Character</option>
                </select>
              </div>

              {/* Character Filter */}
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">
                  Character
                </label>
                <select
                  value={characterFilter}
                  onChange={(e) => setCharacterFilter(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                >
                  <option value="all">All Characters</option>
                  {characters.map((char) => (
                    <option key={char.id} value={char.id}>
                      {char.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Gallery Grid */}
      <main className="container mx-auto px-4 py-8">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-64 text-zinc-400">
            <Loader2 size={48} className="animate-spin mb-4" />
            <p className="text-lg">Loading your gallery...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
            <ImageIcon size={64} className="mb-4 opacity-20" />
            <p className="text-xl mb-2">No media found</p>
            <p className="text-sm">
              {mediaType === 'all'
                ? 'Start chatting with your characters to generate images and videos!'
                : `No ${mediaType}s generated yet`}
            </p>
            <Button
              onClick={() => navigate('/chat')}
              className="mt-4"
            >
              Start Chatting
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="relative aspect-square rounded-lg overflow-hidden group cursor-pointer border border-zinc-800 bg-zinc-900 hover:border-pink-500 transition-all"
                onClick={() => setSelectedItem(item)}
              >
                {/* Media */}
                {item.video_url ? (
                  <div className="w-full h-full relative">
                    <video
                      src={item.video_url}
                      className="w-full h-full object-cover"
                      muted
                      onMouseOver={(e) => e.currentTarget.play()}
                      onMouseOut={(e) => e.currentTarget.pause()}
                    />
                    <div className="absolute top-2 right-2 bg-black/60 p-1.5 rounded-md">
                      <Video size={14} className="text-white" />
                    </div>
                  </div>
                ) : (
                  <img
                    src={item.image_url}
                    alt="Generated content"
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                  />
                )}

                {/* Overlay with character info */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
                  {item.character_name && (
                    <div className="flex items-center gap-2 mb-2">
                      {item.character_image_url && (
                        <img
                          src={item.character_image_url}
                          alt={item.character_name}
                          className="w-6 h-6 rounded-full border border-white/20"
                        />
                      )}
                      <p className="text-xs font-semibold text-white truncate">
                        {item.character_name}
                      </p>
                    </div>
                  )}
                  <p className="text-xs text-zinc-300">
                    {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Full Screen Preview Modal */}
      {selectedItem && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-4 animate-in fade-in duration-200"
          onClick={() => setSelectedItem(null)}
        >
          {/* Close button */}
          <button
            className="absolute top-4 right-4 p-2 text-white/70 hover:text-white bg-black/50 rounded-full transition-colors"
            onClick={() => setSelectedItem(null)}
            aria-label="Close preview"
          >
            <X size={24} />
          </button>

          {/* Action buttons */}
          <div className="absolute top-4 left-4 flex gap-2">
            <button
              className="p-2 text-white/70 hover:text-white bg-black/50 rounded-full transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                handleDownload(selectedItem);
              }}
              aria-label="Download"
            >
              <Download size={20} />
            </button>
            <button
              className="p-2 text-white/70 hover:text-white bg-black/50 rounded-full transition-colors"
              onClick={(e) => {
                e.stopPropagation();
                handleShare(selectedItem);
              }}
              aria-label="Share"
            >
              <Share2 size={20} />
            </button>
          </div>

          {/* Character info */}
          {selectedItem.character_name && (
            <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-black/50 backdrop-blur-sm rounded-lg p-3">
              {selectedItem.character_image_url && (
                <img
                  src={selectedItem.character_image_url}
                  alt={selectedItem.character_name}
                  className="w-10 h-10 rounded-full border-2 border-white/20"
                />
              )}
              <div>
                <p className="text-sm font-semibold text-white">
                  {selectedItem.character_name}
                </p>
                <p className="text-xs text-zinc-400">
                  {new Date(selectedItem.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          )}

          {/* Media */}
          <div className="max-w-full max-h-full" onClick={(e) => e.stopPropagation()}>
            {selectedItem.video_url ? (
              <video
                src={selectedItem.video_url}
                controls
                autoPlay
                className="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
              />
            ) : (
              <img
                src={selectedItem.image_url}
                alt="Full view"
                className="max-w-full max-h-[90vh] rounded-lg shadow-2xl"
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
