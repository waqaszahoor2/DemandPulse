'use client';

import React from 'react';
import { Activity } from 'lucide-react';
import { MonitoringRow } from '@/lib/api';
import { ResponsiveContainer, LineChart, Line } from 'recharts';

interface MonitoringPanelProps {
  data?: MonitoringRow[];
}

export default function MonitoringPanel({ data }: MonitoringPanelProps) {
  if (!data || !data.length) return null;

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
          <Activity className="w-4 h-4" />
        </div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight">Production Monitoring</h2>
      </div>

      {/* Rows */}
      <div className="space-y-3 flex-1 flex flex-col justify-around">
        {data.map((row) => {
          const isGreen = row.status === 'Green';
          const isYellow = row.status === 'Yellow';

          const dotColor = isGreen ? 'bg-emerald-500' : isYellow ? 'bg-amber-500' : 'bg-rose-500';
          const textColor = isGreen ? 'text-emerald-700 font-semibold' : isYellow ? 'text-amber-700 font-semibold' : 'text-rose-700 font-semibold';
          const strokeColor = isGreen ? '#10B981' : isYellow ? '#F59E0B' : '#EF4444';

          const sparkData = row.sparkline.map((val, idx) => ({ idx, val }));

          return (
            <div key={row.name} className="flex items-center justify-between py-1 border-b border-slate-50 last:border-0">
              <span className="text-xs font-semibold text-slate-700 w-1/3 truncate">{row.name}</span>

              <div className="flex items-center gap-1.5 w-1/3 justify-center text-xs">
                <span className={`h-2 w-2 rounded-full ${dotColor}`}></span>
                <span className={textColor}>{row.status}</span>
              </div>

              {/* Sparkline chart */}
              <div className="w-20 h-6 w-1/3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sparkData}>
                    <Line
                      type="monotone"
                      dataKey="val"
                      stroke={strokeColor}
                      strokeWidth={1.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
