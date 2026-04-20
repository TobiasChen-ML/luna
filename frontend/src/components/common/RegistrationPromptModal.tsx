import { Link } from 'react-router-dom';
import { X, UserPlus, Sparkles, Gift, MessageCircle, Image, Mic, Users } from 'lucide-react';
import { Button } from './Button';

interface RegistrationPromptModalProps {
  isOpen: boolean;
  onClose?: () => void;
  variant?: 'credits_exhausted' | 'feature_locked';
}

export function RegistrationPromptModal({
  isOpen,
  onClose,
  variant = 'credits_exhausted'
}: RegistrationPromptModalProps) {
  if (!isOpen) return null;

  const content = {
    credits_exhausted: {
      title: 'Free Credits Exhausted',
      description: "You've used all your free guest credits. Sign up now to continue chatting and get 10 free credits!",
      icon: Gift,
    },
    feature_locked: {
      title: 'Premium Feature',
      description: 'This feature requires a free account. Sign up to unlock image generation, voice chat, and more!',
      icon: Sparkles,
    }
  };

  const benefits = [
    { icon: Gift, text: '10 free credits on signup' },
    { icon: MessageCircle, text: 'Unlimited conversation history' },
    { icon: Image, text: 'Image generation with your AI' },
    { icon: Mic, text: 'Voice chat capabilities' },
    { icon: Users, text: 'Create custom characters' },
  ];

  const { title, description, icon: Icon } = content[variant];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop - blocks interaction */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-zinc-900 rounded-2xl border border-white/10 p-8 shadow-2xl">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        )}

        <div className="text-center space-y-6">
          {/* Icon */}
          <div className="w-20 h-20 mx-auto bg-gradient-to-br from-pink-500 to-purple-600 rounded-full flex items-center justify-center">
            <Icon size={40} className="text-white" />
          </div>

          {/* Title & Description */}
          <div className="space-y-2">
            <h2 className="text-2xl font-heading font-bold text-white">
              {title}
            </h2>
            <p className="text-zinc-400">
              {description}
            </p>
          </div>

          {/* Benefits List */}
          <ul className="text-left space-y-3">
            {benefits.map((benefit, idx) => {
              const BenefitIcon = benefit.icon;
              return (
                <li key={idx} className="flex items-center gap-3 text-zinc-300">
                  <div className="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center flex-shrink-0">
                    <BenefitIcon size={16} className="text-pink-400" />
                  </div>
                  <span className="text-sm">{benefit.text}</span>
                </li>
              );
            })}
          </ul>

          {/* Action Buttons */}
          <div className="space-y-3 pt-2">
            <Link to="/register" className="block">
              <Button variant="primary" className="w-full flex items-center justify-center gap-2">
                <UserPlus size={18} />
                Create Free Account
              </Button>
            </Link>

            <Link to="/login" className="block">
              <Button variant="secondary" className="w-full">
                Already have an account? Login
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
