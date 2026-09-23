import React from 'react';
import { ShoppingBag, ShieldCheck, User as UserIcon, LogOut, Package, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string, params?: any) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate }) => {
  const { user, isAuthenticated, isAdmin, logout, quickLogin } = useAuth();
  const { itemsCount } = useCart();

  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => onNavigate('products')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <Zap className="w-5 h-5 fill-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight text-slate-900">ShopFlow</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-100 text-brand-800">
                Real-Time
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium -mt-1">Order & Inventory Engine</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 font-medium text-sm text-slate-600">
          <button
            onClick={() => onNavigate('products')}
            className={`px-3 py-2 rounded-lg transition ${
              currentView === 'products' ? 'text-brand-700 bg-brand-50 font-semibold' : 'hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Catalog
          </button>
          {isAuthenticated && (
            <button
              onClick={() => onNavigate('orders')}
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                currentView === 'orders' ? 'text-brand-700 bg-brand-50 font-semibold' : 'hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Package className="w-4 h-4" />
              My Orders
            </button>
          )}
          {isAdmin && (
            <button
              onClick={() => onNavigate('admin')}
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                currentView === 'admin'
                  ? 'text-purple-700 bg-purple-50 font-semibold'
                  : 'hover:text-purple-700 hover:bg-purple-50 text-purple-600'
              }`}
            >
              <ShieldCheck className="w-4 h-4" />
              Admin Portal
            </button>
          )}
        </nav>

        {/* Action Controls & Auth */}
        <div className="flex items-center gap-3">
          {/* Cart Button */}
          <button
            onClick={() => onNavigate('cart')}
            className="relative p-2 rounded-xl text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition"
            aria-label="Shopping Cart"
          >
            <ShoppingBag className="w-5 h-5" />
            {itemsCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-brand-600 text-white text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center animate-pulse shadow-sm">
                {itemsCount}
              </span>
            )}
          </button>

          {/* User state / Quick demo switcher */}
          {isAuthenticated ? (
            <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-semibold text-slate-800 leading-tight">{user?.full_name}</p>
                <span className={`text-[10px] font-semibold uppercase tracking-wider ${isAdmin ? 'text-purple-600' : 'text-slate-500'}`}>
                  {user?.role}
                </span>
              </div>
              <button
                onClick={logout}
                title="Sign out"
                className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => quickLogin('customer')}
                className="hidden sm:inline-flex text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 transition"
              >
                Demo Customer
              </button>
              <button
                onClick={() => quickLogin('admin')}
                className="hidden sm:inline-flex text-xs font-medium px-2.5 py-1.5 rounded-lg border border-purple-200 bg-purple-50 hover:bg-purple-100 text-purple-700 transition"
              >
                Demo Admin
              </button>
              <button
                onClick={() => onNavigate('login')}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white transition flex items-center gap-1.5 shadow-sm"
              >
                <UserIcon className="w-3.5 h-3.5" />
                Sign In
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
