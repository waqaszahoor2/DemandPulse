'use client';

import React from 'react';
import Link from 'next/link';
import { Sliders, ArrowRight } from 'lucide-react';
import { ModelPerformanceRow } from '@/lib/api';

interface ModelPerformanceProps {
  data?: ModelPerformanceRow[];
}

export default function ModelPerformance({ data }: ModelPerformanceProps) {
  if (!data || !data.length) return null;

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      <div>
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
            <Sliders className="w-4 h-4" />
          </div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">Model Performance</h2>
        </div>

        {/* Performance Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase tracking-wider">
                <th className="pb-2 font-medium">Model</th>
                <th className="pb-2 font-medium text-right">WAPE</th>
                <th className="pb-2 font-medium text-right">Bias</th>
                <th className="pb-2 font-medium text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50 font-medium">
              {data.map((row) => {
                const isChampion = row.status === 'Champion';
                const isActive = row.status === 'Active';

                const statusBadge = isChampion
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-200 font-bold'
                  : isActive
                  ? 'bg-blue-100 text-blue-800 border-blue-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200';

                return (
                  <tr key={row.model} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-2.5 font-bold text-slate-800">{row.model}</td>
                    <td className="py-2.5 text-right font-semibold text-slate-900">{row.wape}</td>
                    <td className="py-2.5 text-right text-slate-600">{row.bias}</td>
                    <td className="py-2.5 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] border ${statusBadge}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer link */}
      <div className="pt-3 mt-3 border-t border-slate-100">
        <Link
          href="/models"
          className="text-xs font-semibold text-[#1D5EFF] hover:text-blue-700 inline-flex items-center gap-1 group"
        >
          <span>View all models</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  );
}
