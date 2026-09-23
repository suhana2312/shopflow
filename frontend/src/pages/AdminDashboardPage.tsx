import React, { useEffect, useState, useCallback } from 'react';
import { adminApi } from '../api/client';
import { Order, InventoryItem, OrderStatus } from '../types';
import { OrderStatusBadge } from '../components/OrderStatusBadge';
import { useToast } from '../context/ToastContext';
import {
  ShieldCheck,
  TrendingUp,
  Package,
  AlertTriangle,
  Radio,
  RefreshCw,
  Plus,
  Minus,
  CheckCircle,
  Clock,
  Layers,
  Activity,
  ChevronRight,
  Database,
} from 'lucide-react';

export const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'orders' | 'inventory' | 'telemetry'>('orders');
  const [metrics, setMetrics] = useState<any>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [dlqItems, setDlqItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Inventory adjustment modal/state
  const [adjustingProduct, setAdjustingProduct] = useState<InventoryItem | null>(null);
  const [adjustDelta, setAdjustDelta] = useState<number>(5);
  const [adjustReason, setAdjustReason] = useState<string>('Restock from warehouse batch');
  const [isAdjusting, setIsAdjusting] = useState(false);

  const { success, error, info } = useToast();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashMetrics, ordersRes, invData, logs, dlq] = await Promise.all([
        adminApi.getMetrics().catch(() => null),
        adminApi.getOrders({ page_size: 50 }).catch(() => ({ data: [] })),
        adminApi.getInventory().catch(() => []),
        adminApi.getAuditLogs(30).catch(() => []),
        adminApi.getDlq().catch(() => []),
      ]);

      if (dashMetrics) setMetrics(dashMetrics);
      if (ordersRes?.data) setOrders(ordersRes.data);
      if (invData) setInventory(invData);
      if (logs) setAuditLogs(logs);
      if (dlq) setDlqItems(dlq);
    } catch (err) {
      console.error('Failed to load admin dashboard data', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleUpdateStatus = async (orderId: string, nextStatus: OrderStatus) => {
    try {
      const updated = await adminApi.updateOrderStatus(orderId, nextStatus);
      setOrders((prev) => prev.map((o) => (o.id === orderId ? updated : o)));
      success(
        'Status Dispatched',
        `Order #${updated.order_number} moved to ${nextStatus}. Outbox event published & WebSocket broadcasted.`
      );
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Failed to update order status';
      error('Update Failed', msg);
    }
  };

  const handleAdjustInventory = async () => {
    if (!adjustingProduct) return;
    setIsAdjusting(true);
    try {
      const updated = await adminApi.adjustInventory(adjustingProduct.product_id, adjustDelta, adjustReason);
      setInventory((prev) =>
        prev.map((item) => (item.product_id === adjustingProduct.product_id ? updated : item))
      );
      success(
        'Inventory Adjusted',
        `Stock modified by ${adjustDelta > 0 ? '+' : ''}${adjustDelta}. New available: ${updated.available_quantity}`
      );
      setAdjustingProduct(null);
      await loadData();
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Inventory adjustment failed';
      error('Adjustment Error', msg);
    } finally {
      setIsAdjusting(false);
    }
  };

  if (loading && !metrics) {
    return (
      <div className="py-32 text-center">
        <RefreshCw className="w-8 h-8 text-purple-600 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-500">Querying administration telemetry & queues...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* Title & Refresh */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Admin Control Center</h1>
            <span className="text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 px-2.5 py-0.5 rounded-full">
              System Admin
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time state machine orchestrator, transactional outbox monitor & row-locked inventory controls
          </p>
        </div>

        <button
          onClick={loadData}
          className="px-4 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition flex items-center gap-1.5 self-start sm:self-auto shadow-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* High-Level Telemetry Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Orders */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Total Orders</span>
            <Package className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">
            {metrics?.total_orders ?? orders.length}
          </p>
          <span className="text-[11px] text-emerald-600 font-medium flex items-center gap-1 mt-1">
            <TrendingUp className="w-3 h-3" /> Live Transaction Records
          </span>
        </div>

        {/* Total Revenue */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Gross Revenue</span>
            <TrendingUp className="w-4 h-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-extrabold text-slate-900">
            ${Number(metrics?.total_revenue ?? 0).toFixed(2)}
          </p>
          <span className="text-[11px] text-slate-500 mt-1 block">ACID Settled Payments</span>
        </div>

        {/* Low Stock Alerts */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Low Stock Items</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-extrabold text-amber-600">
            {metrics?.low_stock_products_count ?? inventory.filter((i) => i.available_quantity <= 3).length}
          </p>
          <span className="text-[11px] text-amber-700 mt-1 block">Threshold: &le; 3 units</span>
        </div>

        {/* Outbox Pending */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold">Outbox / DLQ Queue</span>
            <Activity className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-2xl font-extrabold text-purple-600">
            {metrics?.pending_outbox_events ?? 0}
          </p>
          <span className="text-[11px] text-slate-500 mt-1 block">
            DLQ Failures: <span className="font-mono text-rose-600">{dlqItems.length}</span>
          </span>
        </div>
      </div>

      {/* Tabs Selector */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('orders')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'orders'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Orders Management ({orders.length})
        </button>
        <button
          onClick={() => setActiveTab('inventory')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'inventory'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Inventory Control ({inventory.length})
        </button>
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
            activeTab === 'telemetry'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Outbox & System Audit Logs
        </button>
      </div>

      {/* Tab 1: Orders Management */}
      {activeTab === 'orders' && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3">Order Number</th>
                  <th className="px-5 py-3">Customer ID</th>
                  <th className="px-5 py-3">Items</th>
                  <th className="px-5 py-3">Total</th>
                  <th className="px-5 py-3">Current Status</th>
                  <th className="px-5 py-3">Trigger State Machine Transition</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-4 font-mono font-bold text-slate-900">
                      {ord.order_number}
                    </td>
                    <td className="px-5 py-4 text-slate-600">User #{ord.user_id}</td>
                    <td className="px-5 py-4 text-slate-600 font-medium">
                      {ord.items?.length || 0} items
                    </td>
                    <td className="px-5 py-4 font-bold text-slate-900">
                      ${Number(ord.total_amount).toFixed(2)}
                    </td>
                    <td className="px-5 py-4">
                      <OrderStatusBadge status={ord.status} size="sm" />
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <select
                          value={ord.status}
                          onChange={(e) => handleUpdateStatus(ord.id, e.target.value as OrderStatus)}
                          className="bg-white border border-slate-200 text-slate-800 rounded-lg px-2.5 py-1 text-xs font-semibold focus:ring-2 focus:ring-brand-500"
                        >
                          <option value="PENDING">PENDING</option>
                          <option value="PAYMENT_PROCESSING">PAYMENT_PROCESSING</option>
                          <option value="CONFIRMED">CONFIRMED</option>
                          <option value="PACKED">PACKED</option>
                          <option value="SHIPPED">SHIPPED</option>
                          <option value="DELIVERED">DELIVERED</option>
                          <option value="CANCELLED">CANCELLED</option>
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Inventory Control */}
      {activeTab === 'inventory' && (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700">
              Active Stock Levels & Reservation Ledger
            </span>
            <span className="text-[11px] text-slate-500">
              Row-level locking protects each modification
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-white border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3">Product Name</th>
                  <th className="px-5 py-3">SKU</th>
                  <th className="px-5 py-3">Total Quantity</th>
                  <th className="px-5 py-3">Reserved Stock</th>
                  <th className="px-5 py-3">Available for Sale</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {inventory.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-5 py-4 font-bold text-slate-900">
                      {inv.product_title || `Product #${inv.product_id}`}
                    </td>
                    <td className="px-5 py-4 font-mono text-slate-500">{inv.product_sku || 'N/A'}</td>
                    <td className="px-5 py-4 font-bold text-slate-800">{inv.total_quantity}</td>
                    <td className="px-5 py-4 font-bold text-amber-600">{inv.reserved_quantity}</td>
                    <td className="px-5 py-4 font-extrabold text-emerald-600">
                      {inv.available_quantity}
                    </td>
                    <td className="px-5 py-4">
                      {inv.available_quantity <= 0 ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800">
                          Out of Stock
                        </span>
                      ) : inv.available_quantity === 1 ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 animate-pulse">
                          Flash Stock: 1
                        </span>
                      ) : inv.available_quantity <= 3 ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700">
                          Low Stock
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700">
                          Healthy
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button
                        onClick={() => {
                          setAdjustingProduct(inv);
                          setAdjustDelta(5);
                          setAdjustReason('Restock shipment');
                        }}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs transition"
                      >
                        Adjust Stock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Outbox & Telemetry */}
      {activeTab === 'telemetry' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Audit Logs */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-600" />
              <span>Immutable Audit Logs</span>
            </h3>
            <p className="text-xs text-slate-500">
              Every inventory change and state transition is captured with actor traceability:
            </p>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {auditLogs.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No audit records recorded yet.</p>
              ) : (
                auditLogs.map((log) => (
                  <div key={log.id} className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1">
                    <div className="flex items-center justify-between font-medium">
                      <span className="font-bold text-slate-800 uppercase tracking-wide text-[11px]">
                        {log.action}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-slate-600">
                      Entity: <span className="font-mono text-slate-800">{log.entity_type} #{log.entity_id}</span>
                    </div>
                    {log.details && (
                      <pre className="text-[10px] bg-white p-1.5 rounded border border-slate-200 font-mono text-slate-600 overflow-x-auto">
                        {typeof log.details === 'string' ? log.details : JSON.stringify(log.details)}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* DLQ & Dead-Letter Inspection */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-rose-600" />
              <span>RabbitMQ Dead-Letter Exchange (DLQ)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Failed Celery tasks and poison pills routed to the DLQ after exhausting retry attempts:
            </p>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {dlqItems.length === 0 ? (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span>DLQ is completely clean. All async worker tasks executed successfully.</span>
                </div>
              ) : (
                dlqItems.map((item, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs space-y-1">
                    <div className="flex justify-between font-bold text-rose-900">
                      <span>{item.task_name || 'Failed Task'}</span>
                      <span className="text-[10px] font-mono">{item.timestamp}</span>
                    </div>
                    <p className="text-rose-700 font-mono text-[11px]">{item.error || 'Max retries exceeded'}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Adjustment Modal */}
      {adjustingProduct && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-md w-full shadow-2xl space-y-4 animate-scale-in">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">
                Adjust Inventory: {adjustingProduct.product_title}
              </h3>
              <button
                onClick={() => setAdjustingProduct(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-slate-600 space-y-2">
              <div className="flex justify-between">
                <span>Current Total Stock:</span>
                <span className="font-bold text-slate-900">{adjustingProduct.total_quantity}</span>
              </div>
              <div className="flex justify-between">
                <span>Reserved by Customers:</span>
                <span className="font-bold text-amber-600">{adjustingProduct.reserved_quantity}</span>
              </div>
              <div className="flex justify-between">
                <span>Currently Available:</span>
                <span className="font-bold text-emerald-600">{adjustingProduct.available_quantity}</span>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Stock Delta (+ to add, - to deduct)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={adjustDelta}
                    onChange={(e) => setAdjustDelta(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 font-mono font-bold"
                  />
                  <div className="flex gap-1">
                    <button
                      type="button"
                      onClick={() => setAdjustDelta((d) => d + 5)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold text-xs"
                    >
                      +5
                    </button>
                    <button
                      type="button"
                      onClick={() => setAdjustDelta((d) => d - 1)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold text-xs"
                    >
                      -1
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Audit Log Reason</label>
                <input
                  type="text"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200"
                  placeholder="e.g. Inbound shipment arrival"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setAdjustingProduct(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isAdjusting}
                onClick={handleAdjustInventory}
                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md"
              >
                {isAdjusting ? 'Committing...' : 'Apply Row-Locked Update'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
