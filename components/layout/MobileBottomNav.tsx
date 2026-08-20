'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  LineChart,
  Bell,
  Menu as MenuIcon,
  X,
  BarChart3,
  TrendingUp,
  Package,
  GitMerge,
  Activity,
  Sliders,
  Settings,
} from 'lucide-react';
import { navItems } from './Sidebar';

interface MobileBottomNavProps {
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
}

export default function MobileBottomNav({ menuOpen, setMenuOpen }: MobileBottomNavProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Slide-over Drawer for Mobile Menu */}
      {menuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
            onClick={() => setMenuOpen(false)}
          />

          {/* Drawer Content */}
          <div className="relative flex-1 w-full max-w-xs bg-[#0B192C] text-slate-300 p-5 flex flex-col justify-between shadow-2xl z-50">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-[#1D5EFF] flex items-center justify-center text-white">
                    <Activity className="w-4 h-4" />
                  </div>
                  <span className="font-bold text-white text-lg">DemandPulse</span>
                </div>
                <button
                  onClick={() => setMenuOpen(false)}
                  className="p-1 text-slate-400 hover:text-white rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mt-4 space-y-1">
                {navItems.map((item) => {
                  const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setMenuOpen(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-[#1D5EFF] text-white font-semibold'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Bottom Status Card */}
            <div className="p-3 rounded-xl bg-[#071322] border border-slate-800 text-xs">
              <div className="flex items-center gap-2 font-semibold text-white">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span>System Operational</span>
              </div>
              <p className="text-slate-400 mt-1">Version 1.4.0 (Champion v1)</p>
            </div>
          </div>
        </div>
      )}

      {/* Fixed Bottom Navigation Bar */}
      <nav aria-label="Mobile Navigation" className="lg:hidden fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 z-40 px-3 py-2 shadow-lg pb-safe">
        <div className="grid grid-cols-4 gap-1 text-center">
          <Link
            href="/"
            className={`flex flex-col items-center py-1 rounded-lg text-xs font-medium ${
              pathname === '/' ? 'text-[#1D5EFF]' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="w-5 h-5 mb-0.5" />
            <span>Overview</span>
          </Link>

          <Link
            href="/forecasting"
            className={`flex flex-col items-center py-1 rounded-lg text-xs font-medium ${
              pathname === '/forecasting' ? 'text-[#1D5EFF]' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <LineChart className="w-5 h-5 mb-0.5" />
            <span>Forecasting</span>
          </Link>

          <Link
            href="/monitoring"
            className={`flex flex-col items-center py-1 rounded-lg text-xs font-medium ${
              pathname === '/monitoring' ? 'text-[#1D5EFF]' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <Bell className="w-5 h-5 mb-0.5" />
            <span>Alerts</span>
          </Link>

          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className={`flex flex-col items-center py-1 rounded-lg text-xs font-medium ${
              menuOpen ? 'text-[#1D5EFF]' : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            <MenuIcon className="w-5 h-5 mb-0.5" />
            <span>Menu</span>
          </button>
        </div>
      </nav>
    </>
  );
}
