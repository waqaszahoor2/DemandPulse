'use client';

import React from 'react';
import { Tag } from 'lucide-react';
import { PromotionImpactData } from '@/lib/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

interface PromotionImpactProps {
  data?: PromotionImpactData;
}

export default function PromotionImpact({ data }: PromotionImpactProps) {
  if (!data) return null;

  return (
    <div className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between h-full">
      {/* Card Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="p-1.5 rounded-lg bg-purple-50 text-purple-600">
          <Tag className="w-4 h-4" />
        </div>
        <h2 className="text-base font-bold text-slate-900 tracking-tight">Promotion Impact</h2>
      </div>

      {/* Main Causal Metric */}
      <div className="mb-3">
        <span className="text-xs font-medium text-slate-500 block">Estimated Uplift</span>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl md:text-3xl font-extrabold text-purple-600 tracking-tight">
            {data.estimatedUplift}
          </span>
          <span className="text-xs text-slate-500 font-medium">{data.causalEstimateText}</span>
        </div>
      </div>

      {/* Confidence Interval Visualizer */}
      <div className="bg-slate-50 rounded-lg p-2.5 border border-slate-100 mb-4">
        <div className="flex items-center justify-between text-[11px] font-semibold text-slate-500 mb-1.5">
          <span>{data.confidenceInterval.label}</span>
        </div>
        <div className="flex items-center justify-between text-xs font-bold text-slate-700">
          <span>{data.confidenceInterval.low}</span>
          <div className="flex-1 mx-3 relative flex items-center">
            <div className="h-1 w-full bg-purple-200 rounded-full"></div>
            <div className="absolute left-1/4 right-1/4 h-2 bg-purple-600 rounded-full"></div>
            <div className="absolute left-1/2 -ml-1.5 w-3 h-3 bg-purple-700 rounded-full border-2 border-white shadow-xs"></div>
          </div>
          <span>{data.confidenceInterval.high}</span>
        </div>
      </div>

      {/* Treatment Effect by Category Chart */}
      <div className="flex-1 min-h-[140px]">
        <span className="text-xs font-bold text-slate-800 block mb-2">Treatment Effect by Category</span>
        <div className="w-full h-32">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.categoryUplifts} margin={{ top: 5, right: 5, left: -20, bottom: 20 }}>
              <XAxis
                dataKey="category"
                tick={{ fontSize: 9, fill: '#64748B' }}
                interval={0}
                axisLine={{ stroke: '#CBD5E1' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 9, fill: '#64748B' }}
                tickFormatter={(val) => `${val}%`}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(val: number) => [`+${val}% Uplift`, 'Category Effect']}
                contentStyle={{ fontSize: 11, borderRadius: 8 }}
              />
              <Bar dataKey="upliftPercent" radius={[4, 4, 0, 0]}>
                {data.categoryUplifts.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      index === 0
                        ? '#8057E8'
                        : index === 1
                        ? '#936DED'
                        : index === 2
                        ? '#A683F2'
                        : index === 3
                        ? '#B999F7'
                        : '#CDAFFC'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
