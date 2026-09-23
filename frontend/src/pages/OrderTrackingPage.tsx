import React, { useEffect, useState, useCallback } from 'react';
import { Order, OrderStatus } from '../types';
import { ordersApi } from '../api/client';
import { OrderTimeline } from '../components/OrderTimeline';
import { OrderStatusBadge } from '../components/OrderStatusBadge';
import { useToast } from '../context/ToastContext';
import {
  ArrowLeft,
  Package,
  MapPin,
  CreditCard,
  XCircle,
  RefreshCw,
  FileText,
  Calendar,
  AlertCircle,
} from 'lucide-react';

interface OrderTrackingPageProps {
  orderId: string;
  onBack: () => void;
}

export const OrderTrackingPage: React.FC<OrderTrackingPageProps> = ({ orderId, onBack }) => {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);
  const { success, error } = useToast();

  const fetchOrder = useCallback(async () => {
    try {
      const data = await ordersApi.getById(orderId);
      setOrder(data);
    } catch (err: any) {
      console.error('Failed to load order', err);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    fetchOrder();
  }, [fetchOrder]);

  const handleStatusChange = (newStatus: OrderStatus) => {
    setOrder((prev) => (prev ? { ...prev, status: newStatus } : null));
  };

  const handleCancel = async () => {
    if (!order) return;
    if (!confirm('Are you sure you want to cancel this order and release reserved stock?')) return;

    setIsCancelling(true);
    try {
      const updated = await ordersApi.cancel(order.id);
      setOrder(updated);
      success('Order Cancelled', 'Reserved inventory has been unlocked and restored to available stock.');
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Could not cancel order';
      error('Cancellation Failed', msg);
    } finally {
      setIsCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="py-32 text-center">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-500">Connecting to real-time order stream...</p>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="py-24 text-center max-w-md mx-auto space-y-4">
        <p className="text-slate-600 font-semibold">Order #{orderId} could not be found.</p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold"
        >
          Back to Orders
        </button>
      </div>
    );
  }

  const isCancellable = order.status === 'PENDING' || order.status === 'PAYMENT_PROCESSING';

  return (
    <div className="space-y-8 pb-16">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl border border-slate-200 hover:bg-slate-100 transition text-slate-600"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                Order #{order.order_number}
              </h1>
              <OrderStatusBadge status={order.status} />
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {new Date(order.created_at).toLocaleString()}
              </span>
              <span>•</span>
              <span className="font-mono text-slate-500">ID: {order.id}</span>
            </div>
          </div>
        </div>

        {isCancellable && (
          <button
            onClick={handleCancel}
            disabled={isCancelling}
            className="px-4 py-2 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs transition flex items-center gap-1.5 self-start sm:self-auto"
          >
            {isCancelling ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <XCircle className="w-3.5 h-3.5" />
            )}
            <span>Cancel Order & Release Stock</span>
          </button>
        )}
      </div>

      {/* Live WebSocket Timeline */}
      <OrderTimeline
        orderId={order.id}
        initialStatus={order.status}
        onStatusChange={handleStatusChange}
      />

      {/* Order Details & Logistics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ordered Items */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Package className="w-4 h-4 text-slate-600" />
            <span>Order Line Items</span>
          </h2>

          <div className="divide-y divide-slate-100">
            {(order.items || []).map((item) => (
              <div key={item.id} className="py-3.5 flex items-center justify-between text-sm">
                <div>
                  <h4 className="font-semibold text-slate-900">{item.product_name || item.product_title || 'Item'}</h4>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">
                    {item.product_sku ? `SKU: ${item.product_sku} • ` : ''}Qty: {item.quantity} × ${Number(item.unit_price).toFixed(2)}
                  </div>
                </div>
                <span className="font-extrabold text-slate-900">
                  ${Number(item.subtotal || item.total_price || (Number(item.unit_price) * item.quantity)).toFixed(2)}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-slate-200 space-y-2 text-xs">
            <div className="flex justify-between text-slate-600">
              <span>Subtotal</span>
              <span className="font-semibold text-slate-800">${Number(order.subtotal || 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Shipping Fee</span>
              <span className="font-semibold text-slate-800">${Number(order.shipping_fee ?? order.shipping_amount ?? 0).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-slate-600">
              <span>Tax</span>
              <span className="font-semibold text-slate-800">${Number(order.tax ?? order.tax_amount ?? 0).toFixed(2)}</span>
            </div>
            <div className="pt-2 border-t border-slate-100 flex justify-between text-sm">
              <span className="font-bold text-slate-900">Total Paid</span>
              <span className="font-extrabold text-base text-slate-900">${Number(order.total_amount || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Shipping & Payment Cards */}
        <div className="space-y-6">
          {/* Shipping Address */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-brand-600" />
              <span>Delivery Destination</span>
            </h3>
            <div className="text-xs text-slate-600 space-y-1">
              <p className="font-bold text-slate-800">{order.shipping_address?.full_name}</p>
              <p>{order.shipping_address?.address_line1 || order.shipping_address?.street || ''}</p>
              {order.shipping_address?.address_line2 && <p>{order.shipping_address?.address_line2}</p>}
              <p>
                {order.shipping_address?.city}, {order.shipping_address?.state} {order.shipping_address?.postal_code}
              </p>
              <p className="text-slate-400">{order.shipping_address?.country}</p>
            </div>
          </div>

          {/* Payment Details */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-indigo-600" />
              <span>Payment Telemetry</span>
            </h3>
            <div className="text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">Method</span>
                <span className="font-semibold text-slate-800">{order.payment?.payment_method || 'Credit Card'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Payment Status</span>
                <span className="font-semibold text-emerald-600">{order.payment?.status || 'AUTHORIZED'}</span>
              </div>
              {order.payment?.transaction_id && (
                <div className="pt-2 border-t border-slate-100">
                  <span className="block text-[10px] text-slate-400 font-mono">TX ID:</span>
                  <span className="font-mono text-[11px] text-slate-700 break-all">{order.payment.transaction_id}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
