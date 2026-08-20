'use client';

import React from 'react';
import MonitoringPanel from '@/components/dashboard/MonitoringPanel';
import { DEFAULT_DASHBOARD_DATA } from '@/lib/api';
import { Activity, ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-600" />
          <h1 className="text-xl font-bold text-slate-900">Production MLOps & Observability</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Real-time Population Stability Index (PSI), Kolmogorov-Smirnov (KS) feature drift detection, and automated retraining policies.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <MonitoringPanel data={DEFAULT_DASHBOARD_DATA.monitoring} />
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-3">Feature Drift Metrics (PSI & KS Test)</h2>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <span className="font-bold text-slate-800 block">lag_7_sales (Population Stability Index)</span>
                  <span className="text-[10px] text-slate-500">Threshold: PSI &lt; 0.10</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-emerald-600 text-sm">PSI = 0.021</span>
                  <span className="text-[10px] text-emerald-600 block">No Drift</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <div>
                  <span className="font-bold text-slate-800 block">promo_discount_percent (KS Test)</span>
                  <span className="text-[10px] text-slate-500">p-value threshold &gt; 0.05</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-emerald-600 text-sm">p = 0.420</span>
                  <span className="text-[10px] text-emerald-600 block font-medium">Distribution Matches</span>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-100 rounded-lg">
                <div>
                  <span className="font-bold text-amber-900 block">rolling_mean_14_sales (Calibration)</span>
                  <span className="text-[10px] text-amber-700">Interval coverage variance check</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-amber-700 text-sm">Coverage = 78.0%</span>
                  <span className="text-[10px] text-amber-700 block font-semibold">Slight Undercoverage</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-2">Automated Retraining Trigger Policy</h2>
            <p className="text-xs text-slate-500 mb-3">
              Trigger criteria evaluate every 24 hours at 00:00 UTC.
            </p>
            <div className="flex items-center justify-between text-xs p-3 bg-slate-50 rounded-lg">
              <span className="font-semibold text-slate-700">Next Scheduled Evaluation</span>
              <span className="font-bold text-blue-600">Tonight at 00:00 UTC</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
