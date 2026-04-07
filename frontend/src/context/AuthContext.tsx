// eslint-disable-next-line react-refresh/only-export-components
import { createContext, useState, useCallback, type ReactNode } from 'react';

// Basic JWT decoder without an external library
const decodeJWT = (token: string) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(function (c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
};

export interface User {
  id?: number | string;
  username: string;
  sub?: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Initial state calculation outside effect to prevent cascading renders
const getInitialState = () => {
  const storedToken = localStorage.getItem('token');
  if (storedToken) {
    const decodedUser = decodeJWT(storedToken);
    return {
      token: storedToken,
      user: decodedUser ? { username: decodedUser.sub || decodedUser.username, ...decodedUser } : null,
    };
  }
  return { token: null, user: null };
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const initialState = getInitialState();
  const [token, setToken] = useState<string | null>(initialState.token);
  const [user, setUser] = useState<User | null>(initialState.user);
  const isLoading = false; // Initial loading is complete once getInitialState returns

  const setAuthToken = useCallback((newToken: string | null) => {
    if (newToken) {
      localStorage.setItem('token', newToken);
      setToken(newToken);
      const decodedUser = decodeJWT(newToken);
      setUser(decodedUser ? { username: decodedUser.sub || decodedUser.username, ...decodedUser } : null);
    } else {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    }
  }, []);

  const login = async (username: string, password: string) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${baseUrl}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: username,
        password: password,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Détails de l'erreur 422 :", errorData);
      throw new Error('Login failed');
    }

    const data = await response.json();
    if (data.access_token) {
      setAuthToken(data.access_token);
    } else {
      throw new Error('No access token received');
    }
  };

  const register = async (username: string, password: string) => {
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${baseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        password: password,
      }),
    });

    if (!response.ok) {
      let errorMessage = 'Registration failed';
      try {
        const errorData = await response.json();
        if (errorData.detail) errorMessage = errorData.detail;
      } catch {
        // ignore JSON parse error
      }
      throw new Error(errorMessage);
    }

    // Automatically login after successful registration
    await login(username, password);
  };

  const logout = () => {
    setAuthToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
