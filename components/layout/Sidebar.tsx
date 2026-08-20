'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  LineChart,
  BarChart3,
  TrendingUp,
  Package,
  GitMerge,
  Activity,
  Sliders,
  Settings,
  Radio,
} from 'lucide-react';

interface SidebarProps {
  currentPath?: string;
}

export const navItems = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Forecasting', href: '/forecasting', icon: LineChart },
  { name: 'Probabilistic Forecasts', href: '/probabilistic', icon: BarChart3 },
  { name: 'Promotion Impact', href: '/promotion-impact', icon: TrendingUp },
  { name: 'Inventory Intelligence', href: '/inventory', icon: Package },
  { name: 'Hierarchical Analysis', href: '/hierarchical', icon: GitMerge },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Model Performance', href: '/models', icon: Sliders },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar({ currentPath }: SidebarProps) {
  const pathname = usePathname() || currentPath || '/';

  return (
    <aside className="hidden lg:flex flex-col fixed inset-y-0 left-0 w-60 xl:w-64 bg-[#0B192C] text-slate-300 z-30 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-slate-800/80">
        <div className="w-8 h-8 rounded-lg bg-[#1D5EFF] flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <Activity className="w-5 h-5 stroke-[2.5]" />
        </div>
        <span className="font-bold text-lg text-white tracking-tight">DemandPulse</span>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-[#1D5EFF] text-white shadow-sm font-semibold'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span className="truncate">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom System Status Widget */}
      <div className="p-3 m-3 rounded-xl bg-[#071322] border border-slate-800/80">
        <div className="flex items-center gap-2 mb-1">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-semibold text-white">System Status</span>
        </div>
        <div className="text-xs text-emerald-400 font-medium ml-4">Healthy</div>
        <div className="text-[11px] text-slate-400 ml-4 mt-0.5">All systems operational</div>
      </div>
    </aside>
  );
}
