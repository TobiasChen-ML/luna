import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AgeGatePage } from '@/pages/AgeGatePage';

const mockVerify = vi.fn();
const mockBlock = vi.fn();

vi.mock('@/contexts/AgeGateContext', () => ({
  useAgeGate: () => ({
    verify: mockVerify,
    block: mockBlock,
    isVerified: false,
    isBlocked: false,
  }),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'ageGate.title': 'Age Verification Required',
        'ageGate.subtitle': 'You must be 18 or older to access this content.',
        'ageGate.yes': 'I am 18 or older',
        'ageGate.no': 'I am under 18',
        'ageGate.notice': 'By continuing, you agree to our',
        'register.termsOfService': 'Terms of Service',
        'register.privacyPolicy': 'Privacy Policy',
        'register.and': 'and',
      };
      return translations[key] || key;
    },
    i18n: {
      changeLanguage: vi.fn(),
    },
  }),
}));

function renderAgeGatePage() {
  return render(
    <MemoryRouter>
      <AgeGatePage />
    </MemoryRouter>
  );
}

describe('AgeGatePage', () => {
  it('renders without crashing', () => {
    renderAgeGatePage();
    expect(document.body).toBeTruthy();
  });

  it('displays age verification heading', () => {
    renderAgeGatePage();
    expect(screen.getByText('Age Verification Required')).toBeInTheDocument();
  });

  it('shows the 18+ enter button', () => {
    renderAgeGatePage();
    expect(screen.getByText(/I am 18 or older$/i)).toBeInTheDocument();
  });

  it('shows the under-18 leave button', () => {
    renderAgeGatePage();
    expect(screen.getByText(/I am under 18$/i)).toBeInTheDocument();
  });

  it('calls verify when the enter button is clicked', async () => {
    const user = userEvent.setup();
    renderAgeGatePage();
    const enterButton = screen.getByText(/I am 18 or older$/i);
    await user.click(enterButton);
    expect(mockVerify).toHaveBeenCalledOnce();
  });

  it('calls block when the leave button is clicked', async () => {
    const user = userEvent.setup();
    renderAgeGatePage();
    const leaveButton = screen.getByText(/I am under 18$/i);
    await user.click(leaveButton);
    expect(mockBlock).toHaveBeenCalledOnce();
  });

  it('renders links to terms and privacy policy', () => {
    renderAgeGatePage();
    expect(screen.getByText('Terms of Service')).toBeInTheDocument();
    expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
  });
});
