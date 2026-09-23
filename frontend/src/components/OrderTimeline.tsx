import React, { useEffect, useState, useRef } from 'react';
import { OrderStatus } from '../types';
import { adminApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { CheckCircle2, Circle, Clock, Radio, RefreshCw, AlertCircle, ChevronRight } from 'lucide-react';

interface OrderTimelineProps {
  orderId: string;
  initialStatus: OrderStatus;
  onStatusChange?: (newStatus: OrderStatus) => void;
}

interface StatusEvent {
  time: string;
  from?: string;
  to: string;
  message?: string;
}

const LIFECYCLE_STEPS: Array<{ key: OrderStatus; title: string; desc: string }> = [
  { key: 'PENDING', title: 'Order Placed', desc: 'Order received & stock reserved' },
  { key: 'PAYMENT_PROCESSING', title: 'Payment Processing', desc: 'Gateway simulation active' },
  { key: 'CONFIRMED', title: 'Order Confirmed', desc: 'Payment verified, stock finalized' },
  { key: 'PACKED', title: 'Packed at Hub', desc: 'Items assembled and boxed' },
  { key: 'SHIPPED', title: 'Shipped', desc: 'Dispatched with carrier' },
  { key: 'DELIVERED', title: 'Delivered', desc: 'Package arrived at destination' },
];

export const OrderTimeline: React.FC<OrderTimelineProps> = ({ orderId, initialStatus, onStatusChange }) => {
  const [currentStatus, setCurrentStatus] = useState<OrderStatus>(initialStatus);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [events, setEvents] = useState<StatusEvent[]>([
    {
      time: new Date().toLocaleTimeString(),
      to: initialStatus,
      message: `Initial order state: ${initialStatus}`,
    },
  ]);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const { token, isAdmin } = useAuth();
  const { info, success, error } = useToast();

  useEffect(() => {
    setCurrentStatus(initialStatus);
  }, [initialStatus]);

  // Connect to WebSocket endpoint
  useEffect(() => {
    if (!orderId || !token) return;

    let ws: WebSocket;
    let reconnectTimeout: any;

    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/orders/${orderId}?token=${token}`;

      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'ORDER_STATUS_UPDATED') {
              const { new_status, previous_status, timestamp } = data.payload || {};
              const targetStatus = (new_status || data.new_status) as OrderStatus;
              if (targetStatus) {
                setCurrentStatus(targetStatus);
                onStatusChange?.(targetStatus);
                setEvents((prev) => [
                  {
                    time: timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString(),
                    from: previous_status,
                    to: targetStatus,
                    message: `Real-time transition: ${previous_status || 'Current'} ➔ ${targetStatus}`,
                  },
                  ...prev,
                ]);
                info('Order Updated', `Status changed to ${targetStatus}`);
              }
            } else if (data.type === 'CONNECTED') {
              // Initial connection handshake
              console.log('WS Handshake:', data.message);
            }
          } catch (e) {
            console.error('WS Parse Error', e);
          }
        };

        ws.onerror = (err) => {
          console.warn('WebSocket error:', err);
          setIsConnected(false);
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Auto reconnect after 3 seconds if not unmounted
          reconnectTimeout = setTimeout(() => {
            connect();
          }, 3000);
        };
      } catch (err) {
        console.error('WS setup error:', err);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [orderId, token, onStatusChange, info]);

  // Demo helper: simulate next transition directly
  const advanceToNext = async () => {
    const sequence: OrderStatus[] = ['PENDING', 'PAYMENT_PROCESSING', 'CONFIRMED', 'PACKED', 'SHIPPED', 'DELIVERED'];
    const currentIndex = sequence.indexOf(currentStatus);
    if (currentIndex === -1 || currentIndex >= sequence.length - 1) return;

    const nextStatus = sequence[currentIndex + 1];
    setIsAdvancing(true);
    try {
      await adminApi.updateOrderStatus(orderId, nextStatus);
      success('Transition Dispatched', `Server emitted ${nextStatus} via Outbox & WebSocket`);
    } catch (err: any) {
      error('Transition Error', err.response?.data?.error?.message || 'Cannot advance order');
    } finally {
      setIsAdvancing(false);
    }
  };

  const getStepIndex = (status: OrderStatus) => {
    return LIFECYCLE_STEPS.findIndex((s) => s.key === status);
  };

  const activeIndex = getStepIndex(currentStatus);
  const isCancelled = currentStatus === 'CANCELLED';

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
      {/* WebSocket Status Header */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-100 mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            Real-Time Order Lifecycle
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Streaming updates over bi-directional WebSocket channel
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${
              isConnected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${isConnected ? 'text-emerald-500 animate-pulse' : 'text-amber-500'}`} />
            <span>{isConnected ? 'WebSocket Live' : 'Reconnecting...'}</span>
          </div>

          {/* Quick advancement tool for demo */}
          {activeIndex >= 0 && activeIndex < LIFECYCLE_STEPS.length - 1 && !isCancelled && (
            <button
              onClick={advanceToNext}
              disabled={isAdvancing}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-brand-600 text-white transition flex items-center gap-1.5 shadow-xs"
              title="Trigger state transition to verify live WebSocket message"
            >
              {isAdvancing ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <>
                  <span>Simulate Next Stage</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* If order is Cancelled */}
      {isCancelled ? (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-3 mb-6">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <div>
            <h4 className="text-sm font-bold">This Order Has Been Cancelled</h4>
            <p className="text-xs text-rose-600 mt-0.5">
              Reserved inventory has been unlocked and restored to available stock.
            </p>
          </div>
        </div>
      ) : (
        /* Stepper progress track */
        <div className="relative mb-8">
          <div className="overflow-x-auto pb-4">
            <div className="min-w-[600px] flex items-center justify-between relative">
              {/* Connecting background line */}
              <div className="absolute top-5 left-8 right-8 h-1 bg-slate-200 -z-0" />
              {/* Active progress line */}
              <div
                className="absolute top-5 left-8 h-1 bg-brand-500 transition-all duration-700 -z-0"
                style={{
                  width: `${Math.max(0, (activeIndex / (LIFECYCLE_STEPS.length - 1)) * 100 - 5)}%`,
                }}
              />

              {LIFECYCLE_STEPS.map((step, idx) => {
                const isPassed = activeIndex > idx;
                const isCurrent = activeIndex === idx;

                return (
                  <div key={step.key} className="flex flex-col items-center relative z-10 w-28 text-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300 shadow-xs ${
                        isPassed
                          ? 'bg-brand-600 text-white'
                          : isCurrent
                          ? 'bg-brand-500 text-white ring-4 ring-brand-100 animate-pulse'
                          : 'bg-white border-2 border-slate-300 text-slate-400'
                      }`}
                    >
                      {isPassed ? (
                        <CheckCircle2 className="w-5 h-5" />
                      ) : isCurrent ? (
                        <Clock className="w-5 h-5 animate-spin" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-300" />
                      )}
                    </div>

                    <span
                      className={`mt-2.5 text-xs font-semibold ${
                        isCurrent ? 'text-brand-700' : isPassed ? 'text-slate-800' : 'text-slate-400'
                      }`}
                    >
                      {step.title}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5 leading-tight">{step.desc}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Real-time Event Log */}
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          Live Event Audit Stream
        </h4>
        <div className="space-y-1.5 max-h-36 overflow-y-auto font-mono text-xs">
          {events.map((ev, i) => (
            <div key={i} className="flex items-center gap-2 text-slate-600 py-0.5">
              <span className="text-slate-400 text-[11px] shrink-0">[{ev.time}]</span>
              <span className="text-slate-800 font-medium">{ev.message || `Status: ${ev.to}`}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
