'use client';

import { Signal } from '@/lib/store';

interface SignalCardProps {
  signal: Signal;
}

// Mapeamento de estratégia para tipo de operação e label
const STRATEGY_INFO: Record<string, { type: string; label: string; color: string }> = {
  'GCM': { type: 'INDICADOR', label: 'GCM', color: 'bg-purple-500/20 text-purple-400' },
  'RSI': { type: 'INDICADOR', label: 'RSI', color: 'bg-blue-500/20 text-blue-400' },
  'MACD': { type: 'INDICADOR', label: 'MACD', color: 'bg-cyan-500/20 text-cyan-400' },
  'RSI_EMA50': { type: 'INDICADOR', label: 'RSI + EMA50', color: 'bg-indigo-500/20 text-indigo-400' },
  'SCALPING': { type: 'SCALPING', label: 'Scalping', color: 'bg-yellow-500/20 text-yellow-400' },
  'SWING_TRADE': { type: 'SWING TRADE', label: 'Swing Trade', color: 'bg-emerald-500/20 text-emerald-400' },
  'DAY_TRADE': { type: 'DAY TRADE', label: 'Day Trade', color: 'bg-orange-500/20 text-orange-400' },
};

export function SignalCard({ signal }: SignalCardProps) {
  const isLong = signal.direction === 'LONG';
  const signalDate = new Date(signal.timestamp);
  
  // Formatar hora - o timestamp já vem em horário de São Paulo do backend
  const time = signalDate.toLocaleTimeString('pt-BR', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
  const date = signalDate.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit'
  });
  const stratInfo = STRATEGY_INFO[signal.strategy] || { 
    type: 'INDICADOR', 
    label: signal.strategy, 
    color: 'bg-gray-500/20 text-gray-400' 
  };
  
  return (
    <div className={`
      signal-enter p-4 rounded-lg border
      ${isLong 
        ? 'border-long/30 bg-long/5 glow-long' 
        : 'border-short/30 bg-short/5 glow-short'
      }
    `}>
      {/* Header com tipo de operação e indicador */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium px-2 py-0.5 rounded ${stratInfo.color}`}>
            {stratInfo.type}
          </span>
          <span className="text-xs font-bold text-foreground">
            📊 {stratInfo.label}
          </span>
        </div>
        <span className="text-xs text-foreground-muted">
          {date} {time}
        </span>
      </div>
      
      {/* Símbolo e direção */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xl font-bold text-foreground">
          {signal.symbol}
        </span>
        <span className={`
          text-sm font-bold px-3 py-1 rounded
          ${isLong ? 'bg-long/20 text-long' : 'bg-short/20 text-short'}
        `}>
          {signal.direction} {isLong ? '🟢' : '🔴'}
        </span>
      </div>
      
      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        <span className={`text-xs px-2 py-1 rounded ${stratInfo.color}`}>
          {stratInfo.label}
        </span>
        <span className="text-xs px-2 py-1 rounded bg-background-tertiary text-foreground-muted">
          {signal.timeframe.toUpperCase()}
        </span>
        <span className="text-xs px-2 py-1 rounded bg-accent-blue/20 text-accent-blue">
          ${signal.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
        </span>
      </div>
      
      {/* Indicadores */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        {signal.rsi && (
          <div className="bg-background-secondary rounded p-2">
            <span className="text-foreground-muted block">RSI</span>
            <span className="text-foreground font-medium">{Number(signal.rsi).toFixed(1)}</span>
          </div>
        )}
        {signal.macd && (
          <div className="bg-background-secondary rounded p-2">
            <span className="text-foreground-muted block">MACD</span>
            <span className="text-foreground font-medium">{Number(signal.macd).toFixed(4)}</span>
          </div>
        )}
        {signal.ema50 && (
          <div className="bg-background-secondary rounded p-2">
            <span className="text-foreground-muted block">EMA50</span>
            <span className="text-foreground font-medium">${Number(signal.ema50).toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
