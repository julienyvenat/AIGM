import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { AuthContext } from '../context/AuthContext';
import { expect, test } from 'vitest';

const renderWithAuth = (token: string | null, isLoading: boolean, initialRoute: string = '/protected') => {
  return render(
    <AuthContext.Provider value={{ token, user: null, login: async () => {}, register: async () => {}, logout: () => {}, isLoading }}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/login" element={<div>Page de Login</div>} />
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Page Protégée</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
};

test('Affiche Loading quand isLoading est true', () => {
  renderWithAuth(null, true);
  expect(screen.getByText('Loading...')).toBeInTheDocument();
});

test('Redirige vers /login si non authentifié', () => {
  renderWithAuth(null, false);
  expect(screen.getByText('Page de Login')).toBeInTheDocument();
  expect(screen.queryByText('Page Protégée')).not.toBeInTheDocument();
});

test('Affiche le contenu si authentifié', () => {
  renderWithAuth('fake-token', false);
  expect(screen.getByText('Page Protégée')).toBeInTheDocument();
  expect(screen.queryByText('Page de Login')).not.toBeInTheDocument();
});
