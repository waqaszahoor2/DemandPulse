'use client';

import React from 'react';
import { Package, ShieldAlert } from 'lucide-react';
import { InventoryData } from '@/lib/api';

interface InventoryCardProps {
  data?: InventoryData;
}

export default function InventoryCard({ data }: InventoryCardProps) {
  if (!data) return null;

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600">
          <Package className="w-4 h-4" />
        </div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight">Inventory Recommendation</h2>
      </div>

      {/* Desktop Metric Rows / Mobile Responsive Layout */}
      <div className="hidden sm:block space-y-3 text-sm">
        <div className="flex items-center justify-between text-slate-600 font-medium">
          <span>Current Stock</span>
          <span className="font-bold text-slate-900">{data.currentStock}</span>
        </div>
        <div className="flex items-center justify-between text-slate-600 font-medium">
          <span>Forecast Demand</span>
          <span className="font-bold text-slate-900">{data.forecastDemand}</span>
        </div>
        <div className="flex items-center justify-between text-slate-600 font-medium">
          <span>Safety Stock</span>
          <span className="font-bold text-slate-900">{data.safetyStock}</span>
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
          <span className="font-bold text-slate-900 text-sm">Recommended Order</span>
          <span className="text-xl font-extrabold text-[#1D5EFF]">{data.recommendedOrder}</span>
        </div>
      </div>

      {/* Mobile Horizontal Layout (< 640px) */}
      <div className="sm:hidden grid grid-cols-4 gap-2 text-center p-3 bg-slate-50 rounded-lg mb-3">
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase block">Stock</span>
          <span className="text-sm font-bold text-slate-900">{data.currentStock}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase block">Forecast</span>
          <span className="text-sm font-bold text-slate-900">{data.forecastDemand}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase block">Safety</span>
          <span className="text-sm font-bold text-slate-900">{data.safetyStock}</span>
        </div>
        <div>
          <span className="text-[10px] font-semibold text-slate-500 uppercase block">Order</span>
          <span className="text-sm font-extrabold text-[#1D5EFF]">{data.recommendedOrder}</span>
        </div>
      </div>

      {/* Stockout Risk Spectrum Bar Section */}
      <div className="mt-4 pt-3 border-t border-slate-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-600">Stockout Risk</span>
          <span className="px-2 py-0.5 text-xs font-bold rounded-md bg-emerald-100 text-emerald-800">
            {data.stockoutRisk}
          </span>
        </div>

        {/* Continuous Color Spectrum Bar */}
        <div className="relative mt-2">
          <div className="h-3 w-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500 shadow-inner"></div>
          {/* Risk Pointer Indicator */}
          <div
            className="absolute top-0 -mt-1.5 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-slate-900 transform -translate-x-1/2 transition-all duration-300"
            style={{ left: `${data.riskScorePercent}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 font-medium mt-1">
          <span>Low (Optimal)</span>
          <span>Medium</span>
          <span>High (Risk)</span>
        </div>
      </div>
    </div>
  );
}
