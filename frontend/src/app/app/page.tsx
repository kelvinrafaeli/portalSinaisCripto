'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Sidebar, Header, SignalFeed, ActivePairs } from '@/components';

const AUTH_KEY = 'ps-auth';

export default function AppPage() {
  const router = useRouter();

  useEffect(() => {
    const authed = localStorage.getItem(AUTH_KEY) === 'true';
    if (!authed) {
      router.replace('/login');
    }
  }, [router]);

  // Inicializa conexao WebSocket
  useWebSocket();

  const handleLogout = () => {
    localStorage.removeItem(AUTH_KEY);
    router.replace('/login');
  };

  return (
    <div className="flex min-h-screen flex-col lg:h-screen lg:flex-row">
      {/* Sidebar esquerda */}
      <Sidebar />

      {/* Area principal */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header com filtros */}
        <Header onLogout={handleLogout} />

        {/* Conteudo principal com Feed e Pares Ativos */}
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Feed de sinais - area principal com scroll */}
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

          {/* Pares ativos - fixo no lado direito */}
          <div className="w-full lg:w-[420px] lg:min-w-[420px] border-t lg:border-l border-border overflow-y-auto">
            <ActivePairs />
          </div>
        </div>
      </main>
    </div>
  );
}
