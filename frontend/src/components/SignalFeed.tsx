'use client';

import { useFilteredSignals, useSignalStore } from '@/lib/store';
import { SignalCard } from './SignalCard';
import { CryptoSummaryCard } from './CryptoSummaryCard';

export function SignalFeed() {
  const filteredSignals = useFilteredSignals();
  const isConnected = useSignalStore((state) => state.isConnected);

  return (
    <div className="space-y-4">
      <CryptoSummaryCard />

      {!isConnected && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-border border-t-accent-blue rounded-full animate-spin mx-auto mb-4" />
            <p className="text-foreground-muted">Conectando ao servidor...</p>
          </div>
        </div>
      )}

      {isConnected && filteredSignals.length === 0 && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4">📊</div>
            <p className="text-foreground-muted text-lg mb-2">Aguardando alertas...</p>
            <p className="text-foreground-muted text-sm">
              Os alertas aparecerão aqui quando forem detectados
            </p>
          </div>
        </div>
      )}

      {isConnected && filteredSignals.map((signal, index) => (
        <SignalCard 
          key={`${signal.symbol}-${signal.timeframe}-${signal.timestamp}-${index}`} 
          signal={signal} 
        />
      ))}
    </div>
  );
}
