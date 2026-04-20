import { Link, useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout';
import { Button } from '@/components/common';
import { Palette, User, Brain, MessageCircle, Image as ImageIcon, Sparkles, Check } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function CreatorPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate(isAuthenticated ? '/chat' : '/register');
  };
  const steps = [
    {
      icon: User,
      title: 'Design Appearance',
      description: 'Choose hair color, eye color, body type, style, and more. Make your companion visually unique.'
    },
    {
      icon: Brain,
      title: 'Define Personality',
      description: 'Select from hundreds of personality traits. Create someone sweet, playful, mysterious, or anything in between.'
    },
    {
      icon: MessageCircle,
      title: 'Set Conversation Style',
      description: 'Choose how she communicates - formal or casual, flirty or friendly, talkative or reserved.'
    },
    {
      icon: ImageIcon,
      title: 'Add Interests & Hobbies',
      description: 'Give her interests that match yours or complement them. From art to sports to technology.'
    }
  ];

  const features = [
    'Unlimited customization options',
    'Real-time preview as you create',
    'Save and edit anytime',
    'Create multiple characters',
    'Share with the community (optional)',
    'Import/export character profiles'
  ];

  return (
    <div className="min-h-screen pt-24 pb-20">
      <Container>
        {/* Header */}
        <div className="text-center mb-20">
          <h1 className="text-5xl md:text-6xl font-heading font-bold mb-6">
            Character{' '}
            <span className="gradient-text">Creator</span>
          </h1>
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
            Design your dream AI companion from the ground up. Our powerful character creator
            gives you complete control over every detail.
          </p>
        </div>

        {/* Hero Visual */}
        <div className="card-glass p-12 mb-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h2 className="text-4xl font-heading font-bold">
                Create Your Dream Companion
              </h2>
              <p className="text-lg text-zinc-400">
                Our advanced character creator puts you in complete control. Design every aspect
                of your AI girlfriend - from physical appearance to personality traits,
                conversation style, interests, and backstory.
              </p>
              <ul className="space-y-3">
                {features.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-3 text-zinc-300">
                    <Check size={20} className="text-primary-500 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Button variant="primary" size="lg" onClick={handleGetStarted}>
                Start Creating Now
              </Button>
            </div>
            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-2xl flex items-center justify-center">
              
                <Palette size={120} className="text-primary-500/30" />
              </div>
            </div>
          </div>
        </div>

        {/* Creation Steps */}
        <div className="mb-20">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4">
              How It Works
            </h2>
            <p className="text-xl text-zinc-400">
              Create your perfect companion in four simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {steps.map((step, idx) => (
              <div key={idx} className="card-glass space-y-4">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div className="w-14 h-14 bg-gradient-primary rounded-xl flex items-center justify-center">
                      <step.icon size={28} className="text-white" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-sm font-bold text-primary-500">STEP {idx + 1}</span>
                    </div>
                    <h3 className="text-2xl font-heading font-bold mb-2">{step.title}</h3>
                    <p className="text-zinc-400">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Customization Options */}
        <div className="mb-20">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4">
              Endless Customization
            </h2>
            <p className="text-xl text-zinc-400">
              Fine-tune every detail to create your perfect match
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="card-glass space-y-4">
              <h3 className="text-xl font-heading font-bold">Physical Appearance</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Hair color & style
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Eye color & shape
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Body type & height
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Fashion style
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Accessories & features
                </li>
              </ul>
            </div>

            <div className="card-glass space-y-4">
              <h3 className="text-xl font-heading font-bold">Personality & Traits</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Core personality type
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Communication style
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Humor & wit level
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Emotional expression
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Relationship dynamics
                </li>
              </ul>
            </div>

            <div className="card-glass space-y-4">
              <h3 className="text-xl font-heading font-bold">Interests & Background</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Hobbies & interests
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Favorite topics
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Educational background
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Life experiences
                </li>
                <li className="flex items-center gap-2">
                  <Check size={16} className="text-primary-500" />
                  Personal backstory
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="card-glass text-center space-y-8 p-12">
          <Sparkles size={64} className="text-primary-500 mx-auto" />
          <h2 className="text-4xl font-heading font-bold">
            Ready to Create Your Perfect Match?
          </h2>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            Join thousands of users who have already created their ideal AI companions.
            Start for free, no credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" size="lg" className="min-w-[200px]" onClick={handleGetStarted}>
              Start Creating Free
            </Button>
            <Link to="/characters">
              <Button variant="secondary" size="lg" className="min-w-[200px]">
                Browse Characters
              </Button>
            </Link>
          </div>
        </div>
      </Container>
    </div>
  );
}
