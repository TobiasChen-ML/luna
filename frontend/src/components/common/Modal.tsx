import { cn } from '@/utils/cn';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  className?: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, className, children }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
      <div className="absolute inset-0" onClick={onClose} />
      <div
        className={cn(
          'relative z-10 w-full max-w-xl rounded-xl border border-zinc-700 bg-zinc-900 p-5',
          className
        )}
      >
        {title && <h2 className="text-lg font-semibold text-white mb-3">{title}</h2>}
        {children}
      </div>
    </div>
  );
}

