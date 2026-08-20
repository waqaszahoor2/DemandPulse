'use client';

import React, { useState } from 'react';
import { Calendar, ChevronDown, Bell, CheckCircle2 } from 'lucide-react';

interface HeaderProps {
  selectedDateRange?: string;
  onDateRangeChange?: (val: string) => void;
  selectedModel?: string;
  onModelChange?: (val: string) => void;
}

export default function Header({
  selectedDateRange = 'May 12 – May 18, 2025',
  onDateRangeChange,
  selectedModel = 'Champion v1',
  onModelChange,
}: HeaderProps) {
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [dateDropdownOpen, setDateDropdownOpen] = useState(false);

  const models = ['Champion v1', 'Candidate v2 (Experimental)', 'LightGBM-Baseline', 'ARIMA-Seasonal'];
  const dateRanges = ['May 12 – May 18, 2025', 'May 05 – May 11, 2025', 'May 01 – May 31, 2025', 'Custom Range...'];

  return (
    <header className="hidden lg:flex items-center justify-between h-16 px-6 bg-white border-b border-slate-200 sticky top-0 z-20 shadow-xs">
      {/* Title & Subtitle */}
      <div className="flex items-baseline gap-3">
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">DemandPulse</h1>
        <span className="text-xs font-medium text-slate-500">Retail Demand Intelligence Platform</span>
      </div>

      {/* Header Controls */}
      <div className="flex items-center gap-3">
        {/* Date Selector */}
        <div className="relative">
          <button
            onClick={() => setDateDropdownOpen(!dateDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
          >
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>{selectedDateRange}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>
          {dateDropdownOpen && (
            <div className="absolute right-0 mt-1 w-56 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-30 text-xs">
              {dateRanges.map((range) => (
                <button
                  key={range}
                  onClick={() => {
                    if (onDateRangeChange) onDateRangeChange(range);
                    setDateDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 hover:bg-slate-50 ${
                    selectedDateRange === range ? 'font-semibold text-blue-600 bg-blue-50/50' : 'text-slate-700'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Model Selector */}
        <div className="relative">
          <button
            onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
          >
            <span className="text-slate-500">Model:</span>
            <span className="font-semibold text-slate-900">{selectedModel}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>
          {modelDropdownOpen && (
            <div className="absolute right-0 mt-1 w-56 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-30 text-xs">
              {models.map((m) => (
                <button
                  key={m}
                  onClick={() => {
                    if (onModelChange) onModelChange(m);
                    setModelDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 hover:bg-slate-50 ${
                    selectedModel === m ? 'font-semibold text-blue-600 bg-blue-50/50' : 'text-slate-700'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/80 rounded-full">
          <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
          <span>Healthy</span>
        </div>

        {/* Notification Bell */}
        <button
          aria-label="Notifications"
          className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full"></span>
        </button>

        {/* User Profile Avatar */}
        <div className="w-8 h-8 rounded-full bg-[#1D5EFF] text-white flex items-center justify-center text-xs font-bold shadow-xs">
          AR
        </div>
      </div>
    </header>
  );
}
