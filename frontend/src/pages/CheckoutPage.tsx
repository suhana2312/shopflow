import React, { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { checkoutApi } from '../api/client';
import {
  ShieldCheck,
  CreditCard,
  Key,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  Lock,
  Flame,
  CheckCircle2,
} from 'lucide-react';

interface CheckoutPageProps {
  onOrderPlaced: (orderId: string) => void;
  onNavigate: (view: string) => void;
}

export const CheckoutPage: React.FC<CheckoutPageProps> = ({ onOrderPlaced, onNavigate }) => {
  const { cart, refreshCart } = useCart();
  const { user } = useAuth();
  const { success, error, warning } = useToast();

  const [address, setAddress] = useState({
    full_name: user?.full_name || 'Sarah Connor',
    street: '742 Cyberdyne Blvd, Suite 400',
    city: 'San Francisco',
    state: 'CA',
    postal_code: '94105',
    country: 'United States',
    phone: '+14155552671',
  });

  const [simulationOutcome, setSimulationOutcome] = useState<'success' | 'insufficient_funds' | 'timeout'>('success');
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() =>
    typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'idem-' + Math.random().toString(36).substring(2)
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const subtotal = cart?.subtotal || 0;
  const shipping = subtotal > 150 || subtotal === 0 ? 0 : 15.0;
  const tax = Number((subtotal * 0.1).toFixed(2));
  const total = Number((subtotal + shipping + tax).toFixed(2));

  const regenerateKey = () => {
    const newKey = typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : 'idem-' + Math.random().toString(36).substring(2);
    setIdempotencyKey(newKey);
  };

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cart || cart.items.length === 0) {
      warning('Empty Cart', 'Please add items to your cart before checking out.');
      return;
    }

    setIsSubmitting(true);
    try {
      const order = await checkoutApi.checkout(
        {
          shipping_address: address,
          payment_method: 'credit_card',
          simulation_outcome: simulationOutcome,
        },
        idempotencyKey
      );

      await refreshCart();

      if (simulationOutcome === 'success') {
        success('Order Placed Successfully!', `Order #${order.order_number} confirmed with atomic lock.`);
      } else {
        warning('Payment Simulation Handled', `Simulation result: ${simulationOutcome}. Status: ${order.status}`);
      }

      onOrderPlaced(order.id);
    } catch (err: any) {
      const status = err.response?.status;
      const data = err.response?.data;
      const errorCode = data?.error?.code;
      const msg = data?.error?.message || 'Checkout failed.';

      if (status === 409 || errorCode === 'OUT_OF_STOCK') {
        error(
          '⚡ Concurrency Conflict Detected!',
          'Another concurrent thread purchased the remaining inventory. Zero overselling was strictly maintained by row-level locking.'
        );
      } else {
        error('Checkout Failed', msg);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Atomic Checkout</h1>
        <p className="text-xs text-slate-500 mt-1">
          Guaranteed reservation state machine backed by ACID database transactions
        </p>
      </div>

      {/* Concurrency architecture notification */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-brand-50 to-blue-50 border border-brand-200 flex items-start gap-3 shadow-xs">
        <ShieldCheck className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 leading-relaxed">
          <span className="font-bold text-slate-900 block mb-0.5">Distributed Concurrency Protection</span>
          Checkout applies a row-level <code className="font-mono text-brand-800 bg-white/80 px-1 py-0.5 rounded border border-brand-200">SELECT FOR UPDATE</code> with an atomic conditional decrement (<code className="font-mono text-brand-800 bg-white/80 px-1 py-0.5 rounded border border-brand-200">WHERE available &gt;= qty</code>). Even under high-concurrency flash sales, race conditions are mathematically prevented.
        </div>
      </div>

      <form onSubmit={handlePlaceOrder} className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Left 2 Cols: Shipping & Payment Options */}
        <div className="lg:col-span-2 space-y-6">
          {/* Shipping Address */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>Shipping Information</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Full Recipient Name</label>
                <input
                  type="text"
                  required
                  value={address.full_name}
                  onChange={(e) => setAddress({ ...address, full_name: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-600 mb-1">Street Address</label>
                <input
                  type="text"
                  required
                  value={address.street}
                  onChange={(e) => setAddress({ ...address, street: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Phone Number</label>
                <input
                  type="tel"
                  required
                  value={address.phone}
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">City</label>
                <input
                  type="text"
                  required
                  value={address.city}
                  onChange={(e) => setAddress({ ...address, city: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">State / Province</label>
                <input
                  type="text"
                  required
                  value={address.state}
                  onChange={(e) => setAddress({ ...address, state: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Postal Code</label>
                <input
                  type="text"
                  required
                  value={address.postal_code}
                  onChange={(e) => setAddress({ ...address, postal_code: e.target.value })}
                  className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>
          </div>

          {/* Payment Gateway Simulation Controls */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-slate-700" />
                <span>Simulated Payment Gateway</span>
              </h2>
              <span className="text-[11px] font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                Test Mode
              </span>
            </div>

            <p className="text-xs text-slate-500">
              Select the simulated payment outcome to evaluate distributed rollback, idempotency, or successful real-time state transitions:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Success */}
              <label
                className={`flex flex-col p-3.5 rounded-xl border-2 cursor-pointer transition ${
                  simulationOutcome === 'success'
                    ? 'border-emerald-500 bg-emerald-50/50 text-emerald-900 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="simulation"
                  value="success"
                  checked={simulationOutcome === 'success'}
                  onChange={() => setSimulationOutcome('success')}
                  className="sr-only"
                />
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold">🟢 Success</span>
                  {simulationOutcome === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                </div>
                <span className="text-[11px] text-slate-500">Normal payment authorization & confirmation</span>
              </label>

              {/* Insufficient Funds */}
              <label
                className={`flex flex-col p-3.5 rounded-xl border-2 cursor-pointer transition ${
                  simulationOutcome === 'insufficient_funds'
                    ? 'border-rose-500 bg-rose-50/50 text-rose-900 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="simulation"
                  value="insufficient_funds"
                  checked={simulationOutcome === 'insufficient_funds'}
                  onChange={() => setSimulationOutcome('insufficient_funds')}
                  className="sr-only"
                />
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold">🔴 Card Declined</span>
                  {simulationOutcome === 'insufficient_funds' && <CheckCircle2 className="w-4 h-4 text-rose-600" />}
                </div>
                <span className="text-[11px] text-slate-500">Triggers failure handler & stock reservation rollback</span>
              </label>

              {/* Timeout */}
              <label
                className={`flex flex-col p-3.5 rounded-xl border-2 cursor-pointer transition ${
                  simulationOutcome === 'timeout'
                    ? 'border-amber-500 bg-amber-50/50 text-amber-900 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="simulation"
                  value="timeout"
                  checked={simulationOutcome === 'timeout'}
                  onChange={() => setSimulationOutcome('timeout')}
                  className="sr-only"
                />
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold">⏱️ Gateway Timeout</span>
                  {simulationOutcome === 'timeout' && <CheckCircle2 className="w-4 h-4 text-amber-600" />}
                </div>
                <span className="text-[11px] text-slate-500">Simulates upstream timeout & DLQ retry path</span>
              </label>
            </div>
          </div>

          {/* Idempotency-Key Header Inspector */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">Idempotency-Key Header</span>
              </div>
              <button
                type="button"
                onClick={regenerateKey}
                className="text-[11px] font-semibold text-brand-700 hover:text-brand-800 flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Generate New UUID
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              Protects against double-charge on network retries or duplicate clicks:
            </p>
            <div className="p-2.5 rounded-xl bg-slate-900 text-brand-300 font-mono text-xs overflow-x-auto">
              Idempotency-Key: {idempotencyKey}
            </div>
          </div>
        </div>

        {/* Right Col: Order Summary & Place Order */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
          <h2 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-100">
            Order Review ({cart?.total_items || 0} items)
          </h2>

          <div className="max-h-48 overflow-y-auto space-y-3 pr-1 text-xs">
            {cart?.items.map((item) => (
              <div key={item.id} className="flex justify-between items-center text-slate-700">
                <div className="truncate pr-2">
                  <span className="font-semibold">{item.product.title}</span>
                  <span className="text-slate-400 ml-1">× {item.quantity}</span>
                </div>
                <span className="font-mono font-bold shrink-0">${Number(item.total_price).toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="space-y-2.5 pt-4 border-t border-slate-100 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span className="font-semibold text-slate-800">${subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Shipping</span>
              <span className="font-semibold text-slate-800">
                {shipping === 0 ? <span className="text-brand-600 font-bold">FREE</span> : `$${shipping.toFixed(2)}`}
              </span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Tax</span>
              <span className="font-semibold text-slate-800">${tax.toFixed(2)}</span>
            </div>
            <div className="pt-3 border-t border-slate-100 flex justify-between items-baseline">
              <span className="text-base font-bold text-slate-900">Total</span>
              <span className="text-2xl font-extrabold text-slate-900">${total.toFixed(2)}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !cart || cart.items.length === 0}
            className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20 active:scale-98 disabled:opacity-50"
          >
            {isSubmitting ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Lock className="w-4 h-4" />
                <span>Place Order & Reserve Stock</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <p className="text-[11px] text-center text-slate-400 leading-normal">
            By placing your order, an inventory reservation is created in PostgreSQL with transactional outbox event dispatch.
          </p>
        </div>
      </form>
    </div>
  );
};
