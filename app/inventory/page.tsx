'use client';

import React from 'react';
import InventoryCard from '@/components/dashboard/InventoryCard';
import { DEFAULT_DASHBOARD_DATA } from '@/lib/api';
import { Package, ShieldAlert, DollarSign, Activity } from 'lucide-react';

export default function InventoryPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-600" />
          <h1 className="text-xl font-bold text-slate-900">Inventory Optimization & Cost Policy</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Uncertainty-aware newsvendor optimization balancing holding costs ($C_h$) against stockout penalties ($C_s$).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5">
          <InventoryCard data={DEFAULT_DASHBOARD_DATA.inventory} />
        </div>

        <div className="lg:col-span-7 space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-3">Cost Trade-Off Policy Benchmarks</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-xs font-semibold text-slate-500 uppercase block">Fixed Order Policy</span>
                <div className="text-2xl font-bold text-slate-900 mt-1">$1,420 / wk</div>
                <p className="text-xs text-slate-500 mt-1">Total expected holding + stockout penalty</p>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <span className="text-xs font-bold text-blue-800 uppercase block">DemandPulse Uncertainty Policy (P90)</span>
                <div className="text-2xl font-extrabold text-[#1D5EFF] mt-1">$540 / wk</div>
                <p className="text-xs text-emerald-600 font-bold mt-1">↓ 61.9% reduction in total inventory costs</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-3">Service Level Target Alignment</h2>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-2.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Target Fill Rate</span>
                <span className="font-bold text-slate-900">95.0%</span>
              </div>
              <div className="flex items-center justify-between p-2.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Calculated Safety Stock (Units)</span>
                <span className="font-bold text-slate-900">85 units</span>
              </div>
              <div className="flex items-center justify-between p-2.5 border-b border-slate-100">
                <span className="font-semibold text-slate-700">Reorder Point (ROP)</span>
                <span className="font-bold text-slate-900">595 units</span>
              </div>
              <div className="flex items-center justify-between p-2.5">
                <span className="font-semibold text-slate-700">Monte Carlo Simulated Stockout Probability</span>
                <span className="font-bold text-emerald-600">4.8% (Target &lt; 5.0%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
