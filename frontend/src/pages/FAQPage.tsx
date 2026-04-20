import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container } from '@/components/layout';
import { Button } from '@/components/common';
import { Shield, Sparkles, Heart } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function FAQPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [openIdx, setOpenIdx] = useState<string | null>(null);

  const handleGetStarted = () => {
    navigate(isAuthenticated ? '/chat' : '/register');
  };

  const categories = [
    {
      icon: Shield,
      title: 'About RoxyClub.ai',
      faqs: [
        {
          q: 'What is roxyclub.ai?',
          a: 'roxyclub.ai is the best AI girlfriend app, letting you create personalized virtual companions or connect instantly with our realistic AI characters in immersive, uncensored fantasy experiences - all within a safe and private space.',
        },
        {
          q: 'Is roxyclub.ai legitimate and safe to use?',
          a: 'Yes, roxyclub.ai is a legitimate service. It employs encrypted transactions, adheres to GDPR-compliant data privacy standards, and uses discreet billing methods to ensure user safety and confidentiality.',
        },
        {
          q: 'How will roxyclub.ai appear on my bank statements?',
          a: 'Transactions are processed securely and appear under a neutral merchant name. There is no direct reference to roxyclub.ai or its services on your bank statement, ensuring user privacy.',
        },
        {
          q: 'Who uses roxyclub.ai and for what purpose?',
          a: 'roxyclub.ai attracts a wide range of users. Some seek companionship or emotional support, while others use it for storytelling, creative writing, or roleplay. Additionally, AI enthusiasts explore it to better understand conversational AI capabilities.',
        },
      ],
    },
    {
      icon: Sparkles,
      title: 'AI Companions & Features',
      faqs: [
        {
          q: 'What is an AI Companion and can I create my own?',
          a: "An AI Companion is a virtual character powered by artificial intelligence that can converse, respond to emotional cues, and evolve with ongoing interactions. With roxyclub.ai, users can fully personalize their companion's appearance, behavior, and preferences.",
        },
        {
          q: 'Can I customize my roxyclub.ai experience?',
          a: 'Yes, roxyclub.ai offers robust customization options. Users can design their own companions through the "Create My AI Girlfriend" feature, selecting preferences such as ethnicity, hairstyle, voice, personality traits, and more.',
        },
        {
          q: 'Can my AI Companion send images, video, or voice messages?',
          a: 'Yes, roxyclub.ai supports multimodal interaction. Your companion can engage in voice conversations, generate personalized images, and appear in AI-generated videos tailored to your inputs and preferences.',
        },
        {
          q: 'Can I roleplay with my AI Companion?',
          a: 'Absolutely. roxyclub.ai supports a wide variety of roleplay scenarios, ranging from casual interactions and narrative development to immersive storytelling. The AI adapts dynamically to user prompts and themes. However, be mindful that you are chatting with an AI character who responds based on the conversation you lead. Interactions here are fictional, consenting, and must comply with our Community Guidelines.',
        },
      ],
    },
    {
      icon: Heart,
      title: 'AI Girlfriend Experience',
      faqs: [
        {
          q: 'What is an AI Girlfriend and how does it work?',
          a: 'An AI Girlfriend is a digital character powered by deep learning and emotional intelligence, designed to chat, flirt, and connect with you in meaningful ways. At roxyclub.ai, your AI GF adapts to your style, preferences, and mood, creating a personal experience that feels natural and emotionally real.',
        },
        {
          q: 'Can I choose from different AI Girlfriend personalities?',
          a: "Yes, roxyclub.ai offers a wide selection of prebuilt AI GF characters, each with unique personalities, communication styles, and vibes. Whether you prefer someone sweet, flirty, soft-spoken, or bold, you'll find an AI Girlfriend that matches your energy.",
        },
        {
          q: 'How does my AI GF get to know me?',
          a: 'Your AI Girlfriend learns through conversation. The more you chat, the more she picks up on your preferences, tone, and interests. Over time, she adjusts her responses and behavior to better match your communication style, making each chat more personal.',
        },
        {
          q: 'Is chatting with an AI Girlfriend private and secure?',
          a: 'Absolutely. roxyclub.ai uses end-to-end encryption to keep all AI GF conversations safe and confidential. You have full control over your chat history and can enable two-factor authentication for extra security. Your data is never shared or sold.',
        },
        {
          q: 'Do I need to install anything to talk to my AI GF?',
          a: 'No installation is needed. You can access your AI Girlfriend directly through roxyclub.ai on desktop or mobile, anytime, anywhere. Just sign up, choose your AI GF, and start chatting instantly.',
        },
      ],
    },
  ];

  return (
    <div className="min-h-screen pt-24 pb-20">
      <Container>
        {/* Header */}
        <div className="text-center mb-20">
          <h1 className="text-5xl md:text-6xl font-heading font-bold mb-6">
            Frequently Asked{' '}
            <span className="gradient-text">Questions</span>
          </h1>
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto">
            Everything you need to know about roxyclub.ai and your AI companion experience.
          </p>
        </div>

        {/* FAQ Categories */}
        <div className="space-y-16">
          {categories.map((category, catIdx) => (
            <div key={catIdx}>
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-gradient-primary rounded-xl flex items-center justify-center flex-shrink-0">
                  <category.icon size={24} className="text-white" />
                </div>
                <h2 className="text-3xl font-heading font-bold">{category.title}</h2>
              </div>

              <div className="space-y-6">
                {category.faqs.map((faq, idx) => {
                  const key = `${catIdx}-${idx}`;
                  return (
                    <div
                      key={idx}
                      className="card-glass space-y-3 cursor-pointer"
                      onClick={() => setOpenIdx(openIdx === key ? null : key)}
                    >
                      <h3 className="text-xl font-heading font-bold text-white">{faq.q}</h3>
                      {openIdx === key && (
                        <p className="text-zinc-400 leading-relaxed">{faq.a}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="card-glass text-center space-y-8 p-12 mt-20">
          <h2 className="text-4xl font-heading font-bold">
            Still Have Questions?
          </h2>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            Our support team is here to help you get started with roxyclub.ai.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="primary" size="lg" onClick={handleGetStarted}>
              Start Free
            </Button>
            <a href="mailto:support@roxyclub.ai">
              <Button variant="secondary" size="lg">
                Contact Support
              </Button>
            </a>
          </div>
        </div>
      </Container>
    </div>
  );
}

