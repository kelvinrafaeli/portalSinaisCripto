'use client';

import { create } from 'zustand';

// Types
export interface Signal {
  symbol: string;
  timeframe: string;
  strategy: string;
  direction: 'LONG' | 'SHORT';
  price: number;
  message: string;
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  ema50?: number;
  timestamp: string;
}

export interface Config {
  strategies: {
    active: string[];
    available: string[];
  };
  symbols: string[];
  timeframes: string[];
  rsi: {
    period: number;
    signal: number;
    overbought: number;
    oversold: number;
  };
  macd: {
    fast: number;
    slow: number;
    signal: number;
  };
  gcm: {
    harsi_len: number;
    harsi_smooth: number;
  };
}

interface SignalStore {
  // Sinais
  signals: Signal[];
  addSignal: (signal: Signal) => void;
  clearSignals: () => void;

  // Conexão
  isConnected: boolean;
  setConnected: (connected: boolean) => void;

  // Filtros
  activeTimeframe: string | null;
  activeStrategy: string | null;
  setActiveTimeframe: (tf: string | null) => void;
  setActiveStrategy: (strat: string | null) => void;

  // Configuração
  config: Config | null;
  setConfig: (config: Config) => void;

  // Símbolos selecionados
  selectedSymbols: string[];
  toggleSymbol: (symbol: string) => void;
  setSelectedSymbols: (symbols: string[]) => void;

  // Engine status
  engineRunning: boolean;
  setEngineRunning: (running: boolean) => void;
}

export const useSignalStore = create<SignalStore>((set) => ({
  // Sinais
  signals: [],
  addSignal: (signal) =>
    set((state) => ({
      signals: [signal, ...state.signals].slice(0, 100), // Mantém últimos 100
    })),
  clearSignals: () => set({ signals: [] }),

  // Conexão
  isConnected: false,
  setConnected: (connected) => set({ isConnected: connected }),

  // Filtros
  activeTimeframe: null,
  activeStrategy: null,
  setActiveTimeframe: (tf) => set({ activeTimeframe: tf }),
  setActiveStrategy: (strat) => set({ activeStrategy: strat }),

  // Configuração
  config: null,
  setConfig: (config) => set({ config }),

  // Símbolos
  selectedSymbols: [],
  toggleSymbol: (symbol) =>
    set((state) => ({
      selectedSymbols: state.selectedSymbols.includes(symbol)
        ? state.selectedSymbols.filter((s) => s !== symbol)
        : [...state.selectedSymbols, symbol],
    })),
  setSelectedSymbols: (symbols) => set({ selectedSymbols: symbols }),

  // Engine
  engineRunning: false,
  setEngineRunning: (running) => set({ engineRunning: running }),
}));

// Filtros computados
export const useFilteredSignals = () => {
  const signals = useSignalStore((state) => state.signals);
  const activeTimeframe = useSignalStore((state) => state.activeTimeframe);
  const activeStrategy = useSignalStore((state) => state.activeStrategy);

  return signals.filter((signal) => {
    if (activeTimeframe && signal.timeframe !== activeTimeframe) return false;
    if (activeStrategy && signal.strategy !== activeStrategy) return false;
    return true;
  });
};
