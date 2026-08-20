'use client';

import React from 'react';
import { Menu, Bell, Calendar, ChevronDown, Activity } from 'lucide-react';

interface MobileHeaderProps {
  onOpenMenu: () => void;
  selectedDateRange?: string;
  selectedModel?: string;
}

export default function MobileHeader({
  onOpenMenu,
  selectedDateRange = 'May 12 – May 18, 2025',
  selectedModel = 'Champion v1',
}: MobileHeaderProps) {
  return (
    <header className="lg:hidden bg-white border-b border-slate-200 sticky top-0 z-20 shadow-xs">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 h-14 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenMenu}
            aria-label="Open Mobile Menu"
            className="p-1.5 text-slate-700 hover:bg-slate-100 rounded-lg"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-[#1D5EFF] flex items-center justify-center text-white">
              <Activity className="w-3.5 h-3.5 stroke-[2.5]" />
            </div>
            <span className="font-bold text-slate-900 text-base tracking-tight">/DemandPulse</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button aria-label="Notifications" className="p-1.5 text-slate-600 hover:bg-slate-100 rounded-lg relative">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-blue-600 rounded-full"></span>
          </button>
          <div className="w-7 h-7 rounded-full bg-[#1D5EFF] text-white flex items-center justify-center text-xs font-bold">
            AR
          </div>
        </div>
      </div>

      {/* Mobile Filter Bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 overflow-x-auto custom-scrollbar bg-slate-50/80 border-t border-slate-100">
        <button className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-md shadow-2xs whitespace-nowrap">
          <Calendar className="w-3 h-3 text-slate-500" />
          <span>{selectedDateRange}</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>

        <button className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-md shadow-2xs whitespace-nowrap">
          <span className="text-slate-500">Model:</span>
          <span className="font-semibold text-slate-900">{selectedModel}</span>
          <ChevronDown className="w-3 h-3 text-slate-400" />
        </button>

        <div className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md whitespace-nowrap">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
          <span>Healthy</span>
        </div>
      </div>
    </header>
  );
}
