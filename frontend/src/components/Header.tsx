'use client';

import { useSignalStore } from '@/lib/store';

const TIMEFRAMES = ['3m', '5m', '15m', '30m', '1h', '4h', '1d'];
const STRATEGIES = [
  { id: 'RSI', label: 'RSI' },
  { id: 'MACD', label: 'MACD' },
  { id: 'GCM', label: 'GCM' },
  { id: 'RSI_EMA50', label: 'RSI EMA50' },
  { id: 'SCALPING', label: 'SCALPING' },
  { id: 'SWING_TRADE', label: 'SWING TRADE' },
  { id: 'DAY_TRADE', label: 'DAY TRADE' },
  { id: 'JFN', label: 'JFN' },
];

export function Header({ onLogout }: { onLogout?: () => void }) {
  const isConnected = useSignalStore((state) => state.isConnected);
  const signals = useSignalStore((state) => state.signals);
  const activeTimeframe = useSignalStore((state) => state.activeTimeframe);
  const activeStrategy = useSignalStore((state) => state.activeStrategy);
  const setActiveTimeframe = useSignalStore((state) => state.setActiveTimeframe);
  const setActiveStrategy = useSignalStore((state) => state.setActiveStrategy);
  const clearSignals = useSignalStore((state) => state.clearSignals);

  const longSignals = signals.filter((s) => s.direction === 'LONG').length;
  const shortSignals = signals.filter((s) => s.direction === 'SHORT').length;
  const filterButtonBase =
    'px-3 py-1.5 rounded-full text-[11px] font-semibold tracking-wide transition-colors';


  return (
    <header className="bg-background-secondary border-b border-border px-4 py-4 sm:px-6">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        {/* Status */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-long' : 'bg-short'}`} />
            <span className="text-sm text-foreground-muted">
              {isConnected ? 'Conectado' : 'Desconectado'}
            </span>
          </div>
          
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-long font-medium">{longSignals}</span>
              <span className="text-foreground-muted">Long</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-short font-medium">{shortSignals}</span>
              <span className="text-foreground-muted">Short</span>
            </div>
          </div>
        </div>
        
        {/* Filtros rápidos por Timeframe */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] uppercase tracking-widest text-foreground-muted/80 mr-2">
            Timeframe
          </span>
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border/70 bg-background-tertiary/40 p-1.5">
          <button
            onClick={() => setActiveTimeframe(null)}
            className={`
              ${filterButtonBase}
              ${!activeTimeframe 
                ? 'bg-accent-blue text-white shadow-sm' 
                : 'bg-background-secondary/70 text-foreground-muted hover:bg-background-secondary'
              }
            `}
          >
            Todos
          </button>
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTimeframe(tf)}
                className={`
                  ${filterButtonBase}
                  ${activeTimeframe === tf 
                    ? 'bg-accent-blue text-white shadow-sm' 
                    : 'bg-background-secondary/70 text-foreground-muted hover:bg-background-secondary'
                  }
                `}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
        
        {/* Filtros rápidos por Estratégia */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] uppercase tracking-widest text-foreground-muted/80 mr-2">
            Estratégia
          </span>
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border/70 bg-background-tertiary/40 p-1.5">
          <button
            onClick={() => setActiveStrategy(null)}
            className={`
              ${filterButtonBase}
              ${!activeStrategy 
                ? 'bg-accent-purple text-white shadow-sm' 
                : 'bg-background-secondary/70 text-foreground-muted hover:bg-background-secondary'
              }
            `}
          >
            Todos
          </button>
            {STRATEGIES.map((strat) => (
              <button
                key={strat.id}
                onClick={() => setActiveStrategy(strat.id)}
                className={`
                  ${filterButtonBase}
                  ${activeStrategy === strat.id 
                    ? 'bg-accent-purple text-white shadow-sm' 
                    : 'bg-background-secondary/70 text-foreground-muted hover:bg-background-secondary'
                  }
                `}
              >
                {strat.label}
              </button>
            ))}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {onLogout && (
            <button
              onClick={onLogout}
              className="w-full sm:w-auto px-4 py-1.5 text-xs text-foreground-muted hover:text-foreground bg-background-tertiary rounded transition-colors"
            >
              Sair
            </button>
          )}
          <button
            onClick={clearSignals}
            className="w-full sm:w-auto px-4 py-1.5 text-xs text-foreground-muted hover:text-foreground bg-background-tertiary rounded transition-colors"
          >
            Limpar Alertas
          </button>
        </div>
      </div>
    </header>
  );
}
