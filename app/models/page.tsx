'use client';

import React from 'react';
import ModelPerformance from '@/components/dashboard/ModelPerformance';
import { DEFAULT_DASHBOARD_DATA } from '@/lib/api';
import { Sliders, Cpu, GitCommit, CheckCircle2 } from 'lucide-react';

export default function ModelsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-[#1D5EFF]" />
          <h1 className="text-xl font-bold text-slate-900">MLflow Model Registry & Champion Promotion</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Automated evaluation gates comparing dry-run candidate artifacts against active production champion.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <ModelPerformance data={DEFAULT_DASHBOARD_DATA.models} />
        </div>

        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-3">MLflow Champion Promotion Gates</h2>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-100 rounded-lg">
                <span className="font-semibold text-emerald-900">WAPE Improvement &gt; 2%</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Passed (+5.5%)
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-100 rounded-lg">
                <span className="font-semibold text-emerald-900">Coverage Nominal Tolerance (&plusmn;3%)</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Passed (80.4%)
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-emerald-50 border border-emerald-100 rounded-lg">
                <span className="font-semibold text-emerald-900">Latency P99 &lt; 10ms</span>
                <span className="font-bold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Passed (4.2ms)
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-2">Active Artifact Metadata</h2>
            <div className="text-xs space-y-1.5 text-slate-600 font-mono">
              <p><span className="text-slate-400">Run ID:</span> 84f901c2a7e44b998</p>
              <p><span className="text-slate-400">Framework:</span> LightGBM 4.3.0</p>
              <p><span className="text-slate-400">Parameters:</span> num_leaves=31, lr=0.05, n_est=500</p>
              <p><span className="text-slate-400">Registry Stage:</span> Production / Champion</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
