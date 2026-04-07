import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider } from '../context/AuthContext';
import { useAuth } from '../hooks/useAuth';
import { expect, test, vi, beforeEach } from 'vitest';

const TestComponent = () => {
  const { token, user, login, logout, register, isLoading } = useAuth();

  if (isLoading) return <div>Loading Auth...</div>;

  return (
    <div>
      <div data-testid="token">{token || 'No Token'}</div>
      <div data-testid="user">{user ? user.username : 'No User'}</div>
      <button onClick={() => login('test', 'pass')}>Login</button>
      <button onClick={() => register('new', 'pass')}>Register</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

beforeEach(() => {
  localStorage.clear();
  window.fetch = vi.fn();
});

test('Initialise sans token par défaut', async () => {
  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

  await waitFor(() => {
    expect(screen.queryByText('Loading Auth...')).not.toBeInTheDocument();
  });

  expect(screen.getByTestId('token')).toHaveTextContent('No Token');
});

test('Peut se déconnecter (logout)', async () => {
  localStorage.setItem('token', 'fake.jwt.token');

  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

  await waitFor(() => {
    expect(screen.queryByText('Loading Auth...')).not.toBeInTheDocument();
  });

  const btnLogout = screen.getByText('Logout');
  await userEvent.click(btnLogout);

  expect(screen.getByTestId('token')).toHaveTextContent('No Token');
  expect(localStorage.getItem('token')).toBeNull();
});

test('Mock API Login update token', async () => {
  // Mock le fetch pour login
  (window.fetch as import("vitest").Mock).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ access_token: 'fake.jwt.token', token_type: 'bearer' }),
  });

  render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  );

  await waitFor(() => {
    expect(screen.queryByText('Loading Auth...')).not.toBeInTheDocument();
  });

  const btnLogin = screen.getByText('Login');
  await userEvent.click(btnLogin);

  await waitFor(() => {
    expect(screen.getByTestId('token')).toHaveTextContent('fake.jwt.token');
  });
  expect(localStorage.getItem('token')).toBe('fake.jwt.token');
});
