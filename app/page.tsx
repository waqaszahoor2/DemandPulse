'use client';

import React, { useEffect, useState } from 'react';
import KPICards from '@/components/dashboard/KPICard';
import ForecastChart from '@/components/dashboard/ForecastChart';
import InventoryCard from '@/components/dashboard/InventoryCard';
import PromotionImpact from '@/components/dashboard/PromotionImpact';
import ProbabilisticForecast from '@/components/dashboard/ProbabilisticForecast';
import ModelPerformance from '@/components/dashboard/ModelPerformance';
import MonitoringPanel from '@/components/dashboard/MonitoringPanel';
import { fetchDashboardData, DashboardData, DEFAULT_DASHBOARD_DATA } from '@/lib/api';
import { RefreshCw, AlertCircle } from 'lucide-react';

export default function OverviewDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboardData();
      setData(res);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      // Fallback to rich reference dataset smoothly
      setData(DEFAULT_DASHBOARD_DATA);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading && !data) {
    return (
      <div className="space-y-4 md:space-y-6 animate-pulse">
        {/* KPI Skeleton */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-slate-200/80 rounded-xl"></div>
          ))}
        </div>
        {/* Main Grid Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-8 h-96 bg-slate-200/80 rounded-xl"></div>
          <div className="lg:col-span-4 space-y-4">
            <div className="h-44 bg-slate-200/80 rounded-xl"></div>
            <div className="h-48 bg-slate-200/80 rounded-xl"></div>
          </div>
        </div>
        {/* Bottom Row Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-slate-200/80 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const currentData = data || DEFAULT_DASHBOARD_DATA;

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Error Alert (If API fails) */}
      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Unable to reach live prediction API. Displaying reference cached metrics.</span>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-1 font-semibold text-amber-900 hover:underline"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* 1. KPI Cards Row */}
      <section aria-label="Key Metrics Overview">
        <KPICards data={currentData.kpis} />
      </section>

      {/* 2. Main Middle Section: Forecast Chart + Inventory & Promotion Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 md:gap-6 items-stretch">
        {/* Left Column: Demand Forecast & Uncertainty Chart */}
        <section aria-label="Demand Forecast Chart" className="lg:col-span-8">
          <ForecastChart data={currentData.forecast} />
        </section>

        {/* Right Column: Inventory Recommendation & Promotion Impact Stack */}
        <div className="lg:col-span-4 flex flex-col gap-4 md:gap-6">
          <section aria-label="Inventory Recommendation" className="flex-1">
            <InventoryCard data={currentData.inventory} />
          </section>
          <section aria-label="Promotion Impact Analysis" className="flex-1">
            <PromotionImpact data={currentData.promotion} />
          </section>
        </div>
      </div>

      {/* 3. Bottom Row: Probabilistic Forecast + Model Performance + Monitoring */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 items-stretch">
        <section aria-label="Probabilistic Forecasts" className="md:col-span-2 lg:col-span-1">
          <ProbabilisticForecast data={currentData.probabilistic} />
        </section>
        <section aria-label="Model Performance Benchmarks">
          <ModelPerformance data={currentData.models} />
        </section>
        <section aria-label="Production Health Monitoring">
          <MonitoringPanel data={currentData.monitoring} />
        </section>
      </div>
    </div>
  );
}
