import { useEffect, useState } from 'react';
import { X, Image as ImageIcon, Video, Loader2 } from 'lucide-react';
import { api } from '@/services/api';

interface GalleryItem {
  id: string;
  image_url?: string;
  video_url?: string;
  created_at: string;
  content?: string;
}

interface GalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  characterId: string;
  characterName: string;
}

export function GalleryModal({ isOpen, onClose, characterId, characterName }: GalleryModalProps) {
  const [items, setItems] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<GalleryItem | null>(null);

  useEffect(() => {
    if (isOpen && characterId) {
      fetchGallery();
    }
  }, [isOpen, characterId]);

  const fetchGallery = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/chat/gallery/${characterId}`);
      if (Array.isArray(response.data)) {
        setItems(response.data);
      } else {
        setItems([]);
      }
    } catch (error) {
      console.error('Failed to fetch gallery:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b border-zinc-800">
          <h2 className="text-lg sm:text-xl font-heading font-bold text-white truncate">
            {characterName}'s Gallery
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-full transition-colors flex-shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label="Close gallery"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-2 sm:p-4 custom-scrollbar" style={{ WebkitOverflowScrolling: 'touch' }}>
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-400">
              <Loader2 size={32} className="animate-spin mb-2" />
              <p>Loading gallery...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
              <ImageIcon size={48} className="mb-4 opacity-20" />
              <p className="text-lg">No media found yet</p>
              <p className="text-sm">Chat with {characterName} to generate images!</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-4">
              {items.map((item) => (
                <div 
                  key={item.id} 
                  className="relative aspect-square rounded-lg overflow-hidden group cursor-pointer border border-zinc-800 bg-zinc-950"
                  onClick={() => setSelectedItem(item)}
                >
                  {item.video_url ? (
                     <div className="w-full h-full relative">
                        <video 
                          src={item.video_url} 
                          className="w-full h-full object-cover"
                          muted // Auto-play muted for preview
                          onMouseOver={e => e.currentTarget.play()}
                          onMouseOut={e => e.currentTarget.pause()}
                        />
                        <div className="absolute top-2 right-2 bg-black/60 p-1 rounded-md">
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
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                    <p className="text-xs text-white truncate w-full">
                        {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Full Screen Preview */}
      {selectedItem && (
        <div
            className="fixed inset-0 z-[60] flex items-center justify-center bg-black/95 p-2 sm:p-4 animate-in fade-in duration-200"
            onClick={() => setSelectedItem(null)}
        >
            <button
                className="absolute top-2 right-2 sm:top-4 sm:right-4 p-2 text-white/70 hover:text-white min-w-[44px] min-h-[44px] flex items-center justify-center bg-black/50 rounded-full"
                onClick={() => setSelectedItem(null)}
                aria-label="Close preview"
            >
                <X size={24} className="sm:w-8 sm:h-8" />
            </button>
            <div className="max-w-full max-h-full px-12 sm:px-0" onClick={e => e.stopPropagation()}>
                {selectedItem.video_url ? (
                    <video 
                        src={selectedItem.video_url} 
                        controls 
                        autoPlay 
                        className="max-w-full max-h-[90vh] rounded-lg"
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
