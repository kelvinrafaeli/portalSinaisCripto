'use client';

import { useState, useEffect } from 'react';
import { useSignalStore } from '@/lib/store';
import { api } from '@/lib/api';
import { TelegramConfig } from './TelegramConfig';

// Estratégias disponíveis com seus nomes de exibição
const STRATEGIES = [
  { id: 'GCM', label: 'GCM', description: 'HA-RSI (Heikin Ashi RSI) com cruzamento de 50 e filtro de tendencia' },
  { id: 'RSI', label: 'RSI', description: 'RSI Wilder cruzando niveis de sobrecompra/sobrevenda' },
  { id: 'MACD', label: 'MACD', description: 'Linha MACD cruzando signal com confirmacao direcional' },
  { id: 'RSI_EMA50', label: 'RSI + EMA50', description: 'RSI com filtro de tendencia pela EMA50' },
  { id: 'SCALPING', label: 'Scalping', description: 'EMA9/EMA50 crossover com confirmacao RSI >/< 50' },
  { id: 'SWING_TRADE', label: 'Swing Trade', description: 'HA-RSI cruzando 50 com filtro EMA100' },
  { id: 'DAY_TRADE', label: 'Day Trade', description: 'Confluencia de cruzamentos MACD e RSI dentro de janela' },
  { id: 'JFN', label: 'JFN', description: 'EMA20/EMA50 crossover com filtro de assertividade por simulacao' },
];
const TIMEFRAMES = ['3m', '5m', '15m', '30m', '1h', '4h', '1d'];

// Timeframes padrão por estratégia
const DEFAULT_STRATEGY_TIMEFRAMES: Record<string, string[]> = {
  'GCM': ['15m', '1h', '4h'],
  'RSI': ['15m', '1h', '4h'],
  'MACD': ['15m', '1h', '4h'],
  'RSI_EMA50': ['1h', '4h'],
  'SCALPING': ['3m', '5m'],
  'SWING_TRADE': ['4h', '1d'],
  'DAY_TRADE': ['15m', '1h'],
  'JFN': ['15m', '1h', '4h'],
};

const DEFAULT_STRATEGY_PARAMS: Record<string, Record<string, number | boolean>> = {
  RSI: { period: 14, signal_period: 9, overbought: 70, oversold: 30, use_ema_filter: true },
  MACD: { fast_period: 12, slow_period: 26, signal_period: 9 },
  GCM: { harsi_length: 10, harsi_smooth: 5, rsi_length: 7, rsi_mode: true, rsi_buy_level: -20, rsi_sell_level: 20 },
  RSI_EMA50: { rsi_period: 14, rsi_signal: 9, ema_period: 50 },
  SCALPING: { ema_fast: 9, ema_slow: 50, rsi_period: 14, rsi_neutral: 50 },
  SWING_TRADE: { harsi_len: 14, harsi_smooth: 7, ema_filter: 100 },
  DAY_TRADE: { macd_fast: 12, macd_slow: 26, macd_signal: 9, rsi_period: 14, rsi_ma_period: 9, confirm_window: 6 },
  JFN: { fast_length: 20, slow_length: 50 },
};

export function Sidebar() {
  const [strategyParams, setStrategyParams] = useState<Record<string, Record<string, number | boolean>>>(
    DEFAULT_STRATEGY_PARAMS
  );
  
  const [activeStrategies, setActiveStrategies] = useState<string[]>(STRATEGIES.map(s => s.id));
  const [strategyTimeframes, setStrategyTimeframes] = useState<Record<string, string[]>>(DEFAULT_STRATEGY_TIMEFRAMES);
  const [strategyGroups, setStrategyGroups] = useState<Record<string, string>>({});
  const [groupInputs, setGroupInputs] = useState<Record<string, string>>({});
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  const [savingGroup, setSavingGroup] = useState<string | null>(null);
  const [testingGroup, setTestingGroup] = useState<string | null>(null);
  const [savingParams, setSavingParams] = useState<string | null>(null);
  
  const engineRunning = useSignalStore((state) => state.engineRunning);
  const setEngineRunning = useSignalStore((state) => state.setEngineRunning);

  useEffect(() => {
    // Carregar configuração inicial
    api.getConfig().then((config: any) => {
      if (config.strategies?.active) {
        setActiveStrategies(config.strategies.active);
      }
      if (config.strategies?.timeframes) {
        setStrategyTimeframes(config.strategies.timeframes);
      }
      if (config.strategy_params) {
        setStrategyParams((prev) => {
          const merged: Record<string, Record<string, number | boolean>> = { ...prev };
          Object.keys(DEFAULT_STRATEGY_PARAMS).forEach((key) => {
            merged[key] = { ...DEFAULT_STRATEGY_PARAMS[key], ...(config.strategy_params[key] || {}) };
          });
          return merged;
        });
      }
    }).catch(console.error);

    // Verificar status do engine
    api.getEngineStatus().then((status) => {
      setEngineRunning(status.running);
    }).catch(console.error);

    // Carregar grupos de Telegram por estratégia
    api.getStrategyGroups().then((data) => {
      setStrategyGroups(data.groups || {});
    }).catch(console.error);
  }, [setEngineRunning]);

  const handleSaveGroup = async (stratId: string) => {
    const chatId = groupInputs[stratId]?.trim();
    if (!chatId) return;
    
    setSavingGroup(stratId);
    try {
      await api.configureStrategyGroup(stratId, chatId);
      // Atualizar estado local
      setStrategyGroups(prev => ({ ...prev, [stratId]: chatId }));
      setGroupInputs(prev => ({ ...prev, [stratId]: '' }));
    } catch (error) {
      console.error('Erro ao salvar grupo:', error);
    } finally {
      setSavingGroup(null);
    }
  };

  const handleRemoveGroup = async (stratId: string) => {
    try {
      await api.removeStrategyGroup(stratId);
      setStrategyGroups(prev => {
        const updated = { ...prev };
        delete updated[stratId];
        return updated;
      });
    } catch (error) {
      console.error('Erro ao remover grupo:', error);
    }
  };

  const handleTestGroup = async (stratId: string) => {
    setTestingGroup(stratId);
    try {
      await api.testTelegram(`🧪 Teste - Estratégia ${stratId}`, stratId);
    } catch (error) {
      console.error('Erro ao testar grupo:', error);
    } finally {
      setTestingGroup(null);
    }
  };

  const toggleStrategy = (stratId: string) => {
    setActiveStrategies((prev) =>
      prev.includes(stratId)
        ? prev.filter((s) => s !== stratId)
        : [...prev, stratId]
    );
  };

  const toggleStrategyTimeframe = (stratId: string, timeframe: string) => {
    setStrategyTimeframes((prev) => {
      const current = prev[stratId] || [];
      const updated = current.includes(timeframe)
        ? current.filter((t) => t !== timeframe)
        : [...current, timeframe];
      
      const newConfig = { ...prev, [stratId]: updated };
      
      // Salvar no backend
      api.updateStrategyTimeframes(newConfig).catch(console.error);
      
      return newConfig;
    });
  };

  const handleStrategyClick = (stratId: string, e: React.MouseEvent) => {
    // Prevenir toggle do checkbox quando clicar para expandir
    e.stopPropagation();
    setExpandedStrategy(expandedStrategy === stratId ? null : stratId);
  };

  const updateStrategyParam = (stratId: string, key: string, value: number | boolean) => {
    setStrategyParams((prev) => ({
      ...prev,
      [stratId]: {
        ...(prev[stratId] || {}),
        [key]: value,
      },
    }));
  };

  const handleSaveStrategyParams = async (stratId: string) => {
    const params = strategyParams[stratId] || {};
    setSavingParams(stratId);
    try {
      await api.updateConfig({ strategy_params: { [stratId]: params } });
    } catch (error) {
      console.error('Erro ao salvar parametros da estrategia:', error);
    } finally {
      setSavingParams(null);
    }
  };

  const renderStrategyConfig = (stratId: string) => {
    const params = strategyParams[stratId] || {};

    switch (stratId) {
      case 'RSI':
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-foreground-muted block mb-1">Periodo</label>
                <input
                  type="number"
                  value={Number(params.period)}
                  onChange={(e) => updateStrategyParam('RSI', 'period', Number(e.target.value))}
                  className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
                />
              </div>
              <div>
                <label className="text-[10px] text-foreground-muted block mb-1">Sinal</label>
                <input
                  type="number"
                  value={Number(params.signal_period)}
                  onChange={(e) => updateStrategyParam('RSI', 'signal_period', Number(e.target.value))}
                  className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
                />
              </div>
              <div>
                <label className="text-[10px] text-foreground-muted block mb-1">Overbought</label>
                <input
                  type="number"
                  value={Number(params.overbought)}
                  onChange={(e) => updateStrategyParam('RSI', 'overbought', Number(e.target.value))}
                  className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
                />
              </div>
              <div>
                <label className="text-[10px] text-foreground-muted block mb-1">Oversold</label>
                <input
                  type="number"
                  value={Number(params.oversold)}
                  onChange={(e) => updateStrategyParam('RSI', 'oversold', Number(e.target.value))}
                  className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
                />
              </div>
            </div>
          </div>
        );
      case 'MACD':
        return (
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Fast</label>
              <input
                type="number"
                value={Number(params.fast_period)}
                onChange={(e) => updateStrategyParam('MACD', 'fast_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Slow</label>
              <input
                type="number"
                value={Number(params.slow_period)}
                onChange={(e) => updateStrategyParam('MACD', 'slow_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Signal</label>
              <input
                type="number"
                value={Number(params.signal_period)}
                onChange={(e) => updateStrategyParam('MACD', 'signal_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'RSI_EMA50':
        return (
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI</label>
              <input
                type="number"
                value={Number(params.rsi_period)}
                onChange={(e) => updateStrategyParam('RSI_EMA50', 'rsi_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Sinal</label>
              <input
                type="number"
                value={Number(params.rsi_signal)}
                onChange={(e) => updateStrategyParam('RSI_EMA50', 'rsi_signal', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA</label>
              <input
                type="number"
                value={Number(params.ema_period)}
                onChange={(e) => updateStrategyParam('RSI_EMA50', 'ema_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'SCALPING':
        return (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA Fast</label>
              <input
                type="number"
                value={Number(params.ema_fast)}
                onChange={(e) => updateStrategyParam('SCALPING', 'ema_fast', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA Slow</label>
              <input
                type="number"
                value={Number(params.ema_slow)}
                onChange={(e) => updateStrategyParam('SCALPING', 'ema_slow', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI</label>
              <input
                type="number"
                value={Number(params.rsi_period)}
                onChange={(e) => updateStrategyParam('SCALPING', 'rsi_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI Neutro</label>
              <input
                type="number"
                value={Number(params.rsi_neutral)}
                onChange={(e) => updateStrategyParam('SCALPING', 'rsi_neutral', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'SWING_TRADE':
        return (
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">HARSI Len</label>
              <input
                type="number"
                value={Number(params.harsi_len)}
                onChange={(e) => updateStrategyParam('SWING_TRADE', 'harsi_len', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Smooth</label>
              <input
                type="number"
                value={Number(params.harsi_smooth)}
                onChange={(e) => updateStrategyParam('SWING_TRADE', 'harsi_smooth', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA</label>
              <input
                type="number"
                value={Number(params.ema_filter)}
                onChange={(e) => updateStrategyParam('SWING_TRADE', 'ema_filter', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'DAY_TRADE':
        return (
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">MACD Fast</label>
              <input
                type="number"
                value={Number(params.macd_fast)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'macd_fast', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">MACD Slow</label>
              <input
                type="number"
                value={Number(params.macd_slow)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'macd_slow', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">MACD Signal</label>
              <input
                type="number"
                value={Number(params.macd_signal)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'macd_signal', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI</label>
              <input
                type="number"
                value={Number(params.rsi_period)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'rsi_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI MA</label>
              <input
                type="number"
                value={Number(params.rsi_ma_period)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'rsi_ma_period', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Janela</label>
              <input
                type="number"
                value={Number(params.confirm_window)}
                onChange={(e) => updateStrategyParam('DAY_TRADE', 'confirm_window', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'GCM':
        return (
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">HARSI Len</label>
              <input
                type="number"
                value={Number(params.harsi_length)}
                onChange={(e) => updateStrategyParam('GCM', 'harsi_length', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Smooth</label>
              <input
                type="number"
                value={Number(params.harsi_smooth)}
                onChange={(e) => updateStrategyParam('GCM', 'harsi_smooth', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">RSI Len</label>
              <input
                type="number"
                value={Number(params.rsi_length)}
                onChange={(e) => updateStrategyParam('GCM', 'rsi_length', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Buy Level</label>
              <input
                type="number"
                value={Number(params.rsi_buy_level)}
                onChange={(e) => updateStrategyParam('GCM', 'rsi_buy_level', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">Sell Level</label>
              <input
                type="number"
                value={Number(params.rsi_sell_level)}
                onChange={(e) => updateStrategyParam('GCM', 'rsi_sell_level', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      case 'JFN':
        return (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA Fast</label>
              <input
                type="number"
                value={Number(params.fast_length)}
                onChange={(e) => updateStrategyParam('JFN', 'fast_length', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
            <div>
              <label className="text-[10px] text-foreground-muted block mb-1">EMA Slow</label>
              <input
                type="number"
                value={Number(params.slow_length)}
                onChange={(e) => updateStrategyParam('JFN', 'slow_length', Number(e.target.value))}
                className="w-full bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
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

  const rsiParams = strategyParams.RSI || DEFAULT_STRATEGY_PARAMS.RSI;
  const macdParams = strategyParams.MACD || DEFAULT_STRATEGY_PARAMS.MACD;
  const gcmParams = strategyParams.GCM || DEFAULT_STRATEGY_PARAMS.GCM;

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
          <div className="space-y-1">
            {STRATEGIES.map((strat) => (
              <div key={strat.id} className="rounded overflow-hidden">
                {/* Header da estratégia */}
                <div className="flex items-center gap-2 p-2 hover:bg-background-tertiary">
                  <input
                    type="checkbox"
                    checked={activeStrategies.includes(strat.id)}
                    onChange={() => toggleStrategy(strat.id)}
                    className="w-4 h-4 rounded border-border bg-background accent-long"
                  />
                  <button
                    onClick={(e) => handleStrategyClick(strat.id, e)}
                    className="flex-1 flex items-center justify-between text-left"
                  >
                    <div className="flex flex-col">
                      <span className="text-sm text-foreground">{strat.label}</span>
                      <span className="text-xs text-foreground-muted">
                        {strategyTimeframes[strat.id]?.length > 0 
                          ? strategyTimeframes[strat.id].join(', ') 
                          : 'Nenhum timeframe'}
                      </span>
                    </div>
                    <svg
                      className={`w-4 h-4 text-foreground-muted transition-transform ${expandedStrategy === strat.id ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
                
                {/* Timeframes e Telegram da estratégia */}
                {expandedStrategy === strat.id && (
                  <div className="px-2 pb-2 pt-1 bg-background rounded-b space-y-3">
                    {/* Timeframes */}
                    <div>
                      <p className="text-xs text-foreground-muted mb-2">Timeframes ativos:</p>
                      <div className="flex flex-wrap gap-1">
                        {TIMEFRAMES.map((tf) => {
                          const isActive = strategyTimeframes[strat.id]?.includes(tf);
                          return (
                            <button
                              key={tf}
                              onClick={() => toggleStrategyTimeframe(strat.id, tf)}
                              className={`
                                px-2 py-1 text-xs rounded transition-colors
                                ${isActive 
                                  ? 'bg-accent-blue text-white' 
                                  : 'bg-background-tertiary text-foreground-muted hover:bg-background-secondary'
                                }
                              `}
                            >
                              {tf}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Configuracao da estrategia */}
                    {(() => {
                      const config = renderStrategyConfig(strat.id);
                      if (!config) return null;
                      return (
                        <div className="pt-2 border-t border-border/50">
                          <p className="text-xs text-foreground-muted mb-2">Parametros da estrategia:</p>
                          {config}
                          <button
                            onClick={() => handleSaveStrategyParams(strat.id)}
                            disabled={savingParams === strat.id}
                            className="mt-2 w-full py-1 text-xs bg-background-tertiary text-foreground hover:bg-background-secondary rounded"
                          >
                            {savingParams === strat.id ? 'Salvando...' : 'Salvar parametros'}
                          </button>
                        </div>
                      );
                    })()}
                    
                    {/* Telegram Group */}
                    <div className="pt-2 border-t border-border/50">
                      <p className="text-xs text-foreground-muted mb-2">📱 Grupo Telegram:</p>
                      {strategyGroups[strat.id] ? (
                        <div className="flex items-center gap-2">
                          <code className="flex-1 text-xs bg-background-tertiary px-2 py-1 rounded text-foreground">
                            {strategyGroups[strat.id]}
                          </code>
                          <button
                            onClick={() => handleTestGroup(strat.id)}
                            disabled={testingGroup === strat.id}
                            className="p-1 text-xs text-accent-blue hover:bg-accent-blue/10 rounded"
                            title="Testar"
                          >
                            {testingGroup === strat.id ? '...' : '🧪'}
                          </button>
                          <button
                            onClick={() => handleRemoveGroup(strat.id)}
                            className="p-1 text-xs text-short hover:bg-short/10 rounded"
                            title="Remover"
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <input
                            type="text"
                            value={groupInputs[strat.id] || ''}
                            onChange={(e) => setGroupInputs(prev => ({ ...prev, [strat.id]: e.target.value }))}
                            placeholder="-1001234567890"
                            className="flex-1 bg-background-secondary border border-border rounded px-2 py-1 text-xs text-foreground focus:border-accent-blue focus:outline-none placeholder:text-foreground-muted/50"
                          />
                          <button
                            onClick={() => handleSaveGroup(strat.id)}
                            disabled={savingGroup === strat.id || !groupInputs[strat.id]?.trim()}
                            className="px-2 py-1 text-xs bg-accent-blue text-white rounded hover:bg-accent-blue/90 disabled:opacity-50"
                          >
                            {savingGroup === strat.id ? '...' : '✓'}
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="px-2 py-2 rounded bg-accent-blue/10 text-accent-blue text-xs">
                      {strat.description}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Telegram Config */}
        <TelegramConfig />
        
        {/* Apply Button */}
        <button
          onClick={async () => {
            try {
              await api.updateConfig({
                strategy_params: strategyParams,
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
