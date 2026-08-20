'use client';

import React from 'react';
import ForecastChart from '@/components/dashboard/ForecastChart';
import { DEFAULT_DASHBOARD_DATA } from '@/lib/api';
import { LineChart, Filter, Download, ArrowUpRight } from 'lucide-react';

export default function ForecastingPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div>
          <div className="flex items-center gap-2">
            <LineChart className="w-5 h-5 text-[#1D5EFF]" />
            <h1 className="text-xl font-bold text-slate-900">Demand Forecasting Intelligence</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Global LightGBM cross-series point & rolling-origin backtested predictions across SKU hierarchies.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold">
          <button className="flex items-center gap-1.5 px-3 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg transition-colors">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter Series</span>
          </button>
          <button className="flex items-center gap-1.5 px-3 py-2 bg-[#1D5EFF] text-white hover:bg-blue-700 rounded-lg shadow-2xs transition-colors">
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Main Forecast Chart */}
      <div className="min-h-[420px]">
        <ForecastChart data={DEFAULT_DASHBOARD_DATA.forecast} />
      </div>

      {/* Cross-Series Breakdown Table */}
      <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-2xs">
        <h2 className="text-base font-bold text-slate-900 mb-3">Top SKU Series Forecasts</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-2.5">SKU ID</th>
                <th className="py-2.5">Product Name</th>
                <th className="py-2.5">Store</th>
                <th className="py-2.5 text-right">P50 Forecast</th>
                <th className="py-2.5 text-right">P10 Bound</th>
                <th className="py-2.5 text-right">P90 Bound</th>
                <th className="py-2.5 text-center">Trend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {[
                { id: 'SKU-1092', name: 'Fresh Organic Milk 1L', store: 'Boston Central (#101)', p50: 510, p10: 320, p90: 710, trend: '+4.2%' },
                { id: 'SKU-3041', name: 'Sparkling Citrus Water 500ml', store: 'NY Mid-town (#104)', p50: 840, p10: 620, p90: 1120, trend: '+12.1%' },
                { id: 'SKU-8820', name: 'Artisanal Whole Wheat Bread', store: 'Boston Central (#101)', p50: 290, p10: 210, p90: 410, trend: '-1.5%' },
                { id: 'SKU-4912', name: 'Greek Yogurt Vanilla 500g', store: 'Seattle Downtown (#108)', p50: 670, p10: 490, p90: 890, trend: '+8.7%' },
              ].map((row) => (
                <tr key={row.id} className="hover:bg-slate-50">
                  <td className="py-3 font-bold text-slate-800">{row.id}</td>
                  <td className="py-3 text-slate-900">{row.name}</td>
                  <td className="py-3 text-slate-500">{row.store}</td>
                  <td className="py-3 text-right font-bold text-teal-600">{row.p50} units</td>
                  <td className="py-3 text-right text-blue-600">{row.p10} units</td>
                  <td className="py-3 text-right text-purple-600">{row.p90} units</td>
                  <td className="py-3 text-center">
                    <span className="inline-flex items-center text-emerald-600 font-bold">
                      {row.trend} <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
