import React from 'react';
import { Database, Cpu, Radio, Shield, GitCommit } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 py-12 border-t border-slate-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand info */}
          <div className="space-y-3">
            <h3 className="text-white font-bold text-lg tracking-tight flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
              ShopFlow Engine
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Production-grade distributed e-commerce architecture engineered for high concurrency, zero-overselling inventory control, and real-time event streaming.
            </p>
          </div>

          {/* Architecture Stack */}
          <div>
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Backend Core</h4>
            <ul className="text-xs space-y-2">
              <li className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-brand-400" />
                <span>FastAPI + Python 3.14 (Async I/O)</span>
              </li>
              <li className="flex items-center gap-2">
                <Database className="w-3.5 h-3.5 text-blue-400" />
                <span>PostgreSQL + Row-Level Locking</span>
              </li>
              <li className="flex items-center gap-2">
                <Radio className="w-3.5 h-3.5 text-purple-400" />
                <span>Redis Sliding-Window Rate Limiting</span>
              </li>
            </ul>
          </div>

          {/* Distributed Pipelines */}
          <div>
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Distributed Async</h4>
            <ul className="text-xs space-y-2">
              <li className="flex items-center gap-2">
                <GitCommit className="w-3.5 h-3.5 text-amber-400" />
                <span>RabbitMQ Message Broker</span>
              </li>
              <li className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                <span>Celery Workers & Beat Sweeper</span>
              </li>
              <li className="flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-rose-400" />
                <span>Dead-Letter Exchange (DLX/DLQ)</span>
              </li>
            </ul>
          </div>

          {/* Real-time telemetry */}
          <div>
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-3">Real-Time & Security</h4>
            <ul className="text-xs space-y-2">
              <li className="flex items-center gap-2 text-emerald-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>WebSockets Channel (/ws/orders)</span>
              </li>
              <li className="text-slate-400">Idempotency-Key Header Protection</li>
              <li className="text-slate-400">Transactional Outbox Pattern</li>
              <li className="text-slate-400">Prometheus Telemetry (/metrics)</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 ShopFlow. Designed for Senior Systems & Distributed Engineering.</p>
          <div className="flex items-center gap-4">
            <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
              Concurrency Guard: Atomic SELECT FOR UPDATE
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
