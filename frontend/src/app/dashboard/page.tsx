'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { Header, SignalFeed, ActivePairs } from '@/components';

export default function DashboardPage() {
  useWebSocket();

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="w-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-foreground">
                Feed de Sinais
              </h2>
              <span className="text-sm text-foreground-muted">
                Atualizacao em tempo real
              </span>
            </div>

            <SignalFeed />
          </div>
        </div>

        <div className="w-full lg:w-[420px] lg:min-w-[420px] border-t lg:border-l border-border overflow-y-auto">
          <ActivePairs />
        </div>
      </main>
    </div>
  );
}
