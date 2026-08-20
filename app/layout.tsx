'use client';

import React, { useState } from 'react';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import MobileHeader from '@/components/layout/MobileHeader';
import MobileBottomNav from '@/components/layout/MobileBottomNav';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedDateRange, setSelectedDateRange] = useState('May 12 – May 18, 2025');
  const [selectedModel, setSelectedModel] = useState('Champion v1');

  return (
    <html lang="en">
      <head>
        <title>DemandPulse — Retail Demand Intelligence Platform</title>
        <meta name="description" content="Production-Grade Retail Demand Intelligence, Conformal Prediction, Causal Promotion Impact, and Cost-Optimal Inventory Optimization" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="bg-[#F7F9FC] text-slate-900 min-h-screen flex flex-col antialiased">
        {/* Fixed Desktop Sidebar */}
        <Sidebar />

        {/* Mobile Slide-over Drawer & Fixed Bottom Bar */}
        <MobileBottomNav menuOpen={mobileMenuOpen} setMenuOpen={setMobileMenuOpen} />

        {/* Main Application Container */}
        <div className="flex-1 flex flex-col lg:pl-60 xl:pl-64 min-w-0 transition-all duration-200">
          {/* Top Desktop Header */}
          <Header
            selectedDateRange={selectedDateRange}
            onDateRangeChange={setSelectedDateRange}
            selectedModel={selectedModel}
            onModelChange={setSelectedModel}
          />

          {/* Top Mobile Header */}
          <MobileHeader
            onOpenMenu={() => setMobileMenuOpen(true)}
            selectedDateRange={selectedDateRange}
            selectedModel={selectedModel}
          />

          {/* Main Content Area */}
          <main className="flex-1 p-4 md:p-6 pb-24 lg:pb-8 max-w-[1600px] w-full mx-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
