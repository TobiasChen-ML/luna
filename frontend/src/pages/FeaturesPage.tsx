import { useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout';
import { Button, GameplayStepCard } from '@/components/common';
import { BookOpen, GitBranch, Unlock, Heart, MessageCircle, Image, Mic, Sparkles, Compass } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function FeaturesPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate(isAuthenticated ? '/chat' : '/register');
  };
  return (
    <div className="min-h-screen pt-24 pb-20">
      <Container>
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-heading font-bold mb-6">
            Story-First <span className="gradient-text">Gameplay</span>
          </h1>
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
            This is not a static chat. It is a branching story loop with progression,
            scene unlocks, and character arcs.
          </p>
        </div>

        {/* Gameplay Loop */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-20">
          <GameplayStepCard
            step="01"
            title="Select a Character"
            description="Every character has an opening story hook and tone."
            icon={<Sparkles size={20} className="text-white" />}
          />
          <GameplayStepCard
            step="02"
            title="Enter the Scene"
            description="Start from a curated moment that sets the stakes."
            icon={<BookOpen size={20} className="text-white" />}
          />
          <GameplayStepCard
            step="03"
            title="Branch the Dialogue"
            description="Choices shift the mood and open different paths."
            icon={<GitBranch size={20} className="text-white" />}
          />
          <GameplayStepCard
            step="04"
            title="Unlock New Moments"
            description="Relationship progress reveals new scenes and content."
            icon={<Unlock size={20} className="text-white" />}
          />
        </div>

        {/* Core Mechanics */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <Heart size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Relationship Levels</h3>
            <p className="text-zinc-400">
              Build affinity over time to unlock deeper tones and scenes.
            </p>
          </div>

          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <Compass size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Scene Progression</h3>
            <p className="text-zinc-400">
              Chapters and moments unlock as you move through the arc.
            </p>
          </div>

          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <MessageCircle size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Responsive Dialogue</h3>
            <p className="text-zinc-400">
              Fast, context-aware replies keep the pacing tight.
            </p>
          </div>

          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <Image size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Visual Moments</h3>
            <p className="text-zinc-400">
              Unlock images and video that match the story beats.
            </p>
          </div>

          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <Mic size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Voice Immersion</h3>
            <p className="text-zinc-400">
              Hear your companion and turn scenes into moments.
            </p>
          </div>

          <div className="card-glass space-y-4">
            <div className="w-16 h-16 bg-gradient-primary rounded-2xl flex items-center justify-center">
              <Sparkles size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-heading font-bold">Replayable Routes</h3>
            <p className="text-zinc-400">
              Make new choices to explore alternate paths and endings.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="card-glass text-center space-y-8 p-12 max-w-3xl mx-auto">
          <h2 className="text-4xl font-heading font-bold">
            Ready to Play Your First Story?
          </h2>
          <p className="text-xl text-zinc-400">
            Pick a character, jump into the opening scene, and start branching.
          </p>
          <Button variant="primary" size="lg" onClick={handleGetStarted}>
            Start Free
          </Button>
        </div>
      </Container>
    </div>
  );
}
