'use client';

import { useState, useEffect } from 'react';
import { useSignalStore } from '@/lib/store';
import { api } from '@/lib/api';

// Estratégias disponíveis com seus nomes de exibição
const STRATEGIES = [
  { id: 'GCM', label: 'GCM', description: 'Cruzamento simples' },
  { id: 'RSI', label: 'RSI', description: 'Cruzamento RSI' },
  { id: 'MACD', label: 'MACD', description: 'Cruzamento MACD' },
  { id: 'RSI_EMA50', label: 'RSI + EMA50', description: 'RSI com filtro EMA50' },
  { id: 'SCALPING', label: 'Scalping', description: 'EMA9/50 + RSI (3m)' },
  { id: 'SWING_TRADE', label: 'Swing Trade', description: 'Operações longas' },
  { id: 'DAY_TRADE', label: 'Day Trade', description: 'MACD + RSI juntos' },
];
const TIMEFRAMES = ['3m', '15m', '1h', '4h', '1d'];

export function Sidebar() {
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiSignal, setRsiSignal] = useState(9);
  const [macdFast, setMacdFast] = useState(12);
  const [macdSlow, setMacdSlow] = useState(26);
  const [macdSignal, setMacdSignal] = useState(9);
  const [harsiLen, setHarsiLen] = useState(10);
  const [harsiSmooth, setHarsiSmooth] = useState(5);
  
  const [activeStrategies, setActiveStrategies] = useState<string[]>(STRATEGIES);
  const engineRunning = useSignalStore((state) => state.engineRunning);
  const setEngineRunning = useSignalStore((state) => state.setEngineRunning);

  useEffect(() => {
    // Carregar configuração inicial
    api.getConfig().then((config: any) => {
      if (config.rsi) {
        setRsiPeriod(config.rsi.period);
        setRsiSignal(config.rsi.signal);
      }
      if (config.macd) {
        setMacdFast(config.macd.fast);
        setMacdSlow(config.macd.slow);
        setMacdSignal(config.macd.signal);
      }
      if (config.gcm) {
        setHarsiLen(config.gcm.harsi_len);
        setHarsiSmooth(config.gcm.harsi_smooth);
      }
      if (config.strategies?.active) {
        setActiveStrategies(config.strategies.active);
      }
    }).catch(console.error);

    // Verificar status do engine
    api.getEngineStatus().then((status) => {
      setEngineRunning(status.running);
    }).catch(console.error);
  }, [setEngineRunning]);

  const toggleStrategy = (stratId: string) => {
    setActiveStrategies((prev) =>
      prev.includes(stratId)
        ? prev.filter((s) => s !== stratId)
        : [...prev, stratId]
    );
  };

  const handleToggleEngine = async () => {
    try {
      if (engineRunning) {
        await api.stopEngine();
        setEngineRunning(false);
      } else {
        await api.startEngine();
        setEngineRunning(true);
      }
    } catch (error) {
      console.error('Failed to toggle engine:', error);
    }
  };

  return (
    <aside className="w-72 bg-background-secondary border-r border-border h-screen overflow-y-auto">
      <div className="p-4">
        <h1 className="text-xl font-bold text-foreground mb-1">Portal Sinais</h1>
        <p className="text-xs text-foreground-muted mb-6">Trading Signals Dashboard</p>
        
        {/* Engine Control */}
        <div className="mb-6">
          <button
            onClick={handleToggleEngine}
            className={`
              w-full py-3 rounded-lg font-medium text-sm transition-all
              ${engineRunning 
                ? 'bg-short/20 text-short hover:bg-short/30' 
                : 'bg-long/20 text-long hover:bg-long/30'
              }
            `}
          >
            {engineRunning ? '⏹ Parar Engine' : '▶ Iniciar Engine'}
          </button>
          <div className="flex items-center gap-2 mt-2">
            <div className={`w-2 h-2 rounded-full ${engineRunning ? 'bg-long status-pulse' : 'bg-foreground-muted'}`} />
            <span className="text-xs text-foreground-muted">
              {engineRunning ? 'Engine rodando' : 'Engine parado'}
            </span>
          </div>
        </div>
        
        {/* Estratégias */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-foreground mb-3">Estratégias</h3>
          <div className="space-y-2">
            {STRATEGIES.map((strat) => (
              <label
                key={strat.id}
                className="flex items-center gap-3 p-2 rounded hover:bg-background-tertiary cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={activeStrategies.includes(strat.id)}
                  onChange={() => toggleStrategy(strat.id)}
                  className="w-4 h-4 rounded border-border bg-background accent-long"
                />
                <div className="flex flex-col">
                  <span className="text-sm text-foreground">{strat.label}</span>
                  <span className="text-xs text-foreground-muted">{strat.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
        
        {/* RSI Settings */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-foreground mb-3">RSI</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Período</label>
              <input
                type="number"
                value={rsiPeriod}
                onChange={(e) => setRsiPeriod(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Sinal (SMA)</label>
              <input
                type="number"
                value={rsiSignal}
                onChange={(e) => setRsiSignal(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
          </div>
        </div>
        
        {/* MACD Settings */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-foreground mb-3">MACD</h3>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Fast</label>
              <input
                type="number"
                value={macdFast}
                onChange={(e) => setMacdFast(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-2 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Slow</label>
              <input
                type="number"
                value={macdSlow}
                onChange={(e) => setMacdSlow(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-2 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Signal</label>
              <input
                type="number"
                value={macdSignal}
                onChange={(e) => setMacdSignal(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-2 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
          </div>
        </div>
        
        {/* GCM Settings */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-foreground mb-3">GCM Heikin Ashi</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Length</label>
              <input
                type="number"
                value={harsiLen}
                onChange={(e) => setHarsiLen(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-2 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-foreground-muted block mb-1">Smooth</label>
              <input
                type="number"
                value={harsiSmooth}
                onChange={(e) => setHarsiSmooth(Number(e.target.value))}
                className="w-full bg-background border border-border rounded px-2 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none"
              />
            </div>
          </div>
        </div>
        
        {/* Apply Button */}
        <button
          onClick={async () => {
            try {
              await api.updateConfig({
                rsi_period: rsiPeriod,
                rsi_signal: rsiSignal,
                macd_fast: macdFast,
                macd_slow: macdSlow,
                macd_signal: macdSignal,
                harsi_len: harsiLen,
                harsi_smooth: harsiSmooth,
              });
              alert('Configurações atualizadas!');
            } catch (error) {
              console.error('Failed to update config:', error);
            }
          }}
          className="w-full py-2 bg-accent-blue text-white rounded-lg text-sm font-medium hover:bg-accent-blue/80 transition-colors"
        >
          Aplicar Configurações
        </button>
      </div>
    </aside>
  );
}
