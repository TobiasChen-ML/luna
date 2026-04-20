import { useWizard } from '@/contexts/CharacterWizardContext';
import { WizardStep } from '../WizardStep';
import { Input } from '@/components/common';

const professionSuggestions = [
  'Designer',
  'Artist',
  'Writer',
  'Teacher',
  'Engineer',
  'Doctor',
  'Chef',
  'Musician',
  'Student',
  'Entrepreneur',
];

const hobbySuggestions = ['Reading', 'Art', 'Music', 'Sports', 'Gaming', 'Cooking', 'Travel', 'Photography'];

const listToString = (items?: string[]) => (items || []).join(', ');

const parseList = (value: string) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

export function Step7BackgroundBoundaries() {
  const { characterData, updateNestedField } = useWizard();

  const addHobby = (hobby: string) => {
    const current = characterData.background.hobbies || [];
    if (!current.includes(hobby) && current.length < 5) {
      updateNestedField('background.hobbies', [...current, hobby]);
    }
  };

  const removeHobby = (hobby: string) => {
    const current = characterData.background.hobbies || [];
    updateNestedField(
      'background.hobbies',
      current.filter((h) => h !== hobby)
    );
  };

  return (
    <WizardStep
      title="Background and Boundaries"
      description="Optional details that shape tone, limits, and history"
    >
      <div className="space-y-10">
        <div className="space-y-6 p-6 rounded-lg bg-white/5 border border-white/10">
          <h3 className="text-lg font-semibold">Background Details</h3>

          <div>
            <Input
              label="Profession"
              placeholder="e.g., Designer, Artist, Teacher"
              value={characterData.background.profession || ''}
              onChange={(e) => updateNestedField('background.profession', e.target.value)}
              helperText="What does your character do for a living?"
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {professionSuggestions.map((prof) => (
                <button
                  key={prof}
                  onClick={() => updateNestedField('background.profession', prof)}
                  className="px-3 py-1 text-xs bg-white/10 hover:bg-white/20 rounded-full transition-colors"
                >
                  {prof}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Hobbies and Interests
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {(characterData.background.hobbies || []).map((hobby) => (
                <button
                  key={hobby}
                  onClick={() => removeHobby(hobby)}
                  className="px-3 py-1.5 bg-primary-500 text-white rounded-full text-sm hover:bg-primary-600 transition-colors"
                >
                  {hobby}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {hobbySuggestions.map((hobby) => (
                <button
                  key={hobby}
                  onClick={() => addHobby(hobby)}
                  disabled={(characterData.background.hobbies || []).includes(hobby)}
                  className="px-3 py-1 text-xs bg-white/10 hover:bg-white/20 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {hobby}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Backstory (Optional)
            </label>
            <textarea
              value={characterData.background.backstory || ''}
              onChange={(e) => updateNestedField('background.backstory', e.target.value)}
              placeholder="Write a brief backstory for your character"
              rows={4}
              className="input resize-none"
            />
            <p className="mt-1 text-sm text-zinc-500">
              This helps create more contextual and personalized conversations.
            </p>
          </div>
        </div>

        <div className="space-y-4 p-6 rounded-lg bg-white/5 border border-white/10">
          <h3 className="text-lg font-semibold">Preferences</h3>
          <Input
            label="Likes"
            placeholder="e.g., coffee, rain, jazz"
            value={listToString(characterData.preferences?.likes)}
            onChange={(e) => updateNestedField('preferences.likes', parseList(e.target.value))}
            helperText="Comma-separated list"
          />
          <Input
            label="Dislikes"
            placeholder="e.g., loud crowds, dishonesty"
            value={listToString(characterData.preferences?.dislikes)}
            onChange={(e) => updateNestedField('preferences.dislikes', parseList(e.target.value))}
            helperText="Comma-separated list"
          />
        </div>

        <div className="space-y-6 p-6 rounded-lg bg-white/5 border border-white/10">
          <h3 className="text-lg font-semibold">Chat Rules and Boundaries</h3>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Safety Level</label>
              <select
                value={characterData.chatRules?.mandatory?.safety_level || 'R13'}
                onChange={(e) => updateNestedField('chatRules.mandatory.safety_level', e.target.value)}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-black focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="R13" className="text-black">R13</option>
                <option value="ADULT" className="text-black">ADULT</option>
              </select>
            </div>
            <Input
              label="Disallowed Topics"
              placeholder="e.g., politics, medical, legal"
              value={listToString(characterData.chatRules?.mandatory?.disallowed_topics)}
              onChange={(e) => updateNestedField('chatRules.mandatory.disallowed_topics', parseList(e.target.value))}
              helperText="Comma-separated list"
            />
          </div>

          <Input
            label="Tone of Voice"
            placeholder="e.g., warm_friendly"
            value={characterData.chatRules?.anchors?.tone_voice || ''}
            onChange={(e) => updateNestedField('chatRules.anchors.tone_voice', e.target.value)}
          />

          <div className="grid md:grid-cols-2 gap-4">
            <Input
              label="Keywords"
              placeholder="e.g., playful, gentle"
              value={listToString(characterData.chatRules?.anchors?.keywords)}
              onChange={(e) => updateNestedField('chatRules.anchors.keywords', parseList(e.target.value))}
              helperText="Comma-separated list"
            />
            <Input
              label="Quirks"
              placeholder="e.g., speaks softly, uses ellipses"
              value={listToString(characterData.chatRules?.anchors?.quirks)}
              onChange={(e) => updateNestedField('chatRules.anchors.quirks', parseList(e.target.value))}
              helperText="Comma-separated list"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <Input
              label="Catchphrases"
              placeholder="e.g., stay close"
              value={listToString(characterData.chatRules?.anchors?.catchphrases)}
              onChange={(e) => updateNestedField('chatRules.anchors.catchphrases', parseList(e.target.value))}
              helperText="Comma-separated list"
            />
            <Input
              label="Secrets"
              placeholder="e.g., hides a past mistake"
              value={listToString(characterData.chatRules?.anchors?.secrets)}
              onChange={(e) => updateNestedField('chatRules.anchors.secrets', parseList(e.target.value))}
              helperText="Comma-separated list"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Interaction Style</label>
            <select
              value={characterData.chatRules?.interaction?.role_type || 'guiding'}
              onChange={(e) => updateNestedField('chatRules.interaction.role_type', e.target.value)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="guiding">Guiding</option>
              <option value="dependent">Dependent</option>
              <option value="passive">Passive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Guidance Notes (Optional)
            </label>
            <textarea
              value={characterData.chatRules?.interaction?.guidance_notes || ''}
              onChange={(e) => updateNestedField('chatRules.interaction.guidance_notes', e.target.value)}
              placeholder="Notes on how the character should respond or guide the conversation"
              rows={3}
              className="input resize-none"
            />
          </div>
        </div>
      </div>
    </WizardStep>
  );
}
