import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ShieldCheck, AlertTriangle, X } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { DOBPicker } from '@/components/common/DOBPicker';
import type { DateOfBirth } from '@/components/common/DOBPicker';
import { useAuth } from '@/contexts/AuthContext';

// Helper to check if DOB makes user 18+
const isAdultFromDOB = (dob: DateOfBirth | null): boolean => {
  if (!dob || !dob.year || !dob.month || !dob.day) return false;

  const today = new Date();
  const birthDate = new Date(dob.year, dob.month - 1, dob.day);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }

  return age >= 18;
};

const dobSchema = z.object({
  dateOfBirth: z.object({
    month: z.number().min(1, 'Month is required').max(12),
    day: z.number().min(1, 'Day is required').max(31),
    year: z.number().min(1900, 'Year is required').max(new Date().getFullYear() - 18),
  }).refine((dob) => isAdultFromDOB(dob), {
    message: 'You must be at least 18 years old to use this service',
  }),
  ageConsent: z.boolean().refine((val) => val === true, {
    message: 'You must confirm that you are 18 years or older',
  }),
});

type DOBFormData = z.infer<typeof dobSchema>;

interface DOBCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DOBCollectionModal({ isOpen, onClose }: DOBCollectionModalProps) {
  const { completeRegistration, logout } = useAuth();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<DOBFormData>({
    resolver: zodResolver(dobSchema),
    defaultValues: {
      dateOfBirth: { month: 0, day: 0, year: 0 },
      ageConsent: false,
    },
  });

  const dateOfBirth = watch('dateOfBirth');
  const ageConsent = watch('ageConsent');
  const isAdult = isAdultFromDOB(dateOfBirth);

  const onSubmit = async (data: DOBFormData) => {
    setError('');
    setLoading(true);

    try {
      await completeRegistration(data.dateOfBirth, data.ageConsent);
      onClose();
    } catch (err: any) {
      console.error('Complete registration error:', err);
      if (err.response?.status === 403) {
        setError('You must be at least 18 years old to use this service.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to complete registration. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    // If user cancels, log them out since they can't use the service without age verification
    await logout();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="relative max-w-md w-full bg-zinc-900 rounded-2xl p-6 border border-zinc-800 shadow-xl">
        {/* Close button */}
        <button
          onClick={handleCancel}
          className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="flex justify-center mb-4">
            <ShieldCheck className="w-12 h-12 text-primary-500" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            Age Verification Required
          </h2>
          <p className="text-sm text-zinc-400">
            To complete your account setup, please provide your date of birth.
          </p>
        </div>

        {/* Warning */}
        <div className="flex items-start gap-3 text-amber-500/90 bg-amber-500/10 p-3 rounded-lg text-xs leading-relaxed mb-6">
          <AlertTriangle className="shrink-0 w-4 h-4 mt-0.5" />
          <p>
            <span className="font-medium">18+ Only:</span> This service contains age-restricted content. You must be 18 or older to continue.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <Controller
            name="dateOfBirth"
            control={control}
            render={({ field }) => (
              <DOBPicker
                label="Date of Birth"
                value={field.value ?? null}
                onChange={field.onChange}
                error={errors.dateOfBirth?.message || errors.dateOfBirth?.root?.message}
                disabled={loading}
              />
            )}
          />

          {!isAdult && dateOfBirth && (dateOfBirth.month > 0 || dateOfBirth.day > 0 || dateOfBirth.year > 0) && (
            <p className="text-xs text-red-400 text-center">
              You must be at least 18 years old to use this service
            </p>
          )}

          {/* Age Consent Checkbox */}
          <Controller
            name="ageConsent"
            control={control}
            render={({ field }) => (
              <div className="space-y-1">
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={field.value}
                    onChange={field.onChange}
                    disabled={loading}
                    className="mt-0.5 w-5 h-5 rounded border-2 border-zinc-700 bg-zinc-900 text-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-zinc-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
                  />
                  <span className="text-sm text-zinc-300 group-hover:text-white transition-colors">
                    I confirm that I am <span className="font-semibold text-white">18 years or older</span> and agree to the Terms of Service
                  </span>
                </label>
                {errors.ageConsent && (
                  <p className="text-xs text-red-400 ml-8">
                    {errors.ageConsent.message}
                  </p>
                )}
              </div>
            )}
          />

          <div className="flex gap-3">
            <Button
              type="button"
              variant="secondary"
              className="flex-1"
              onClick={handleCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              loading={loading}
              disabled={loading || !isAdult || !ageConsent}
            >
              Continue
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
