import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Container } from '@/components/layout';
import { Button, Card } from '@/components/common';
import { LanguageSwitcher } from '@/i18n';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/services/authService';
import { api } from '@/services/api';
import { Flag, PencilLine, User, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTelegramBackButton } from '@/hooks/useTelegramBackButton';

function maskEmail(email?: string): string {
  if (!email) return '-';
  const [name = '', domain = ''] = email.split('@');
  if (!name || !domain) return email;
  const visible = name.slice(0, 2);
  return `${visible}${'*'.repeat(Math.max(2, Math.min(name.length - 2, 8)))}@${domain}`;
}

function formatTier(tier?: string): string {
  if (!tier) return 'Free';
  return tier.charAt(0).toUpperCase() + tier.slice(1);
}

interface EditModalProps {
  title: string;
  onClose: () => void;
  onSave: () => Promise<void>;
  saving: boolean;
  error: string;
  children: React.ReactNode;
}

function EditModal({ title, onClose, onSave, saving, error, children }: EditModalProps) {
  const { t } = useTranslation('profile');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm rounded-2xl border border-zinc-700 bg-zinc-900 p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button type="button" onClick={onClose} className="text-zinc-400 hover:text-white">
            <X size={20} />
          </button>
        </div>
        <div className="space-y-4">
          {children}
          {error && <p className="text-sm text-rose-400">{error}</p>}
          <div className="flex gap-3 pt-1">
            <Button
              variant="ghost"
              onClick={onClose}
              className="flex-1 border border-zinc-700 text-zinc-300 hover:bg-zinc-800"
            >
              {t('cancel')}
            </Button>
            <Button
              onClick={onSave}
              disabled={saving}
              className="flex-1 bg-rose-500 text-white hover:bg-rose-400 disabled:opacity-50"
            >
              {saving ? (t('saving') || 'Saving…') : t('save')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ProfilePage() {
  const { t } = useTranslation('profile');
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  useTelegramBackButton(() => navigate(-1));

  const [modal, setModal] = useState<'nickname' | 'gender' | 'password' | null>(null);
  const [saving, setSaving] = useState(false);
  const [modalError, setModalError] = useState('');

  const [nicknameVal, setNicknameVal] = useState('');
  const [genderVal, setGenderVal] = useState('');
  const [currentPwVal, setCurrentPwVal] = useState('');
  const [newPwVal, setNewPwVal] = useState('');
  const [confirmPwVal, setConfirmPwVal] = useState('');
  const [feedbackType, setFeedbackType] = useState<'complaint' | 'suggestion'>('complaint');
  const [feedbackContent, setFeedbackContent] = useState('');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackError, setFeedbackError] = useState('');
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  const openModal = (type: 'nickname' | 'gender' | 'password') => {
    setModalError('');
    if (type === 'nickname') setNicknameVal(user?.display_name || '');
    if (type === 'gender') setGenderVal(user?.gender || '');
    if (type === 'password') { setCurrentPwVal(''); setNewPwVal(''); setConfirmPwVal(''); }
    setModal(type);
  };

  const closeModal = () => { setModal(null); setModalError(''); };

  const saveNickname = async () => {
    if (!nicknameVal.trim()) { setModalError(t('errors.nicknameEmpty') || 'Nickname cannot be empty'); return; }
    setSaving(true);
    try {
      await authService.updateProfile({ display_name: nicknameVal.trim() });
      await refreshUser();
      closeModal();
    } catch {
      setModalError(t('errors.nicknameFailed') || 'Failed to update nickname. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const saveGender = async () => {
    if (!genderVal) { setModalError(t('errors.genderRequired') || 'Please select a gender'); return; }
    setSaving(true);
    try {
      await authService.updateProfile({ gender: genderVal });
      await refreshUser();
      closeModal();
    } catch {
      setModalError(t('errors.genderFailed') || 'Failed to update gender. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const savePassword = async () => {
    if (!currentPwVal) { setModalError(t('errors.currentPasswordRequired') || 'Enter your current password'); return; }
    if (newPwVal.length < 8) { setModalError(t('errors.passwordMinLength') || 'New password must be at least 8 characters'); return; }
    if (newPwVal !== confirmPwVal) { setModalError(t('errors.passwordMismatch') || 'Passwords do not match'); return; }
    setSaving(true);
    try {
      await authService.changePassword(currentPwVal, newPwVal);
      closeModal();
    } catch (err: unknown) {
      const msg = (err as { code?: string })?.code;
      if (msg === 'auth/wrong-password' || msg === 'auth/invalid-credential') {
        setModalError(t('errors.currentPasswordIncorrect') || 'Current password is incorrect');
      } else {
        setModalError(t('errors.passwordChangeFailed') || 'Failed to change password. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const submitFeedback = async () => {
    const content = feedbackContent.trim();
    if (content.length < 10) {
      setFeedbackError(t('feedback.minLength') || 'Please enter at least 10 characters.');
      setFeedbackSuccess('');
      return;
    }

    setFeedbackSubmitting(true);
    setFeedbackError('');
    setFeedbackSuccess('');

    try {
      await api.post('/billing/support/feedback', {
        feedback_type: feedbackType,
        content,
      });
      setFeedbackContent('');
      setFeedbackSuccess(t('feedback.success') || 'Thanks. Your feedback has been sent.');
    } catch {
      setFeedbackError(t('feedback.error') || 'Failed to send feedback. Please try again.');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const nickname = user?.display_name || user?.email?.split('@')[0] || 'User';
  const tier = user?.subscription_tier || 'free';
  const isPremium = tier === 'premium';

  return (
    <div className="min-h-screen py-8 md:py-12">
      <Container>
        <div className="mx-auto max-w-[640px]">
          <h1 className="mb-8 text-center text-3xl font-heading font-bold text-white md:text-4xl">
            {t('title')}
          </h1>

          <div className="space-y-5">
            <Card className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5 md:p-6">
              <div className="flex flex-col gap-5 md:flex-row md:items-center">
                <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full bg-rose-400/90 text-white shadow-lg shadow-rose-500/20">
                  <User size={48} strokeWidth={1.6} />
                </div>
                <div className="grid flex-1 grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <button
                      type="button"
                      onClick={() => openModal('nickname')}
                      className="group w-full text-left"
                    >
                      <p className="mb-1 flex items-center gap-1 text-sm text-zinc-400 group-hover:text-zinc-200">
                        {t('fields.displayName')}
                        <PencilLine size={12} className="text-zinc-500 group-hover:text-rose-400" />
                      </p>
                      <p className="font-semibold text-white group-hover:text-rose-300">{nickname}</p>
                    </button>
                  </div>
                  <div>
                    <button
                      type="button"
                      onClick={() => openModal('gender')}
                      className="group w-full text-left"
                    >
                      <p className="mb-1 flex items-center gap-1 text-sm text-zinc-400 group-hover:text-zinc-200">
                        {t('fields.gender')}
                        <PencilLine size={12} className="text-zinc-500 group-hover:text-rose-400" />
                      </p>
                      <p className="font-semibold text-white group-hover:text-rose-300">
                        {user?.gender ? t(`genders.${user.gender}`, user.gender) : '-'}
                      </p>
                    </button>
                  </div>
                  <div>
                    <p className="mb-1 text-sm text-zinc-400">{t('fields.email')}</p>
                    <p className="truncate font-semibold text-white">{maskEmail(user?.email)}</p>
                  </div>
                  <div>
                    <button
                      type="button"
                      onClick={() => openModal('password')}
                      className="group w-full text-left"
                    >
                      <p className="mb-1 flex items-center gap-1 text-sm text-zinc-400 group-hover:text-zinc-200">
                        {t('fields.password') || 'Password'}
                        <PencilLine size={12} className="text-zinc-500 group-hover:text-rose-400" />
                      </p>
                      <p className="font-semibold text-white group-hover:text-rose-300">••••••••</p>
                    </button>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="rounded-2xl border border-zinc-800 bg-gradient-to-r from-rose-900/35 via-rose-900/10 to-zinc-900/80 p-4 md:p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-lg font-semibold text-white">
                  {t('subscription.plan')} <span className="ml-2 text-rose-400">{formatTier(tier)}</span>
                </p>
                {!isPremium && (
                  <Button
                    onClick={() => navigate('/subscriptions')}
                    className="rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-400"
                  >
                    {t('subscription.upgrade')}
                  </Button>
                )}
              </div>
            </Card>

            <Card className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70 p-0">
              <section className="border-b border-zinc-800 p-5 md:p-6">
                <h2 className="mb-4 text-2xl font-semibold text-white">{t('language') || 'Language'}</h2>
                <LanguageSwitcher />
              </section>

              <section className="border-b border-zinc-800 p-5 md:p-6">
                <h2 className="mb-4 text-2xl font-semibold text-white">{t('notifications.title') || 'Notifications'}</h2>
                <label className="flex items-start gap-3 text-zinc-300">
                  <input type="checkbox" defaultChecked className="mt-1 h-4 w-4 accent-blue-500" />
                  <span className="text-sm leading-6">
                    {t('notifications.description') || 'Receive automatic notifications from us. Uncheck to disable.'}
                  </span>
                </label>
              </section>

              <section className="border-b border-zinc-800 p-5 md:p-6">
                <h2 className="mb-4 text-2xl font-semibold text-white">{t('feedback.title') || 'Feedback'}</h2>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setFeedbackType('complaint')}
                      className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                        feedbackType === 'complaint'
                          ? 'border-rose-500 bg-rose-500/20 text-rose-300'
                          : 'border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-800'
                      }`}
                    >
                      {t('feedback.complaint') || 'Complaint'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setFeedbackType('suggestion')}
                      className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                        feedbackType === 'suggestion'
                          ? 'border-rose-500 bg-rose-500/20 text-rose-300'
                          : 'border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-800'
                      }`}
                    >
                      {t('feedback.suggestion') || 'Suggestion'}
                    </button>
                  </div>

                  <textarea
                    value={feedbackContent}
                    onChange={(e) => setFeedbackContent(e.target.value)}
                    rows={5}
                    maxLength={2000}
                    placeholder={t('feedback.placeholder') || 'Tell us what happened or what we can improve...'}
                    className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />

                  {feedbackError && <p className="text-sm text-rose-400">{feedbackError}</p>}
                  {feedbackSuccess && <p className="text-sm text-emerald-400">{feedbackSuccess}</p>}

                  <div>
                    <Button
                      onClick={submitFeedback}
                      disabled={feedbackSubmitting}
                      className="rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-400 disabled:opacity-50"
                    >
                      {feedbackSubmitting ? (t('feedback.sending') || 'Sending...') : (t('feedback.send') || 'Send Feedback')}
                    </Button>
                  </div>
                </div>
              </section>

              <section className="flex flex-wrap items-center justify-between gap-3 p-5 md:p-6">
                <p className="text-sm text-zinc-300">
                  <span className="mr-2 font-semibold text-zinc-100">{t('dangerZone.title')}</span>
                  {t('dangerZone.warning')}
                </p>
                <button type="button" className="text-sm text-zinc-400 underline transition hover:text-zinc-200">
                  {t('dangerZone.deleteAccount')}
                </button>
              </section>
            </Card>

            <div className="flex justify-end">
              <Button variant="ghost" onClick={handleSignOut} className="text-zinc-400 hover:text-white">
                {t('account.logout') || 'Sign out'}
              </Button>
            </div>
          </div>
        </div>
      </Container>

      {modal === 'nickname' && (
        <EditModal title={t('editModal.nickname') || 'Edit Nickname'} onClose={closeModal} onSave={saveNickname} saving={saving} error={modalError}>
          <input
            type="text"
            value={nicknameVal}
            onChange={(e) => setNicknameVal(e.target.value)}
            maxLength={32}
            placeholder={t('editModal.nicknamePlaceholder') || 'Your nickname'}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
          />
        </EditModal>
      )}

      {modal === 'gender' && (
        <EditModal title={t('editModal.gender') || 'Edit Gender'} onClose={closeModal} onSave={saveGender} saving={saving} error={modalError}>
          <div className="grid grid-cols-2 gap-2">
            {[
              { value: 'male', label: t('genders.male') },
              { value: 'female', label: t('genders.female') },
              { value: 'non-binary', label: t('genders.nonBinary') || 'Non-binary' },
              { value: 'prefer_not_to_say', label: t('genders.preferNotToSay') },
            ].map(({ value, label }) => (
              <button
                key={value}
                type="button"
                onClick={() => setGenderVal(value)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition ${
                  genderVal === value
                    ? 'border-rose-500 bg-rose-500/20 text-rose-300'
                    : 'border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:bg-zinc-800'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </EditModal>
      )}

      {modal === 'password' && (
        <EditModal title={t('account.changePassword') || 'Change Password'} onClose={closeModal} onSave={savePassword} saving={saving} error={modalError}>
          <input
            type="password"
            value={currentPwVal}
            onChange={(e) => setCurrentPwVal(e.target.value)}
            placeholder={t('editModal.currentPassword') || 'Current password'}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
          />
          <input
            type="password"
            value={newPwVal}
            onChange={(e) => setNewPwVal(e.target.value)}
            placeholder={t('editModal.newPassword') || 'New password (min 8 chars)'}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
          />
          <input
            type="password"
            value={confirmPwVal}
            onChange={(e) => setConfirmPwVal(e.target.value)}
            placeholder={t('editModal.confirmPassword') || 'Confirm new password'}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-rose-500"
          />
        </EditModal>
      )}
    </div>
  );
}
