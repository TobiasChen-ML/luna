interface LoadingSpinnerProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ text, size = 'md' }: LoadingSpinnerProps) {
  const spinnerSizeClass =
    size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-8 w-8' : 'h-4 w-4';
  return (
    <div className="flex items-center justify-center gap-2 text-zinc-400">
      <div
        className={`animate-spin ${spinnerSizeClass} border-2 border-zinc-400 border-t-transparent rounded-full`}
      />
      {text && <span className="text-sm">{text}</span>}
    </div>
  );
}
