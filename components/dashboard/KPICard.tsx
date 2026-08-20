'use client';

import React from 'react';
import { Target, Scale, ShieldCheck, AlertTriangle } from 'lucide-react';
import { KPICardData } from '@/lib/api';

interface KPICardsProps {
  data?: KPICardData;
}

export default function KPICards({ data }: KPICardsProps) {
  if (!data) return null;

  const cards = [
    {
      title: 'Forecast Accuracy',
      value: data.forecastAccuracy.value,
      subtext: data.forecastAccuracy.subtext,
      icon: Target,
      iconBg: 'bg-blue-100/70 text-blue-600 border border-blue-200/50',
      valueColor: 'text-slate-900',
      subtextColor: 'text-emerald-600 font-medium',
    },
    {
      title: 'Forecast Bias',
      value: data.forecastBias.value,
      subtext: data.forecastBias.subtext,
      icon: Scale,
      iconBg: 'bg-emerald-100/70 text-emerald-600 border border-emerald-200/50',
      valueColor: 'text-slate-900',
      subtextColor: 'text-emerald-600 font-medium',
    },
    {
      title: 'Service Level',
      value: data.serviceLevel.value,
      subtext: data.serviceLevel.subtext,
      icon: ShieldCheck,
      iconBg: 'bg-purple-100/70 text-purple-600 border border-purple-200/50',
      valueColor: 'text-slate-900',
      subtextColor: 'text-purple-600 font-medium',
    },
    {
      title: 'Stockout Risk',
      value: data.stockoutRisk.value,
      subtext: data.stockoutRisk.subtext,
      icon: AlertTriangle,
      iconBg: 'bg-orange-100/70 text-orange-600 border border-orange-200/50',
      valueColor: 'text-slate-900',
      subtextColor: 'text-emerald-600 font-medium',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white rounded-xl p-4 md:p-5 border border-slate-200/80 shadow-2xs hover:shadow-xs transition-shadow duration-150 flex items-start gap-3 md:gap-4"
          >
            <div className={`p-2.5 md:p-3 rounded-full shrink-0 ${card.iconBg}`}>
              <Icon className="w-5 h-5 md:w-6 md:h-6 stroke-[2]" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                {card.title}
              </span>
              <div className={`text-xl md:text-2xl font-bold tracking-tight ${card.valueColor}`}>
                {card.value}
              </div>
              <div className={`text-xs mt-1 truncate ${card.subtextColor}`}>
                {card.subtext}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
