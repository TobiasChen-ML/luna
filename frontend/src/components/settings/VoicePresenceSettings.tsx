/**
 * Voice Presence Settings Component
 * Allows users to control Vocal Presence parameters
 */

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { api } from '@/services/api';

interface PresencePreferences {
  enable_presence: boolean;
  max_breathiness: number;
  max_proximity_effect: number;
  allow_intimate_sounds: boolean;
  preferred_scene_type: 'public' | 'semi_private' | 'private';
}

const DEFAULT_PREFERENCES: PresencePreferences = {
  enable_presence: true,
  max_breathiness: 0.3,
  max_proximity_effect: 0.2,
  allow_intimate_sounds: false,
  preferred_scene_type: 'public'
};

export const VoicePresenceSettings: React.FC = () => {
  const [preferences, setPreferences] = useState<PresencePreferences>(DEFAULT_PREFERENCES);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Load preferences from localStorage on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await api.get('/auth/me/preferences');
        const backendPrefs = response.data?.voice_presence;
        if (backendPrefs) {
          setPreferences({ ...DEFAULT_PREFERENCES, ...backendPrefs });
          localStorage.setItem('voice_presence_preferences', JSON.stringify({ ...DEFAULT_PREFERENCES, ...backendPrefs }));
          return;
        }
      } catch (error) {
        console.warn('Failed to load preferences from backend, using local cache:', error);
      }

      const saved = localStorage.getItem('voice_presence_preferences');
      if (saved) {
        try {
          setPreferences({ ...DEFAULT_PREFERENCES, ...JSON.parse(saved) });
        } catch (e) {
          console.error('Failed to load preferences from localStorage:', e);
        }
      }
    };

    void loadPreferences();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage('');

    try {
      // Save to localStorage
      localStorage.setItem('voice_presence_preferences', JSON.stringify(preferences));

      // Sync to backend
      await api.put('/auth/me/preferences', {
        voice_presence: preferences,
      });

      setSaveMessage('Preferences saved successfully!');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      setSaveMessage('Failed to save preferences');
      console.error('Save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setPreferences(DEFAULT_PREFERENCES);
  };

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h3 className="text-xl font-semibold mb-2">Voice Presence Settings</h3>
        <p className="text-sm text-gray-600">
          Control how natural and intimate the AI voice sounds. Higher values = more emotional presence.
        </p>
      </div>

      {/* Enable/Disable Presence */}
      <div className="flex items-center justify-between">
        <div>
          <label className="font-medium">Enable Vocal Presence</label>
          <p className="text-sm text-gray-500">
            Use advanced voice parameters for more natural speech
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={preferences.enable_presence}
            onChange={(e) => setPreferences({ ...preferences, enable_presence: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Scene Type Preference */}
      <div>
        <label className="block font-medium mb-2">Preferred Scene Type</label>
        <select
          value={preferences.preferred_scene_type}
          onChange={(e) => setPreferences({
            ...preferences,
            preferred_scene_type: e.target.value as PresencePreferences['preferred_scene_type']
          })}
          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={!preferences.enable_presence}
        >
          <option value="public">Public (Safe, minimal intimacy)</option>
          <option value="semi_private">Semi-Private (Moderate intimacy)</option>
          <option value="private">Private (Full emotional range)</option>
        </select>
        <p className="text-xs text-gray-500 mt-1">
          Public scenes enforce safety limits on breathiness and proximity
        </p>
      </div>

      {/* Max Breathiness */}
      <div>
        <label className="block font-medium mb-2">
          Max Breathiness: {preferences.max_breathiness.toFixed(2)}
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={preferences.max_breathiness}
          onChange={(e) => setPreferences({ ...preferences, max_breathiness: parseFloat(e.target.value) })}
          className="w-full"
          disabled={!preferences.enable_presence}
        />
        <p className="text-xs text-gray-500 mt-1">
          Controls how breathy/whispery the voice sounds (0 = crisp, 1 = very breathy)
        </p>
      </div>

      {/* Max Proximity Effect */}
      <div>
        <label className="block font-medium mb-2">
          Max Proximity Effect: {preferences.max_proximity_effect.toFixed(2)}
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={preferences.max_proximity_effect}
          onChange={(e) => setPreferences({ ...preferences, max_proximity_effect: parseFloat(e.target.value) })}
          className="w-full"
          disabled={!preferences.enable_presence}
        />
        <p className="text-xs text-gray-500 mt-1">
          Bass boost effect simulating physical closeness (0 = distant, 1 = very close)
        </p>
      </div>

      {/* Allow Intimate Sounds */}
      <div className="flex items-center justify-between">
        <div>
          <label className="font-medium">Allow Intimate Non-Verbal Sounds</label>
          <p className="text-sm text-gray-500">
            Breath sounds, mouth sounds, sighs (only in private scenes)
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={preferences.allow_intimate_sounds}
            onChange={(e) => setPreferences({ ...preferences, allow_intimate_sounds: e.target.checked })}
            className="sr-only peer"
            disabled={!preferences.enable_presence}
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Save Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          onClick={handleSave}
          disabled={isSaving || !preferences.enable_presence}
          className="flex-1"
        >
          {isSaving ? 'Saving...' : 'Save Preferences'}
        </Button>
        <Button
          onClick={handleReset}
          variant="outline"
          disabled={isSaving}
          className="flex-1"
        >
          Reset to Default
        </Button>
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div className={`text-center p-2 rounded ${
          saveMessage.includes('success') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {saveMessage}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
        <p className="font-medium text-blue-900 mb-1">How Presence Works:</p>
        <ul className="text-blue-800 space-y-1 list-disc list-inside">
          <li>Relationship stage automatically adjusts voice parameters</li>
          <li>Stranger: Formal, clear speech with minimal intimacy</li>
          <li>Intimate: Softer, breathy, with emotional nuances</li>
          <li>Public scenes enforce safety limits regardless of relationship</li>
          <li>Your preferences set maximum boundaries, never exceeded</li>
        </ul>
      </div>
    </Card>
  );
};
