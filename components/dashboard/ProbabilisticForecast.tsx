'use client';

import React from 'react';
import { ProbabilisticCardData } from '@/lib/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip } from 'recharts';

interface ProbabilisticForecastProps {
  data?: ProbabilisticCardData[];
}

export default function ProbabilisticForecast({ data }: ProbabilisticForecastProps) {
  if (!data || !data.length) return null;

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      {/* Title */}
      <div className="mb-3">
        <h2 className="text-base font-bold text-slate-900 tracking-tight">
          Probabilistic Forecast (Next 7 Days)
        </h2>
        <p className="text-xs text-slate-500">Conformal quantile predictions with exact coverage bounds</p>
      </div>

      {/* 3 Side-by-Side Quantile Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {data.map((item) => {
          const isBlue = item.colorTheme === 'blue';
          const isTeal = item.colorTheme === 'teal';

          const textColor = isBlue
            ? 'text-blue-600'
            : isTeal
            ? 'text-teal-600'
            : 'text-purple-600';

          const barColor = isBlue
            ? '#1D5EFF'
            : isTeal
            ? '#12B8A6'
            : '#8057E8';

          const bgColor = isBlue
            ? 'bg-blue-50/60 border-blue-100'
            : isTeal
            ? 'bg-teal-50/60 border-teal-100'
            : 'bg-purple-50/60 border-purple-100';

          return (
            <div key={item.quantile} className={`p-3 rounded-lg border ${bgColor} flex flex-col justify-between`}>
              <div>
                <span className="text-[11px] font-semibold text-slate-600 uppercase block mb-1">
                  {item.title}
                </span>
                <div className={`text-xl font-bold tracking-tight ${textColor}`}>
                  {item.subtitle}
                </div>
              </div>

              {/* 7-Day Mini Bar Chart */}
              <div className="w-full h-16 mt-3">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={item.dailyValues} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
                    <XAxis
                      dataKey="day"
                      tick={{ fontSize: 9, fill: '#64748B' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      formatter={(val: number) => [`${val} Units`, item.quantile]}
                      contentStyle={{ fontSize: 10, padding: '4px 8px' }}
                    />
                    <Bar dataKey="value" fill={barColor} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
