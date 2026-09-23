import React, { useState, Component, ErrorInfo, ReactNode } from 'react';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';

import { ProductCatalogPage } from './pages/ProductCatalogPage';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { CartPage } from './pages/CartPage';
import { CheckoutPage } from './pages/CheckoutPage';
import { OrdersHistoryPage } from './pages/OrdersHistoryPage';
import { OrderTrackingPage } from './pages/OrderTrackingPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { AuthPage } from './pages/AuthPage';
import { Product } from './types';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('App caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Something interrupted your view</h2>
          <p className="text-xs text-slate-500 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred while rendering the page.'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false });
              window.location.reload();
            }}
            className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-brand-600 transition flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload Application</span>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function MainApp() {
  const [currentView, setCurrentView] = useState<string>('products');
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const { isAuthenticated } = useAuth();

  const handleNavigate = (view: string, params?: any) => {
    if (view === 'product-detail' && params?.productId) {
      setSelectedProductId(String(params.productId));
    }
    if (view === 'order-tracking' && params?.orderId) {
      setSelectedOrderId(String(params.orderId));
    }
    setCurrentView(view);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectProduct = (product: Product) => {
    setSelectedProductId(String(product.id));
    setCurrentView('product-detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectOrder = (orderId: string) => {
    setSelectedOrderId(String(orderId));
    setCurrentView('order-tracking');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 selection:bg-brand-500 selection:text-white">
      <Navbar currentView={currentView} onNavigate={handleNavigate} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <ErrorBoundary>
          {currentView === 'products' && (
            <ProductCatalogPage onSelectProduct={handleSelectProduct} />
          )}

          {currentView === 'product-detail' && selectedProductId && (
            <ProductDetailPage
              productId={selectedProductId}
              onBack={() => setCurrentView('products')}
              onSelectProduct={handleSelectProduct}
            />
          )}

          {currentView === 'cart' && (
            <CartPage onNavigate={handleNavigate} />
          )}

          {currentView === 'checkout' && (
            <CheckoutPage
              onOrderPlaced={(orderId) => {
                setSelectedOrderId(String(orderId));
                setCurrentView('order-tracking');
              }}
              onNavigate={handleNavigate}
            />
          )}

          {currentView === 'orders' && (
            <OrdersHistoryPage
              onSelectOrder={handleSelectOrder}
              onNavigate={handleNavigate}
            />
          )}

          {currentView === 'order-tracking' && selectedOrderId && (
            <OrderTrackingPage
              orderId={selectedOrderId}
              onBack={() => setCurrentView(isAuthenticated ? 'orders' : 'products')}
            />
          )}

          {currentView === 'admin' && <AdminDashboardPage />}

          {currentView === 'login' && (
            <AuthPage onSuccess={() => setCurrentView('products')} />
          )}
        </ErrorBoundary>
      </main>

      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          <MainApp />
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
