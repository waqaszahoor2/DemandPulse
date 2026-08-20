'use client';

import React from 'react';
import { Settings, Server, Key, Database, Bell } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-slate-700" />
          <h1 className="text-xl font-bold text-slate-900">Platform Settings & Environment Config</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Configure API connections, MLflow tracking URI, retraining policies, and notification webhooks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          {/* API Config */}
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Server className="w-4 h-4 text-blue-600" /> Backend API Endpoint
            </h2>
            <div className="space-y-2 text-xs">
              <label className="font-semibold text-slate-700 block">FastAPI Base URL (NEXT_PUBLIC_API_URL)</label>
              <input
                type="text"
                readOnly
                value={process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000 (Development Auto-rewrite)'}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 outline-none"
              />
              <p className="text-[11px] text-slate-400">
                Routes to FastAPI serverless handler on Vercel deployment.
              </p>
            </div>
          </div>

          {/* MLflow Config */}
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Database className="w-4 h-4 text-purple-600" /> MLflow Tracking & Artifact Registry
            </h2>
            <div className="space-y-2 text-xs">
              <label className="font-semibold text-slate-700 block">MLflow Tracking Server URI</label>
              <input
                type="text"
                readOnly
                value="http://mlflow.demandpulse.internal:5000"
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-slate-800 outline-none"
              />
            </div>
          </div>
        </div>

        {/* Right Sidebar info */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
            <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-500" /> Alerts & Webhooks
            </h2>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-700 font-semibold">Slack Drift Channel</span>
                <span className="text-emerald-600 font-bold">Enabled</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-700 font-semibold">PagerDuty Urgent Escalation</span>
                <span className="text-emerald-600 font-bold">Enabled</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-slate-700 font-semibold">Email Audit Digests</span>
                <span className="text-slate-400 font-medium">Daily</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
