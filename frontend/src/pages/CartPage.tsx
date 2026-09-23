import React from 'react';
import { useCart } from '../context/CartContext';
import { Trash2, Plus, Minus, ArrowRight, ShoppingBag, ShieldCheck } from 'lucide-react';

interface CartPageProps {
  onNavigate: (view: string) => void;
}

export const CartPage: React.FC<CartPageProps> = ({ onNavigate }) => {
  const { cart, updateQuantity, removeItem, clearCart, loading } = useCart();

  const items = cart?.items || [];
  const subtotal = cart?.subtotal || 0;
  const shipping = subtotal > 150 || subtotal === 0 ? 0 : 15.0;
  const tax = Number((subtotal * 0.1).toFixed(2));
  const total = Number((subtotal + shipping + tax).toFixed(2));

  if (items.length === 0) {
    return (
      <div className="py-24 text-center max-w-md mx-auto space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Your shopping cart is empty</h2>
        <p className="text-sm text-slate-500">
          Explore our real-time inventory catalog to add items with live concurrency control.
        </p>
        <button
          onClick={() => onNavigate('products')}
          className="mt-4 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm transition shadow-md shadow-brand-500/20"
        >
          Browse Products
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Shopping Cart</h1>
          <p className="text-xs text-slate-500 mt-1">
            Review reserved selections before initiating atomic checkout
          </p>
        </div>
        <button
          onClick={clearCart}
          className="text-xs font-semibold text-rose-600 hover:text-rose-700 p-2 rounded-lg hover:bg-rose-50 transition"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Cart Items List */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => {
            const product = item.product;
            const title = product?.name || product?.title || `Product #${item.product_id}`;
            const imageSrc =
              product?.image_url ||
              (product?.images && product.images.length > 0 ? product.images[0] : null) ||
              'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&auto=format&fit=crop&q=80';

            return (
              <div
                key={item.id}
                className="flex flex-col sm:flex-row items-center gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-xs"
              >
                {/* Thumbnail */}
                <div className="w-20 h-20 rounded-xl bg-slate-100 overflow-hidden shrink-0">
                  <img src={imageSrc} alt={title} className="w-full h-full object-cover" />
                </div>

                {/* Info */}
                <div className="flex-1 text-center sm:text-left space-y-1">
                  <h3 className="text-sm font-bold text-slate-900">{title}</h3>
                  <div className="flex items-center justify-center sm:justify-start gap-2 text-xs text-slate-400">
                    <span className="font-mono text-[11px]">SKU: {product?.sku || 'N/A'}</span>
                    <span>•</span>
                    <span className="text-slate-600 font-semibold">${Number(item.unit_price).toFixed(2)} each</span>
                  </div>
                </div>

                {/* Quantity Controls */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center border border-slate-200 rounded-xl bg-slate-50 p-1">
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      disabled={loading}
                      className="w-7 h-7 flex items-center justify-center text-slate-600 hover:bg-white rounded-lg transition"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="w-8 text-center text-xs font-bold text-slate-800">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      disabled={loading}
                      className="w-7 h-7 flex items-center justify-center text-slate-600 hover:bg-white rounded-lg transition"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <span className="text-sm font-extrabold text-slate-900 w-20 text-right">
                    ${Number(item.total_price).toFixed(2)}
                  </span>

                  <button
                    onClick={() => removeItem(item.id)}
                    className="p-2 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Order Summary Box */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
            Order Summary
          </h2>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span className="font-semibold text-slate-800">${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Estimated Shipping</span>
              <span className="font-semibold text-slate-800">
                {shipping === 0 ? <span className="text-brand-600 font-bold">FREE</span> : `$${shipping.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Sales Tax (10%)</span>
              <span className="font-semibold text-slate-800">${tax.toFixed(2)}</span>
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-between items-baseline">
              <span className="text-base font-bold text-slate-900">Total</span>
              <span className="text-2xl font-extrabold text-slate-900">${total.toFixed(2)}</span>
            </div>
          </div>

          <button
            onClick={() => onNavigate('checkout')}
            className="w-full py-3.5 px-4 rounded-xl bg-slate-900 hover:bg-brand-600 text-white font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-slate-900/10 active:scale-98"
          >
            <span>Proceed to Checkout</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-2 text-[11px] text-slate-400 justify-center">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>256-Bit SSL Encrypted Checkout</span>
          </div>
        </div>
      </div>
    </div>
  );
};
