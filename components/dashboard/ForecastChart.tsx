'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { ForecastPoint } from '@/lib/api';
import { Maximize2, ChevronDown } from 'lucide-react';

interface ForecastChartProps {
  data: ForecastPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const pData = payload[0].payload as ForecastPoint;
    return (
      <div className="bg-white/95 backdrop-blur-xs p-3 rounded-lg shadow-lg border border-slate-200 text-xs space-y-1 z-50">
        <p className="font-bold text-slate-900 border-b border-slate-100 pb-1">{pData.displayDate}</p>
        {!pData.isForecast ? (
          <p className="text-blue-600 font-semibold">
            Actual Demand: <span className="font-bold text-slate-900">{pData.actualDemand} units</span>
          </p>
        ) : (
          <>
            <p className="text-teal-600 font-semibold">
              Forecast (P50): <span className="font-bold text-slate-900">{pData.forecastP50} units</span>
            </p>
            <p className="text-blue-500">
              P10 (Low): <span className="font-semibold">{pData.p10} units</span>
            </p>
            <p className="text-purple-600">
              P90 (High): <span className="font-semibold">{pData.p90} units</span>
            </p>
            <p className="text-slate-400 text-[10px] pt-1">Conformal Interval: 80% coverage</p>
          </>
        )}
      </div>
    );
  }
  return null;
};

export default function ForecastChart({ data }: ForecastChartProps) {
  const [storeFilter, setStoreFilter] = useState('All Stores');
  const [productFilter, setProductFilter] = useState('All Products');
  const [horizonFilter, setHorizonFilter] = useState('7 Days');

  return (
    <div className="bg-white rounded-xl p-4 md:p-6 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base md:text-lg font-bold text-slate-900 tracking-tight">
              Demand Forecast & Uncertainty
            </h2>
            <button aria-label="Maximize view" className="text-slate-400 hover:text-slate-600 p-1 rounded-md hidden md:inline-block">
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-lg">
            <span className="text-slate-500 font-medium">Store:</span>
            <select
              value={storeFilter}
              onChange={(e) => setStoreFilter(e.target.value)}
              className="bg-transparent font-semibold text-slate-800 outline-none cursor-pointer pr-1"
            >
              <option>All Stores</option>
              <option>Store #101 (Boston)</option>
              <option>Store #104 (NY Central)</option>
            </select>
          </div>

          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-lg">
            <span className="text-slate-500 font-medium">Product:</span>
            <select
              value={productFilter}
              onChange={(e) => setProductFilter(e.target.value)}
              className="bg-transparent font-semibold text-slate-800 outline-none cursor-pointer pr-1"
            >
              <option>All Products</option>
              <option>Fresh Beverage 500ml</option>
              <option>Organic Snack Bar</option>
            </select>
          </div>

          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 px-2.5 py-1.5 rounded-lg">
            <span className="text-slate-500 font-medium">Horizon:</span>
            <select
              value={horizonFilter}
              onChange={(e) => setHorizonFilter(e.target.value)}
              className="bg-transparent font-semibold text-slate-800 outline-none cursor-pointer pr-1"
            >
              <option>7 Days</option>
              <option>14 Days</option>
              <option>30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Legend Row */}
      <div className="flex flex-wrap items-center gap-4 text-xs mb-4 text-slate-600 font-medium">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
          <span>Historical Sales</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-blue-600 inline-block"></span>
          <span>Actual Demand</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-teal-500 border-b border-dashed border-teal-500 inline-block"></span>
          <span>Forecast (P50)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-2.5 bg-blue-100/80 border border-blue-300 rounded-xs inline-block"></span>
          <span>P10 – P90 Range</span>
        </div>
      </div>

      {/* Recharts Canvas */}
      <div className="w-full h-72 md:h-80 relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="displayDate"
              tick={{ fontSize: 11, fill: '#64748B' }}
              axisLine={{ stroke: '#CBD5E1' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748B' }}
              axisLine={false}
              tickLine={false}
              domain={[0, 1200]}
              ticks={[0, 200, 400, 600, 800, 1000, 1200]}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Vertical boundary line dividing history & forecast */}
            <ReferenceLine x="May 11" stroke="#94A3B8" strokeDasharray="4 4" label={{ value: 'Forecast', position: 'top', fill: '#94A3B8', fontSize: 10 }} />

            {/* P10 - P90 Area Range */}
            <Area
              type="monotone"
              dataKey="p10p90Range"
              stroke="none"
              fill="#DBEAFE"
              fillOpacity={0.75}
              isAnimationActive={true}
            />

            {/* Forecast P50 Line */}
            <Line
              type="monotone"
              dataKey="forecastP50"
              stroke="#0D9488"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 3, fill: '#0D9488' }}
              connectNulls
            />

            {/* Actual Demand / Historical Line */}
            <Line
              type="monotone"
              dataKey="actualDemand"
              stroke="#1D5EFF"
              strokeWidth={2.5}
              dot={{ r: 4, fill: '#1D5EFF', strokeWidth: 1, stroke: '#FFFFFF' }}
              activeDot={{ r: 6 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Bottom Subtext */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 border-t border-slate-100 pt-2">
        <span className="font-semibold uppercase tracking-wider">History</span>
        <span className="font-semibold uppercase tracking-wider text-teal-600">7-Day Out-of-Sample Forecast</span>
      </div>
    </div>
  );
}
