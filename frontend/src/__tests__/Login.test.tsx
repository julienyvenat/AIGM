import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Login } from '../pages/Login';
import { AuthContext, type User } from '../context/AuthContext';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { expect, test, vi } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: null
    }),
  };
});

const renderLogin = (loginMock: (username: string, password: string) => Promise<void>) => {
  return render(
    <AuthContext.Provider value={{
      token: null,
      user: null as User | null,
      login: loginMock,
      register: vi.fn(),
      logout: vi.fn(),
      isLoading: false
    }}>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

test('Affiche un message d\'erreur en cas d\'échec de la connexion', async () => {
  const loginMock = vi.fn().mockRejectedValue(new Error('Invalid credentials'));

  renderLogin(loginMock);

  const usernameInput = screen.getByLabelText(/Nom d'utilisateur/i);
  const passwordInput = screen.getByLabelText(/Mot de passe/i);
  const submitButton = screen.getByRole('button', { name: /Se connecter/i });

  await userEvent.type(usernameInput, 'testuser');
  await userEvent.type(passwordInput, 'wrongpassword');
  await userEvent.click(submitButton);

  await waitFor(() => {
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  expect(loginMock).toHaveBeenCalledWith('testuser', 'wrongpassword');
});

test('Redirige vers /dashboard par défaut après une connexion réussie', async () => {
  const loginMock = vi.fn().mockResolvedValue(undefined);

  renderLogin(loginMock);

  const usernameInput = screen.getByLabelText(/Nom d'utilisateur/i);
  const passwordInput = screen.getByLabelText(/Mot de passe/i);
  const submitButton = screen.getByRole('button', { name: /Se connecter/i });

  await userEvent.type(usernameInput, 'validuser');
  await userEvent.type(passwordInput, 'validpassword');
  await userEvent.click(submitButton);

  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });
});
