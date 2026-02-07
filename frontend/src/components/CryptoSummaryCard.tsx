'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface Summary1h {
  timeframe: string;
  total: number;
  positives: number;
  negatives: number;
  positive_pct: number;
  negative_pct: number;
  top_5_abs: Array<{ symbol: string; change: number }>;
}

export function CryptoSummaryCard() {
  const [summary, setSummary] = useState<Summary1h | null>(null);
  const [loading, setLoading] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    let active = true;

    const fetchSummary = async () => {
      try {
        const data = await api.getCryptoBubblesSummary1h();
        if (active) {
          setSummary(data);
        }
      } catch (error) {
        if (active) {
          setSummary(null);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchSummary();
    const interval = setInterval(fetchSummary, 5 * 60 * 1000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-background-secondary p-5">
        <div className="text-xs text-foreground-muted">Carregando resumo...</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="rounded-xl border border-border bg-background-secondary p-5">
        <div className="text-xs text-foreground-muted">Resumo indisponivel</div>
      </div>
    );
  }

  const biasUp = summary.positive_pct >= summary.negative_pct;
  const biasEmoji = biasUp ? '🟢' : '🔴';
  const biasSignal = biasUp ? '+' : '-';
  const neutralPct = Math.max(0, 100 - summary.positive_pct - summary.negative_pct);

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-gradient-to-br from-[#0b111f] via-[#101a2b] to-[#0e1627] p-5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]">
      <div className="pointer-events-none absolute inset-0 opacity-40">
        <div className="absolute -top-24 -right-24 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgba(34,197,94,0.35),rgba(34,197,94,0))]" />
        <div className="absolute -bottom-28 -left-20 h-64 w-64 rounded-full bg-[radial-gradient(circle,rgba(14,116,144,0.35),rgba(14,116,144,0))]" />
      </div>

      {/* Header */}
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-[0.3em] text-foreground-muted">
              CryptoBubbles
            </span>
            <span className="text-[10px] rounded-full border border-border bg-background/40 px-2 py-0.5 text-foreground-muted">
              1H
            </span>
          </div>
          <div className="mt-2 text-lg font-semibold text-foreground">
            Resumo Cripto {biasEmoji} {biasSignal}
          </div>
          <div className="mt-1 text-xs text-foreground-muted">
            Atualiza a cada 15 minutos
          </div>
        </div>

        <div className="text-right">
          <div className="space-y-2">
            <div>
              <div
                className={`font-semibold ${biasUp ? 'text-long text-3xl' : 'text-foreground-muted text-xl'}`}
              >
                {summary.positive_pct.toFixed(1)}%
              </div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-foreground-muted">positivas</div>
            </div>
            <div>
              <div
                className={`font-semibold ${!biasUp ? 'text-short text-3xl' : 'text-foreground-muted text-xl'}`}
              >
                {summary.negative_pct.toFixed(1)}%
              </div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-foreground-muted">negativas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed((prev) => !prev)}
        className="relative mt-4 flex items-center gap-2 rounded-full border border-border bg-background/40 px-3 py-1 text-xs text-foreground-muted hover:bg-background/60"
      >
        {isCollapsed ? 'Expandir' : 'Recolher'}
        <svg
          className={`h-3 w-3 transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Collapsed View */}
      {isCollapsed && (
        <div className="relative mt-4 flex flex-wrap gap-2 text-[11px] text-foreground-muted">
          <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
            {summary.positive_pct.toFixed(1)}% positivas
          </span>
          <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
            {summary.negative_pct.toFixed(1)}% negativas
          </span>
          <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
            Analisadas: {summary.total}
          </span>
        </div>
      )}

      {/* Expanded View */}
      {!isCollapsed && (
        <>
          {/* Progress Bar */}
          <div className="relative mt-4">
            <div className="h-2 w-full overflow-hidden rounded-full bg-background/40 flex">
              <div
                className="h-full bg-long"
                style={{ width: `${summary.positive_pct.toFixed(1)}%` }}
              />
              <div
                className="h-full bg-short"
                style={{ width: `${summary.negative_pct.toFixed(1)}%` }}
              />
              {neutralPct > 0 && (
                <div
                  className="h-full bg-foreground-muted/60"
                  style={{ width: `${neutralPct.toFixed(1)}%` }}
                />
              )}
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-foreground-muted">
              <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
                {summary.positive_pct.toFixed(1)}% positivas
              </span>
              <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
                {summary.negative_pct.toFixed(1)}% negativas
              </span>
              {neutralPct > 0 && (
                <span className="rounded-full border border-border bg-background/40 px-2 py-0.5">
                  {neutralPct.toFixed(1)}% neutras
                </span>
              )}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="relative mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-border bg-background/40 p-4">
              <div className="text-xs uppercase tracking-[0.25em] text-foreground-muted">Analisadas</div>
              <div className="mt-3 text-4xl font-semibold text-foreground">{summary.total}</div>
              <div className="mt-2 text-base text-foreground-muted">
                Positivas: {summary.positives} | Negativas: {summary.negatives}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-background/40 p-3">
              <div className="text-[10px] uppercase tracking-[0.2em] text-foreground-muted">Top 5</div>
              <div className="mt-4 space-y-3 text-base">
                {summary.top_5_abs.map((item, idx) => {
                  const sign = item.change >= 0 ? '+' : '';
                  const color = item.change >= 0 ? 'text-long' : 'text-short';
                  return (
                    <div key={`${item.symbol}-${idx}`} className="flex items-center justify-between">
                      <span className="text-foreground">
                        <span className="mr-3 inline-flex h-7 w-7 items-center justify-center rounded-full bg-background-tertiary text-[12px] text-foreground-muted">
                          {idx + 1}
                        </span>
                        {item.symbol}
                      </span>
                      <span className={`${color} text-lg font-semibold`}>{sign}{item.change.toFixed(1)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
