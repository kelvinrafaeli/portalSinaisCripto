'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { Sidebar, Header, SignalFeed } from '@/components';

export default function Home() {
  // Inicializa conexão WebSocket
  useWebSocket();

  return (
    <div className="flex h-screen">
      {/* Sidebar esquerda */}
      <Sidebar />
      
      {/* Área principal */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header com filtros */}
        <Header />
        
        {/* Feed de sinais */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-foreground">
                Feed de Sinais
              </h2>
              <span className="text-sm text-foreground-muted">
                Atualização em tempo real
              </span>
            </div>
            
            <SignalFeed />
          </div>
        </div>
      </main>
    </div>
  );
}
