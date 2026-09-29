import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import KPICards from '@/components/dashboard/KPICard';
import InventoryCard from '@/components/dashboard/InventoryCard';
import PromotionImpact from '@/components/dashboard/PromotionImpact';
import ProbabilisticForecast from '@/components/dashboard/ProbabilisticForecast';
import ModelPerformance from '@/components/dashboard/ModelPerformance';
import MonitoringPanel from '@/components/dashboard/MonitoringPanel';
import Sidebar from '@/components/layout/Sidebar';
import MobileHeader from '@/components/layout/MobileHeader';
import Header from '@/components/layout/Header';
import ForecastChart from '@/components/dashboard/ForecastChart';
import MobileBottomNav from '@/components/layout/MobileBottomNav';
import { DEFAULT_DASHBOARD_DATA } from '@/lib/api';

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

// Mock Recharts components cleanly for Vitest/jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="barchart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="xaxis" />,
  YAxis: () => <div data-testid="yaxis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ComposedChart: ({ children }: any) => <div data-testid="composed-chart">{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  Area: () => <div data-testid="area" />,
  ReferenceLine: () => <div data-testid="reference-line" />,
  CartesianGrid: () => <div data-testid="cartesiangrid" />,
  Cell: () => <div data-testid="cell" />,
}));

describe('DemandPulse Frontend UI Components', () => {
  it('renders KPICards with valid WAPE, Bias, Service Level, and Stockout Risk', () => {
    render(<KPICards data={DEFAULT_DASHBOARD_DATA.kpis} />);
    expect(screen.getByText(/Forecast Accuracy/i)).toBeInTheDocument();
    expect(screen.getByText(/WAPE 8.7%/i)).toBeInTheDocument();
    expect(screen.getByText(/-1.6%/i)).toBeInTheDocument();
    expect(screen.getByText(/96.2%/i)).toBeInTheDocument();
    expect(screen.getByText(/4.8%/i)).toBeInTheDocument();
  });

  it('renders InventoryCard with recommended order and stockout risk', () => {
    render(<InventoryCard data={DEFAULT_DASHBOARD_DATA.inventory} />);
    expect(screen.getByText(/Inventory Recommendation/i)).toBeInTheDocument();
    expect(screen.getAllByText('420')[0]).toBeInTheDocument();
    expect(screen.getAllByText('510')[0]).toBeInTheDocument();
    expect(screen.getAllByText('175')[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Low/i)[0]).toBeInTheDocument();
  });

  it('renders PromotionImpact with estimated uplift and confidence interval', () => {
    render(<PromotionImpact data={DEFAULT_DASHBOARD_DATA.promotion} />);
    expect(screen.getByText(/Promotion Impact/i)).toBeInTheDocument();
    expect(screen.getByText(/\+8.4%/i)).toBeInTheDocument();
    expect(screen.getByText(/-5.2%/i)).toBeInTheDocument();
    expect(screen.getByText(/\+11.6%/i)).toBeInTheDocument();
    expect(screen.getByText(/Treatment Effect by Category/i)).toBeInTheDocument();
  });

  it('renders ProbabilisticForecast with P10, P50, and P90 quantile cards', () => {
    render(<ProbabilisticForecast data={DEFAULT_DASHBOARD_DATA.probabilistic} />);
    expect(screen.getByText(/Probabilistic Forecast/i)).toBeInTheDocument();
    expect(screen.getByText(/P10 - Low Demand/i)).toBeInTheDocument();
    expect(screen.getByText(/320 Units/i)).toBeInTheDocument();
    expect(screen.getByText(/P50 - Expected Demand/i)).toBeInTheDocument();
    expect(screen.getByText(/510 Units/i)).toBeInTheDocument();
    expect(screen.getByText(/P90 - High Demand/i)).toBeInTheDocument();
    expect(screen.getByText(/710 Units/i)).toBeInTheDocument();
  });

  it('renders ModelPerformance with Seasonal Naive, LightGBM, and Quantile Model rows', () => {
    render(<ModelPerformance data={DEFAULT_DASHBOARD_DATA.models} />);
    expect(screen.getByText(/Model Performance/i)).toBeInTheDocument();
    expect(screen.getByText(/LightGBM/i)).toBeInTheDocument();
    expect(screen.getByText(/Champion/i)).toBeInTheDocument();
    expect(screen.getByText(/Seasonal Naive/i)).toBeInTheDocument();
  });

  it('renders MonitoringPanel with status indicators', () => {
    render(<MonitoringPanel data={DEFAULT_DASHBOARD_DATA.monitoring} />);
    expect(screen.getByText(/Production Monitoring/i)).toBeInTheDocument();
    expect(screen.getByText(/Data Quality/i)).toBeInTheDocument();
    expect(screen.getByText(/Feature Drift/i)).toBeInTheDocument();
    expect(screen.getByText(/Calibration/i)).toBeInTheDocument();
  });

  it('renders Sidebar with DemandPulse logo and overview link', () => {
    render(<Sidebar currentPath="/" />);
    expect(screen.getByText('DemandPulse')).toBeInTheDocument();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('System Status')).toBeInTheDocument();
  });

  it('renders MobileHeader with brand title', () => {
    render(<MobileHeader onOpenMenu={() => {}} />);
    expect(screen.getByText('/DemandPulse')).toBeInTheDocument();
  });

  it('renders Header with title and controls', () => {
    render(<Header />);
    expect(screen.getAllByText(/DemandPulse/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Retail Demand Intelligence Platform/i)).toBeInTheDocument();
  });

  it('renders ForecastChart with container and controls', () => {
    render(<ForecastChart data={DEFAULT_DASHBOARD_DATA.forecast} />);
    expect(screen.getByText(/Demand Forecast & Uncertainty/i)).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  it('renders MobileBottomNav with navigation bar', () => {
    render(<MobileBottomNav menuOpen={false} setMenuOpen={() => {}} />);
    expect(screen.getByText(/Overview/i)).toBeInTheDocument();
    expect(screen.getByText(/Forecasting/i)).toBeInTheDocument();
  });

  it('provides default dashboard fallback data with valid elements', () => {
    expect(DEFAULT_DASHBOARD_DATA.forecast.length).toBeGreaterThan(0);
    expect(DEFAULT_DASHBOARD_DATA.inventory.currentStock).toBe(420);
  });
});
