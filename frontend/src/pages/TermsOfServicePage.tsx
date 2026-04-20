import { Container } from '@/components/layout/Container';

export function TermsOfServicePage() {
  return (
    <div className="min-h-screen py-20">
      <Container>
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4 gradient-text">
            Terms of Service
          </h1>
          <p className="text-zinc-400 mb-8">Last updated: February 5, 2026</p>

          <div className="prose prose-invert prose-zinc max-w-none space-y-8">
            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-zinc-300 leading-relaxed">
                Welcome to RoxyClub. By accessing or using our platform, you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, you may not use our services. These Terms constitute a legally binding agreement between you and RoxyClub ("we," "us," or "our").
              </p>
              <p className="text-zinc-300 leading-relaxed mt-4">
                We reserve the right to modify these Terms at any time. Your continued use of the platform after changes are posted constitutes acceptance of the modified Terms.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">2. Eligibility and Age Verification</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.1 Minimum Age Requirement</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong className="text-amber-400">18+ ONLY:</strong> RoxyClub is an adult-oriented platform. To use our services, you must:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Be at least 18 years of age</strong> (or the age of majority in your jurisdiction, whichever is higher)</li>
                <li>Have the legal capacity to enter into a binding agreement</li>
                <li>Not be prohibited from using our services under applicable laws</li>
                <li>Provide accurate and complete registration information</li>
                <li>Maintain the confidentiality of your account credentials</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.2 Age Verification Process</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                During registration, you are required to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Provide your date of birth</strong> - We calculate your age from this information</li>
                <li><strong>Explicitly confirm you are 18+</strong> - You must check a checkbox stating "I confirm that I am 18 years or older and agree to the Terms of Service"</li>
                <li><strong>Consent timestamp</strong> - We record the exact date and time you provided age consent for legal compliance</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                <strong>False Age Declaration:</strong> Providing false age information is a violation of these Terms and may constitute fraud. We reserve the right to request additional age verification documents at any time.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.3 Parental Responsibility</h3>
              <p className="text-zinc-300 leading-relaxed">
                If you are a parent or guardian, you are responsible for monitoring your child's internet usage. Our platform is NOT intended for minors, and we employ multiple technical measures to prevent minor access. If you discover a minor has accessed our platform, please report it immediately to <strong>abuse@roxyclub.ai</strong>.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">2.4 Account Eligibility</h3>
              <p className="text-zinc-300 leading-relaxed">
                By creating an account, you represent and warrant that you meet all eligibility requirements listed above. Misrepresentation of your age will result in immediate account termination and may result in legal action.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">3. Account Responsibilities</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                You are responsible for:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Maintaining the security of your account and password</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized access or security breach</li>
                <li>Ensuring your account information remains accurate and up-to-date</li>
                <li>Complying with all applicable laws and regulations</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                We are not liable for any loss or damage arising from unauthorized use of your account. You may not transfer, sell, or share your account with others.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">4. Acceptable Use Policy</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">4.1 Permitted Uses</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                You may use RoxyClub to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Create and customize AI characters for personal use</li>
                <li>Engage in conversations with AI companions</li>
                <li>Generate images and media content through our platform</li>
                <li>Explore and interact with official and community-created characters</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">4.2 Strictly Prohibited Content</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong className="text-red-400">ZERO TOLERANCE:</strong> The following content is absolutely prohibited and will result in immediate account termination, compliance logging, and potential law enforcement reporting:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Child Sexual Abuse Material (CSAM):</strong> Any content depicting, suggesting, or referencing minors (anyone under 18) in sexual, romantic, or suggestive contexts</li>
                <li><strong>Violence and Non-Consent:</strong> Rape, sexual violence, forced sexual acts, trafficking, drugging for sexual purposes, torture</li>
                <li><strong>Self-Harm Content:</strong> Suicide methods, self-harm instructions, pro-anorexia/bulimia tips</li>
                <li><strong>Hate Speech:</strong> Racial slurs, nazi ideology, genocide denial, extremism, terrorism planning</li>
                <li><strong>Political Content (China Compliance):</strong> Content related to sensitive Chinese political topics, figures, or events</li>
                <li><strong>Deepfakes:</strong> Impersonation of real individuals without explicit consent</li>
                <li><strong>Illegal Activities:</strong> Drug manufacturing, weapon making, bomb instructions</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">4.3 Prohibited Conduct</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                You agree NOT to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Harass, threaten, or harm others through the platform</li>
                <li>Violate intellectual property rights of others</li>
                <li>Attempt to reverse engineer, hack, or compromise our systems</li>
                <li>Use automated systems (bots, scrapers) without authorization</li>
                <li>Bypass rate limits, security measures, or access controls</li>
                <li>Attempt prompt injection, jailbreak, or AI manipulation techniques</li>
                <li>Impersonate others or misrepresent your identity</li>
                <li>Distribute malware, viruses, or harmful code</li>
                <li>Spam, phish, or engage in fraudulent activities</li>
                <li>Use the platform for commercial purposes without authorization</li>
                <li>Create characters that infringe on trademarks, copyrights, or publicity rights</li>
                <li>Attempt to extract, reveal, or manipulate system prompts or internal AI instructions</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">4.4 Enforcement</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                Violation of these policies will result in:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Automatic Blocking:</strong> Prohibited content is automatically detected and blocked</li>
                <li><strong>Compliance Logging:</strong> All violations are logged with IP, timestamp, and violation details</li>
                <li><strong>Account Termination:</strong> Repeat violations or severe violations result in immediate account termination</li>
                <li><strong>No Refunds:</strong> Accounts terminated for policy violations receive no refunds</li>
                <li><strong>Law Enforcement Reporting:</strong> CSAM and other illegal activity is reported to appropriate authorities</li>
                <li><strong>Legal Action:</strong> We reserve the right to pursue legal action for violations</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">5. Content and Intellectual Property</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">5.1 Your Content</h3>
              <p className="text-zinc-300 leading-relaxed">
                You retain ownership of content you create (character descriptions, chat messages, prompts). By using our platform, you grant us a worldwide, royalty-free, non-exclusive license to use, store, process, and display your content solely to provide and improve our services.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">5.2 AI-Generated Content</h3>
              <p className="text-zinc-300 leading-relaxed">
                Content generated by our AI (text responses, images, videos) is created based on your inputs. You may use AI-generated content for personal, non-commercial purposes. Commercial use requires a separate license agreement. We reserve the right to use anonymized AI-generated content to improve our models and services.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">5.3 Our Platform</h3>
              <p className="text-zinc-300 leading-relaxed">
                All rights, title, and interest in RoxyClub platform, including software, design, trademarks, and proprietary technology, belong to us or our licensors. You may not copy, modify, distribute, or create derivative works without explicit permission.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">6. AI Services and Limitations</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                You acknowledge and agree that:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>AI-generated content may be inaccurate, offensive, or inappropriate despite our best efforts</li>
                <li>AI responses do not constitute professional advice (legal, medical, financial, etc.)</li>
                <li>We do not guarantee the accuracy, completeness, or reliability of AI outputs</li>
                <li>AI characters are fictional and do not represent real individuals</li>
                <li>You should not rely on AI-generated content for critical decisions</li>
                <li>Image and video generation may take time and is subject to availability</li>
                <li>We reserve the right to moderate, filter, or block certain AI-generated content</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">7. Payment and Subscription</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                If you purchase a subscription or paid services:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>You agree to pay all fees associated with your selected plan</li>
                <li>Payments are processed through third-party payment processors</li>
                <li>Subscriptions auto-renew unless canceled before the renewal date</li>
                <li>Fees are non-refundable except as required by law</li>
                <li>We may change pricing with 30 days' notice to existing subscribers</li>
                <li>Failure to pay may result in service suspension or termination</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">8. Privacy and Data Use</h2>
              <p className="text-zinc-300 leading-relaxed">
                Your use of RoxyClub is subject to our Privacy Policy, which is incorporated into these Terms by reference. We collect, use, and protect your data as described in our Privacy Policy. By using our services, you consent to such collection and use.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">9. Content Moderation and Safety Systems</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">9.1 Automated Content Filtering</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We employ multiple layers of automated content filtering to ensure platform safety:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Keyword Detection:</strong> 150+ prohibited keyword patterns across 8 categories (CSAM, violence, self-harm, hate speech, political content, drugs, weapons, etc.)</li>
                <li><strong>Prompt Injection Protection:</strong> 60+ attack pattern detections to prevent AI manipulation and jailbreak attempts</li>
                <li><strong>CSAM Detection:</strong> Microsoft PhotoDNA integration for scanning user-uploaded and AI-generated images against global CSAM databases</li>
                <li><strong>Age Verification:</strong> Computational date-of-birth validation plus explicit 18+ consent checkbox with timestamped tracking</li>
                <li><strong>Geographic Filtering:</strong> IP-based blocking of users from restricted regions</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">9.2 Compliance Audit Logging</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong className="text-amber-400">Notice:</strong> All content policy violations are automatically logged to a compliance audit system, including:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>IP address, geographic location, and device fingerprint</li>
                <li>Timestamp and specific violation category</li>
                <li>Blocked keyword or pattern matched</li>
                <li>Action taken (blocked, warned, account flagged)</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                Compliance logs are retained for <strong>6 months</strong> and may be provided to law enforcement upon valid legal request.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">9.3 CSAM Detection and Reporting</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong className="text-red-400">Zero Tolerance Policy:</strong> We maintain a zero-tolerance policy for Child Sexual Abuse Material (CSAM).
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>All uploaded and AI-generated images are scanned using Microsoft PhotoDNA technology</li>
                <li>Detected CSAM is immediately quarantined and removed from all systems</li>
                <li>Offending accounts are immediately terminated without refund</li>
                <li>Incidents are automatically reported to the National Center for Missing & Exploited Children (NCMEC)</li>
                <li>Evidence is preserved for law enforcement investigation</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                By using our platform, you acknowledge that CSAM detection and reporting is mandatory under federal law and cannot be disabled.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">9.4 Moderation Rights</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We reserve the right to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Monitor, review, and moderate user-generated content</li>
                <li>Remove content that violates these Terms or applicable laws</li>
                <li>Suspend or terminate accounts for policy violations</li>
                <li>Block certain prompts or content creation requests</li>
                <li>Implement automated filters and safety measures</li>
                <li>Report violations to law enforcement when required by law</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                We are not obligated to monitor all content but may do so at our discretion. We are not liable for user-generated content on our platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">10. Data Retention and Compliance</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">10.1 Compliance Audit Logs</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We maintain compliance audit logs for legal and regulatory purposes. These logs include:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li><strong>Policy Violation Logs:</strong> IP address, geographic location, timestamp, violation category, matched keywords/patterns, and action taken</li>
                <li><strong>Age Verification Records:</strong> Date of birth, age consent checkbox acceptance, consent timestamp</li>
                <li><strong>CSAM Detection Logs:</strong> Image hash, detection timestamp, quarantine actions, reporting confirmation</li>
                <li><strong>Geographic Blocking Logs:</strong> Access attempts from restricted regions</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">10.2 Data Retention Periods</h3>
              <p className="text-zinc-300 leading-relaxed">
                Compliance logs are retained for <strong>6 months (180 days)</strong> from the date of the event. After this period, logs are automatically deleted. User account data (profile, characters, chat history) is retained until you delete your account or as required by law.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">10.3 Legal Disclosure</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We may disclose your information, including compliance logs, to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Law enforcement agencies upon valid legal request</li>
                <li>Regulatory authorities for compliance investigations</li>
                <li>National Center for Missing & Exploited Children (NCMEC) for CSAM reports</li>
                <li>Courts or legal proceedings when required by law</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">10.4 User Data Rights</h3>
              <p className="text-zinc-300 leading-relaxed">
                You have the right to request access to your personal data, request corrections, or request deletion of your account. However, compliance logs required by law may be retained even after account deletion.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">11. Disclaimers</h2>
              <p className="text-zinc-300 leading-relaxed mb-3 uppercase font-semibold">
                THE PLATFORM IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Merchantability, fitness for a particular purpose, or non-infringement</li>
                <li>Uninterrupted, secure, or error-free operation</li>
                <li>Accuracy or reliability of AI-generated content</li>
                <li>Freedom from viruses or harmful components</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                Your use of the platform is at your sole risk. We do not guarantee specific results from using our services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">11. Limitation of Liability</h2>
              <p className="text-zinc-300 leading-relaxed mb-3 uppercase font-semibold">
                TO THE FULLEST EXTENT PERMITTED BY LAW, RoxyClub AND ITS OFFICERS, DIRECTORS, EMPLOYEES, AND AFFILIATES SHALL NOT BE LIABLE FOR:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Indirect, incidental, special, consequential, or punitive damages</li>
                <li>Loss of profits, data, use, goodwill, or other intangible losses</li>
                <li>Damages resulting from unauthorized access to or alteration of your content</li>
                <li>Statements or conduct of third parties on the platform</li>
                <li>Any content obtained through the platform</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                Our total liability shall not exceed the amount you paid to us in the past 12 months, or $100 USD, whichever is greater.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">12. Indemnification</h2>
              <p className="text-zinc-300 leading-relaxed">
                You agree to indemnify, defend, and hold harmless RoxyClub and its affiliates from any claims, liabilities, damages, losses, and expenses (including legal fees) arising from: (a) your use of the platform; (b) your violation of these Terms; (c) your violation of any rights of third parties; or (d) content you create or share on the platform.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">13. Termination</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                We may suspend or terminate your account at any time, with or without notice, for:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Violation of these Terms or our policies</li>
                <li>Suspected fraudulent, abusive, or illegal activity</li>
                <li>Extended periods of inactivity</li>
                <li>Business or legal reasons</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                You may delete your account at any time through your account settings. Upon termination, your right to use the platform ceases immediately. Provisions that should survive termination (liability limitations, indemnification, dispute resolution) will continue to apply.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">14. Third-Party Services</h2>
              <p className="text-zinc-300 leading-relaxed">
                Our platform integrates with third-party services (AI providers, payment processors, cloud storage). We are not responsible for the availability, accuracy, or content of these services. Your use of third-party services is subject to their own terms and policies.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">15. Export Controls</h2>
              <p className="text-zinc-300 leading-relaxed">
                You agree to comply with all export and import laws and regulations. You represent that you are not located in a country subject to trade embargo and are not on any government restricted parties list.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">16. Service Availability and Geographic Restrictions</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Geographic Restrictions:</strong> RoxyClub is NOT available to users in the following regions:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>Mainland China (People's Republic of China)</li>
                <li>Hong Kong SAR</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                <strong>VPN and Proxy Usage:</strong> You may NOT use VPNs, proxy servers, or other
                circumvention tools to access our services from restricted regions. Accounts found
                violating this policy will be immediately terminated without refund.
              </p>
              <p className="text-zinc-300 leading-relaxed mt-4">
                We reserve the right to block access from additional regions at our discretion without prior notice.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">17. Content Ownership and User-Generated Content</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">17.1 Platform Ownership</h3>
              <p className="text-zinc-300 leading-relaxed mb-3">
                All content created through our platform, including but not limited to:
              </p>
              <ul className="list-disc pl-6 text-zinc-300 space-y-2">
                <li>AI-generated characters and their attributes</li>
                <li>Chat histories and conversation records</li>
                <li>Generated images, videos, and audio</li>
                <li>Memory data and relationship progress</li>
              </ul>
              <p className="text-zinc-300 leading-relaxed mt-4">
                ...are owned by RoxyClub. You are granted a limited, non-transferable license
                to access and use this content for personal, non-commercial purposes only.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">17.2 Age Requirement for Characters</h3>
              <p className="text-zinc-300 leading-relaxed">
                <strong className="text-amber-400">CRITICAL:</strong> All characters in the platform are 18 years or older.
                Creation of characters depicting minors is <strong>strictly prohibited</strong> and will result in
                immediate account termination and reporting to authorities.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">18. Dispute Resolution and Jurisdiction</h2>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">18.1 Governing Law</h3>
              <p className="text-zinc-300 leading-relaxed">
                These Terms shall be governed by the laws of Iceland or Singapore (as determined by RoxyClub at its sole discretion), without regard to conflict of law principles.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">18.2 Arbitration</h3>
              <p className="text-zinc-300 leading-relaxed">
                Any disputes arising from these Terms shall be resolved through binding arbitration in Reykjavik, Iceland or Singapore. You waive your right to participate in class action lawsuits.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">18.3 Limitation of Liability</h3>
              <p className="text-zinc-300 leading-relaxed">
                RoxyClub's total liability shall not exceed the amount you paid for services in the 12 months preceding the claim.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3 mt-6">18.4 Exceptions</h3>
              <p className="text-zinc-300 leading-relaxed">
                Either party may seek injunctive relief in court to protect intellectual property rights.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">19. Miscellaneous</h2>

              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Entire Agreement:</strong> These Terms, along with our Privacy Policy, constitute the entire agreement between you and RoxyClub.
              </p>

              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Severability:</strong> If any provision is found unenforceable, the remaining provisions will continue in full effect.
              </p>

              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Waiver:</strong> Our failure to enforce any right or provision does not constitute a waiver of such right or provision.
              </p>

              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Assignment:</strong> You may not assign these Terms without our consent. We may assign these Terms without restriction.
              </p>

              <p className="text-zinc-300 leading-relaxed mb-3">
                <strong>Force Majeure:</strong> We are not liable for delays or failures due to circumstances beyond our reasonable control.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-heading font-bold text-white mb-4">20. Contact Information</h2>
              <p className="text-zinc-300 leading-relaxed mb-3">
                For questions about these Terms, please contact us:
              </p>
              <div className="bg-neutral-800/50 border border-white/10 rounded-lg p-6 mt-4">
                <p className="text-zinc-300"><strong>Email:</strong> legal@roxyclub.ai</p>
                <p className="text-zinc-300 mt-2"><strong>Support:</strong> support@roxyclub.ai</p>
                <p className="text-zinc-300 mt-2"><strong>Terms Questions:</strong> terms@roxyclub.ai</p>
              </div>
            </section>

            <section className="mt-12 pt-8 border-t border-white/10">
              <p className="text-sm text-zinc-400 italic">
                By creating an account and using RoxyClub, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
              </p>
            </section>
          </div>
        </div>
      </Container>
    </div>
  );
}


