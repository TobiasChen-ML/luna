import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface ImagePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
}

export function ImagePreviewModal({ isOpen, onClose, imageUrl }: ImagePreviewModalProps) {
  const [scale, setScale] = useState(1);

  // Reset scale when modal opens
  useEffect(() => {
    if (isOpen) setScale(1);
  }, [isOpen]);

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.5, 4));
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.5, 0.5));
  const handleReset = () => setScale(1);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
          onClick={onClose}
        >
          {/* Controls */}
          <div 
            className="absolute top-4 right-4 flex gap-2 z-10"
            onClick={e => e.stopPropagation()}
          >
            <button
              onClick={handleZoomIn}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              title="Zoom In"
            >
              <ZoomIn size={20} />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              title="Zoom Out"
            >
              <ZoomOut size={20} />
            </button>
            <button
              onClick={handleReset}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
              title="Reset"
            >
              <RotateCcw size={20} />
            </button>
            <button
              onClick={onClose}
              className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors ml-2"
              title="Close"
            >
              <X size={20} />
            </button>
          </div>

          {/* Image Container */}
          <div 
            className="w-full h-full flex items-center justify-center overflow-hidden p-4"
            onClick={e => e.stopPropagation()}
          >
            <motion.img
              src={imageUrl}
              alt="Preview"
              className="max-w-full max-h-full object-contain cursor-grab active:cursor-grabbing"
              drag
              dragConstraints={{ left: -1000, right: 1000, top: -1000, bottom: 1000 }}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: scale, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.2 }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
