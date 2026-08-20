'use client';

import React from 'react';
import { GitMerge, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function HierarchicalPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
        <div className="flex items-center gap-2">
          <GitMerge className="w-5 h-5 text-teal-600" />
          <h1 className="text-xl font-bold text-slate-900">MinT Hierarchical Forecast Reconciliation</h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Minimum Trace shrinkage matrix projection enforcing 100% accounting coherence across Enterprise, Region, City, Store, Category, and SKU.
        </p>
      </div>

      {/* Reconciliation Performance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
          <span className="text-xs font-semibold text-slate-500 block">Unreconciled Coherence Error</span>
          <div className="text-2xl font-bold text-rose-600 mt-1">14.82 units</div>
          <p className="text-xs text-rose-600 font-semibold mt-1 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Direct sum mismatch
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
          <span className="text-xs font-semibold text-slate-500 block">MinT Reconciled Coherence Error</span>
          <div className="text-2xl font-bold text-emerald-600 mt-1">0.00 units</div>
          <p className="text-xs text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% Accounting Coherence
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-2xs">
          <span className="text-xs font-semibold text-slate-500 block">Variance Reduction</span>
          <div className="text-2xl font-bold text-teal-600 mt-1">18.4%</div>
          <p className="text-xs text-slate-500 mt-1">Information sharing across aggregate nodes</p>
        </div>
      </div>

      {/* Tree Hierarchy Breakdown Table */}
      <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-2xs">
        <h2 className="text-base font-bold text-slate-900 mb-3">Hierarchical Structure & Aggregation Nodes</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="py-2.5">Hierarchy Level</th>
                <th className="py-2.5">Node Name</th>
                <th className="py-2.5 text-right">Bottom-Up Raw</th>
                <th className="py-2.5 text-right">MinT Reconciled</th>
                <th className="py-2.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {[
                { level: 'Level 0 (Total)', node: 'Enterprise Retail Total', raw: '28,450', reconciled: '28,450', status: 'Coherent' },
                { level: 'Level 1 (Region)', node: 'Northeast Region', raw: '12,120', reconciled: '12,120', status: 'Coherent' },
                { level: 'Level 2 (Store)', node: 'Boston Central Store #101', raw: '4,850', reconciled: '4,850', status: 'Coherent' },
                { level: 'Level 3 (Category)', node: 'Beverages & Dairy', raw: '2,180', reconciled: '2,180', status: 'Coherent' },
                { level: 'Level 4 (SKU)', node: 'Fresh Organic Milk 1L', raw: '510', reconciled: '510', status: 'Coherent' },
              ].map((row) => (
                <tr key={row.node} className="hover:bg-slate-50">
                  <td className="py-3 font-semibold text-slate-500">{row.level}</td>
                  <td className="py-3 font-bold text-slate-800">{row.node}</td>
                  <td className="py-3 text-right text-slate-600">{row.raw}</td>
                  <td className="py-3 text-right font-bold text-teal-600">{row.reconciled}</td>
                  <td className="py-3 text-center">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      {row.status}
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
