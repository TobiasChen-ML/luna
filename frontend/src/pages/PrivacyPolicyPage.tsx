import { Container } from '@/components/layout/Container';

export function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen py-20">
      <Container>
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4 gradient-text">
            Privacy Policy
          </h1>
          <p className="text-zinc-400 mb-8">Last updated: December 16, 2025</p>

          <div className="prose prose-invert prose-zinc max-w-none space-y-8">
            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">1. Introduction</h2>
              <p className="text-zinc-300 leading-relaxed">
                Welcome to RoxyClub ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI companion platform and services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">2. Information We Collect</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.1 Personal Information</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                When you register for an account, we collect:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Email address</li>
                <li>Account credentials (encrypted)</li>
                <li>Age verification status</li>
                <li>Profile information you choose to provide</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.2 User-Generated Content</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We collect and store:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>AI characters you create (appearance, personality traits, backgrounds)</li>
                <li>Chat conversations with AI characters</li>
                <li>Images and videos generated through our platform</li>
                <li>Character customization preferences</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.3 Usage Data</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We automatically collect:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Device information (browser type, operating system)</li>
                <li>IP address and location data</li>
                <li>Usage patterns and interaction data</li>
                <li>Performance metrics and error logs</li>
                <li>Cookies and similar tracking technologies</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">3. How We Use Your Information</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We use your information to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Provide, operate, and maintain our AI companion services</li>
                <li>Process your requests and personalize your experience</li>
                <li>Generate AI responses and media content based on your interactions</li>
                <li>Improve our AI models and service quality</li>
                <li>Send you updates, notifications, and marketing communications (with your consent)</li>
                <li>Detect and prevent fraud, abuse, and technical issues</li>
                <li>Comply with legal obligations and enforce our Terms of Service</li>
                <li>Analyze usage patterns to enhance platform features</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">4. Data Storage and Security</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We implement industry-standard security measures to protect your data:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Data is stored using Firebase/Firestore with encryption at rest</li>
                <li>All communications are encrypted using SSL/TLS protocols</li>
                <li>Passwords are hashed and never stored in plain text</li>
                <li>Media files are stored on secure cloud infrastructure (Cloudflare R2)</li>
                <li>Regular security audits and vulnerability assessments</li>
                <li>Access controls and authentication mechanisms</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                While we strive to protect your data, no method of transmission over the internet is 100% secure. You acknowledge the inherent security risks of providing information online.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">5. Third-Party Services</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We use third-party services to operate our platform:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Firebase Authentication:</strong> User authentication and identity management</li>
                <li><strong>Firestore:</strong> Database storage for user data and content</li>
                <li><strong>AI Providers (DeepSeek, ChatGPT/Grasi):</strong> Natural language processing and conversation generation</li>
                <li><strong>Image Generation APIs (Nano Banana/Grasi):</strong> AI-powered image creation</li>
                <li><strong>Cloudflare R2:</strong> Media file storage and delivery</li>
                <li><strong>Analytics Services:</strong> Platform usage analysis and improvement</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                These providers have their own privacy policies. We encourage you to review them. We share only the minimum necessary data with these services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">6. Data Sharing and Disclosure</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We do not sell your personal data. We may share your information only in these circumstances:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>With your consent:</strong> When you explicitly authorize us to share specific information</li>
                <li><strong>Service providers:</strong> Third-party vendors who assist in operating our platform</li>
                <li><strong>Legal requirements:</strong> When required by law, court order, or government request</li>
                <li><strong>Business transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                <li><strong>Safety and protection:</strong> To protect rights, property, or safety of RoxyClub, our users, or the public</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">7. Your Privacy Rights</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                Depending on your location, you may have the following rights:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Access:</strong> Request copies of your personal data</li>
                <li><strong>Correction:</strong> Request correction of inaccurate or incomplete data</li>
                <li><strong>Deletion:</strong> Request deletion of your personal data (subject to legal obligations)</li>
                <li><strong>Data portability:</strong> Request transfer of your data to another service</li>
                <li><strong>Opt-out:</strong> Unsubscribe from marketing communications</li>
                <li><strong>Restrict processing:</strong> Request limitation on how we use your data</li>
                <li><strong>Object:</strong> Object to our processing of your personal data</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                To exercise these rights, please contact us at privacy@roxyclub.ai.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">8. Data Retention</h2>
              <p className="text-zinc-300 leading-relaxed">
                We retain your personal data only as long as necessary to provide our services and comply with legal obligations. When you delete your account, we will delete or anonymize your personal data within 30 days, except where we must retain it for legal, accounting, or security purposes.
              </p>
              <p className="text-zinc-300 leading-relaxed mt-4">
                Chat histories and generated content may be retained for service improvement and model training purposes unless you request deletion.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">9. Children's Privacy</h2>
              <p className="text-zinc-300 leading-relaxed">
                Our services are intended for users who are at least 18 years old. We do not knowingly collect personal information from children under 18. If we discover that we have collected data from a child under 18, we will delete that information immediately. If you believe we have collected information from a minor, please contact us.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">10. International Data Transfers</h2>
              <p className="text-zinc-300 leading-relaxed">
                Your information may be transferred to and processed in countries other than your country of residence. These countries may have different data protection laws. By using our services, you consent to the transfer of your information to these countries. We ensure appropriate safeguards are in place to protect your data.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">11. Cookies and Tracking Technologies</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We use cookies and similar technologies to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Maintain your login session</li>
                <li>Remember your preferences</li>
                <li>Analyze usage patterns</li>
                <li>Improve platform performance</li>
                <li>Deliver personalized content</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                You can control cookies through your browser settings. Note that disabling cookies may affect platform functionality.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">12. AI-Specific Privacy Considerations</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                Because our platform uses artificial intelligence:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Your conversations may be analyzed to improve AI response quality</li>
                <li>Anonymized chat data may be used to train and enhance our AI models</li>
                <li>AI-generated content (images, videos, text) is created based on your inputs</li>
                <li>We do not use your personal data to train third-party AI models without your consent</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">13. Changes to This Privacy Policy</h2>
              <p className="text-zinc-300 leading-relaxed">
                We may update this Privacy Policy periodically to reflect changes in our practices or legal requirements. We will notify you of material changes by posting the updated policy on our platform and updating the "Last updated" date. Your continued use of our services after changes constitutes acceptance of the updated policy.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">14. Contact Us</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                If you have questions or concerns about this Privacy Policy or our data practices, please contact us:
              </p>
              <div className="bg-neutral-800/50 border border-white/10 rounded-lg p-6 mt-4">
                <p className="text-zinc-300"><strong>Email:</strong> privacy@roxyclub.ai</p>
                <p className="text-zinc-300 mt-2"><strong>Support:</strong> support@roxyclub.ai</p>
                <p className="text-zinc-300 mt-2"><strong>Data Protection Officer:</strong> dpo@roxyclub.ai</p>
              </div>
            </section>

            <section className="mt-12 pt-8 border-t border-white/10">
              <p className="text-sm text-zinc-400 italic">
                By using RoxyClub, you acknowledge that you have read and understood this Privacy Policy and agree to its terms.
              </p>
            </section>
          </div>
        </div>
      </Container>
    </div>
  );
}


