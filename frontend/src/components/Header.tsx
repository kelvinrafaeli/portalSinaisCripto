'use client';

import { useSignalStore } from '@/lib/store';

const TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d'];
const STRATEGIES = ['RSI', 'MACD', 'GCM', 'COMBO'];

export function Header() {
  const isConnected = useSignalStore((state) => state.isConnected);
  const signals = useSignalStore((state) => state.signals);
  const activeTimeframe = useSignalStore((state) => state.activeTimeframe);
  const activeStrategy = useSignalStore((state) => state.activeStrategy);
  const setActiveTimeframe = useSignalStore((state) => state.setActiveTimeframe);
  const setActiveStrategy = useSignalStore((state) => state.setActiveStrategy);
  const clearSignals = useSignalStore((state) => state.clearSignals);

  const longSignals = signals.filter((s) => s.direction === 'LONG').length;
  const shortSignals = signals.filter((s) => s.direction === 'SHORT').length;

  return (
    <header className="bg-background-secondary border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Status */}
        <div className="flex items-center gap-6">
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
        <div className="flex items-center gap-2">
          <span className="text-xs text-foreground-muted mr-2">Timeframe:</span>
          <button
            onClick={() => setActiveTimeframe(null)}
            className={`
              px-3 py-1.5 rounded text-xs font-medium transition-colors
              ${!activeTimeframe 
                ? 'bg-accent-blue text-white' 
                : 'bg-background-tertiary text-foreground-muted hover:bg-background-tertiary/80'
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
                px-3 py-1.5 rounded text-xs font-medium transition-colors
                ${activeTimeframe === tf 
                  ? 'bg-accent-blue text-white' 
                  : 'bg-background-tertiary text-foreground-muted hover:bg-background-tertiary/80'
                }
              `}
            >
              {tf}
            </button>
          ))}
        </div>
        
        {/* Filtros rápidos por Estratégia */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-foreground-muted mr-2">Estratégia:</span>
          <button
            onClick={() => setActiveStrategy(null)}
            className={`
              px-3 py-1.5 rounded text-xs font-medium transition-colors
              ${!activeStrategy 
                ? 'bg-accent-purple text-white' 
                : 'bg-background-tertiary text-foreground-muted hover:bg-background-tertiary/80'
              }
            `}
          >
            Todos
          </button>
          {STRATEGIES.map((strat) => (
            <button
              key={strat}
              onClick={() => setActiveStrategy(strat)}
              className={`
                px-3 py-1.5 rounded text-xs font-medium transition-colors
                ${activeStrategy === strat 
                  ? 'bg-accent-purple text-white' 
                  : 'bg-background-tertiary text-foreground-muted hover:bg-background-tertiary/80'
                }
              `}
            >
              {strat}
            </button>
          ))}
        </div>
        
        {/* Clear */}
        <button
          onClick={clearSignals}
          className="px-4 py-1.5 text-xs text-foreground-muted hover:text-foreground bg-background-tertiary rounded transition-colors"
        >
          Limpar
        </button>
      </div>
    </header>
  );
}
