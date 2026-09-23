import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, User as UserIcon, Lock, Mail, ArrowRight, Zap, RefreshCw } from 'lucide-react';

interface AuthPageProps {
  onSuccess: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { login, register, quickLogin } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      onSuccess();
    } catch (err) {
      // Error toast already triggered by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemo = async (role: 'admin' | 'customer') => {
    setSubmitting(true);
    try {
      await quickLogin(role);
      onSuccess();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 px-4 sm:px-0">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 text-brand-600 flex items-center justify-center mx-auto shadow-inner">
            <Zap className="w-6 h-6 fill-brand-600 text-brand-600" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            {mode === 'login' ? 'Sign In to ShopFlow' : 'Create an Account'}
          </h1>
          <p className="text-xs text-slate-500">
            {mode === 'login'
              ? 'Access real-time order tracking & synchronized shopping carts'
              : 'Join the next-generation distributed e-commerce experience'}
          </p>
        </div>

        {/* Quick Demo Login Buttons */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2.5">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block text-center">
            One-Click Demo Credentials
          </span>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              disabled={submitting}
              onClick={() => handleDemo('customer')}
              className="py-2 px-3 rounded-xl bg-white border border-slate-200 hover:border-brand-500 hover:text-brand-700 text-xs font-semibold text-slate-700 transition shadow-xs flex items-center justify-center gap-1.5"
            >
              <UserIcon className="w-3.5 h-3.5 text-brand-600" />
              <span>Customer Demo</span>
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => handleDemo('admin')}
              className="py-2 px-3 rounded-xl bg-white border border-slate-200 hover:border-purple-500 hover:text-purple-700 text-xs font-semibold text-slate-700 transition shadow-xs flex items-center justify-center gap-1.5"
            >
              <Shield className="w-3.5 h-3.5 text-purple-600" />
              <span>Admin Demo</span>
            </button>
          </div>
        </div>

        {/* Tabs for Login / Register */}
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 pb-3 text-xs font-bold text-center border-b-2 transition ${
              mode === 'login'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode('register')}
            className={`flex-1 pb-3 text-xs font-bold text-center border-b-2 transition ${
              mode === 'register'
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            Register
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ada Lovelace"
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="customer@shopflow.io"
                className="w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-3.5 py-2.5 text-sm rounded-xl border border-slate-200 focus:ring-2 focus:ring-brand-500 focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 rounded-xl bg-slate-900 hover:bg-brand-600 text-white font-bold text-sm transition flex items-center justify-center gap-2 shadow-md shadow-slate-900/10 active:scale-98"
          >
            {submitting ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
