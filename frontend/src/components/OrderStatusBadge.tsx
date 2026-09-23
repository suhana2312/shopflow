import React from 'react';
import { OrderStatus } from '../types';
import { Clock, RefreshCw, CheckCircle, Package, Truck, Award, XCircle, RotateCcw } from 'lucide-react';

interface OrderStatusBadgeProps {
  status: OrderStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const OrderStatusBadge: React.FC<OrderStatusBadgeProps> = ({ status, size = 'md' }) => {
  const configs: Record<
    OrderStatus,
    { label: string; bg: string; text: string; border: string; icon: React.ReactNode }
  > = {
    PENDING: {
      label: 'Pending',
      bg: 'bg-amber-50',
      text: 'text-amber-700',
      border: 'border-amber-200',
      icon: <Clock className="w-3.5 h-3.5" />,
    },
    PAYMENT_PROCESSING: {
      label: 'Payment Processing',
      bg: 'bg-indigo-50',
      text: 'text-indigo-700',
      border: 'border-indigo-200',
      icon: <RefreshCw className="w-3.5 h-3.5 animate-spin" />,
    },
    CONFIRMED: {
      label: 'Confirmed',
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      border: 'border-emerald-200',
      icon: <CheckCircle className="w-3.5 h-3.5" />,
    },
    PACKED: {
      label: 'Packed',
      bg: 'bg-teal-50',
      text: 'text-teal-700',
      border: 'border-teal-200',
      icon: <Package className="w-3.5 h-3.5" />,
    },
    SHIPPED: {
      label: 'Shipped',
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
      icon: <Truck className="w-3.5 h-3.5" />,
    },
    DELIVERED: {
      label: 'Delivered',
      bg: 'bg-emerald-100',
      text: 'text-emerald-800',
      border: 'border-emerald-300',
      icon: <Award className="w-3.5 h-3.5" />,
    },
    CANCELLED: {
      label: 'Cancelled',
      bg: 'bg-rose-50',
      text: 'text-rose-700',
      border: 'border-rose-200',
      icon: <XCircle className="w-3.5 h-3.5" />,
    },
    REFUNDED: {
      label: 'Refunded',
      bg: 'bg-slate-100',
      text: 'text-slate-700',
      border: 'border-slate-300',
      icon: <RotateCcw className="w-3.5 h-3.5" />,
    },
  };

  const current = configs[status] || configs.PENDING;

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-semibold rounded-full border shadow-xs ${current.bg} ${current.text} ${current.border} ${sizeClasses}`}
    >
      {current.icon}
      {current.label}
    </span>
  );
};
