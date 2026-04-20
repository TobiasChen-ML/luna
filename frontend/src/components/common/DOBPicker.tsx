import { cn } from '@/utils/cn';

export interface DateOfBirth {
  month: number;
  day: number;
  year: number;
}

interface DOBPickerProps {
  value: DateOfBirth | null;
  onChange: (dob: DateOfBirth | null) => void;
  error?: string;
  disabled?: boolean;
  label?: string;
}

const months = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

// Generate years from (currentYear - 100) to (currentYear - 18)
// Only show years where user could be 18+
const currentYear = new Date().getFullYear();
const years = Array.from({ length: 83 }, (_, i) => currentYear - 18 - i);

// Generate days 1-31
const days = Array.from({ length: 31 }, (_, i) => i + 1);

function getDaysInMonth(month: number, year: number): number {
  return new Date(year, month, 0).getDate();
}

export function DOBPicker({ value, onChange, error, disabled, label }: DOBPickerProps) {
  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const month = parseInt(e.target.value, 10);
    if (isNaN(month)) {
      onChange(null);
      return;
    }

    const newValue = {
      month,
      day: value?.day || 0,
      year: value?.year || 0
    };

    // Adjust day if it exceeds days in new month
    if (newValue.year && newValue.day) {
      const maxDays = getDaysInMonth(month, newValue.year);
      if (newValue.day > maxDays) {
        newValue.day = maxDays;
      }
    }

    onChange(newValue);
  };

  const handleDayChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const day = parseInt(e.target.value, 10);
    if (isNaN(day)) {
      onChange(value ? { ...value, day: 0 } : null);
      return;
    }

    onChange({
      month: value?.month || 0,
      day,
      year: value?.year || 0
    });
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const year = parseInt(e.target.value, 10);
    if (isNaN(year)) {
      onChange(value ? { ...value, year: 0 } : null);
      return;
    }

    const newValue = {
      month: value?.month || 0,
      day: value?.day || 0,
      year
    };

    // Adjust day if it exceeds days in selected month/year
    if (newValue.month && newValue.day) {
      const maxDays = getDaysInMonth(newValue.month, year);
      if (newValue.day > maxDays) {
        newValue.day = maxDays;
      }
    }

    onChange(newValue);
  };

  // Get available days based on selected month/year
  const availableDays = value?.month && value?.year
    ? getDaysInMonth(value.month, value.year)
    : 31;

  const selectClassName = cn(
    'flex-1 min-w-0 px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg',
    'text-white text-sm appearance-none cursor-pointer',
    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    error && 'border-red-500 focus:ring-red-500'
  );

  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          {label}
        </label>
      )}

      <div className="flex gap-2">
        {/* Month */}
        <select
          value={value?.month || ''}
          onChange={handleMonthChange}
          disabled={disabled}
          className={selectClassName}
          aria-label="Month"
        >
          <option value="">Month</option>
          {months.map((month, index) => (
            <option key={month} value={index + 1}>
              {month}
            </option>
          ))}
        </select>

        {/* Day */}
        <select
          value={value?.day || ''}
          onChange={handleDayChange}
          disabled={disabled}
          className={selectClassName}
          aria-label="Day"
        >
          <option value="">Day</option>
          {days.slice(0, availableDays).map((day) => (
            <option key={day} value={day}>
              {day}
            </option>
          ))}
        </select>

        {/* Year */}
        <select
          value={value?.year || ''}
          onChange={handleYearChange}
          disabled={disabled}
          className={selectClassName}
          aria-label="Year"
        >
          <option value="">Year</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
}
