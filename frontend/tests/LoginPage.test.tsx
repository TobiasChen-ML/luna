import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';

// Mock AuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
    loginWithGoogle: vi.fn(),
    isAuthenticated: false,
    loading: false,
    user: null,
  }),
}));

// Mock react-router-dom navigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  it('renders without crashing', () => {
    renderLoginPage();
    expect(document.body).toBeTruthy();
  });

  it('displays Welcome Back heading', () => {
    renderLoginPage();
    expect(screen.getByText('Welcome Back')).toBeInTheDocument();
  });

  it('renders email input field', () => {
    renderLoginPage();
    expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
  });

  it('renders password input field', () => {
    renderLoginPage();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  });

  it('renders sign in button', () => {
    renderLoginPage();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders Google sign in button', () => {
    renderLoginPage();
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  });

  it('shows link to register page', () => {
    renderLoginPage();
    expect(screen.getByText('Create one')).toBeInTheDocument();
  });

  it('shows 18+ age notice', () => {
    renderLoginPage();
    expect(screen.getByText(/18\+ Only/i)).toBeInTheDocument();
  });
});
