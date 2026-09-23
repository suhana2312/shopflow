import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, Role } from '../types';
import { authApi } from '../api/client';
import { useToast } from './ToastContext';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  quickLogin: (role: 'admin' | 'customer') => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('shopflow_access_token'));
  const [loading, setLoading] = useState<boolean>(true);
  const { success, error } = useToast();

  const refreshProfile = useCallback(async () => {
    try {
      const currentUser = await authApi.me();
      setUser(currentUser);
    } catch (err) {
      console.warn('Failed to fetch user profile:', err);
      setUser(null);
      setToken(null);
      authApi.logout();
    }
  }, []);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('shopflow_access_token');
      if (storedToken) {
        setToken(storedToken);
        await refreshProfile();
      }
      setLoading(false);
    };
    initAuth();
  }, [refreshProfile]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const tokens = await authApi.login({ email, password });
      localStorage.setItem('shopflow_access_token', tokens.access_token);
      localStorage.setItem('shopflow_refresh_token', tokens.refresh_token);
      setToken(tokens.access_token);
      const profile = await authApi.me();
      setUser(profile);
      success('Welcome back!', `Signed in as ${profile.full_name}`);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Invalid email or password';
      error('Sign In Failed', msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName: string) => {
    setLoading(true);
    try {
      await authApi.register({ email, password, full_name: fullName });
      // Automatically log in after registration
      await login(email, password);
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Failed to create account';
      error('Registration Failed', msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setToken(null);
    success('Signed Out', 'You have been signed out successfully.');
  };

  const quickLogin = async (role: 'admin' | 'customer') => {
    const credentials =
      role === 'admin'
        ? { email: 'admin@shopflow.io', password: 'AdminPassword123!' }
        : { email: 'customer@shopflow.io', password: 'CustomerPassword123!' };
    await login(credentials.email, credentials.password);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
        loading,
        login,
        register,
        logout,
        quickLogin,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
