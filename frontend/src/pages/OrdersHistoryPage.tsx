import React, { useEffect, useState } from 'react';
import { Order } from '../types';
import { ordersApi } from '../api/client';
import { OrderStatusBadge } from '../components/OrderStatusBadge';
import { Package, Calendar, ChevronRight, RefreshCw, ShoppingBag } from 'lucide-react';

interface OrdersHistoryPageProps {
  onSelectOrder: (orderId: string) => void;
  onNavigate: (view: string) => void;
}

export const OrdersHistoryPage: React.FC<OrdersHistoryPageProps> = ({ onSelectOrder, onNavigate }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      try {
        const res = await ordersApi.list({ limit: 50 });
        setOrders(Array.isArray(res) ? res : []);
      } catch (err) {
        console.error('Failed to load orders', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, []);

  if (loading) {
    return (
      <div className="py-32 text-center">
        <RefreshCw className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-500">Retrieving order history from database...</p>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="py-24 text-center max-w-md mx-auto space-y-4">
        <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <Package className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">No orders placed yet</h2>
        <p className="text-sm text-slate-500">
          When you purchase items through our concurrent checkout engine, you can track them here in real-time.
        </p>
        <button
          onClick={() => onNavigate('products')}
          className="mt-4 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm transition shadow-md shadow-brand-500/20"
        >
          Explore Catalog
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">My Orders</h1>
        <p className="text-xs text-slate-500 mt-1">
          Historical order records with live WebSocket tracking links
        </p>
      </div>

      <div className="space-y-4">
        {orders.map((order) => (
          <div
            key={order.id}
            onClick={() => onSelectOrder(order.id)}
            className="group bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-md hover:border-brand-200 transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-bold text-slate-900">
                  #{order.order_number}
                </span>
                <OrderStatusBadge status={order.status} size="sm" />
              </div>

              <div className="text-xs text-slate-500 flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  {new Date(order.created_at).toLocaleDateString()}
                </span>
                <span>•</span>
                <span>{order.items?.length || 0} item(s)</span>
              </div>

              <p className="text-xs text-slate-600 line-clamp-1">
                {order.items?.map((i) => `${i.product_title} (×${i.quantity})`).join(', ')}
              </p>
            </div>

            <div className="flex items-center justify-between sm:justify-end gap-6 pt-3 sm:pt-0 border-t sm:border-t-0 border-slate-100">
              <div className="text-left sm:text-right">
                <span className="block text-[11px] text-slate-400">Total</span>
                <span className="text-base font-extrabold text-slate-900">
                  ${Number(order.total_amount).toFixed(2)}
                </span>
              </div>

              <div className="flex items-center gap-1 text-xs font-bold text-brand-600 group-hover:text-brand-700">
                <span>Track Live</span>
                <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
