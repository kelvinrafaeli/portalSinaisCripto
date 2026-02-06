'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';

interface ActivePair {
  symbol: string;
  name: string;
  binance_symbol: string;
  rank?: number;
  price?: number;
  volume?: number;
  marketcap?: number;
  change_1h?: number;
  change_24h?: number;
  change_7d?: number;
}

interface ActivePairsData {
  source: string;
  count: number;
  limit?: number;
  pairs: ActivePair[];
}

export function ActivePairs() {
  const [data, setData] = useState<ActivePairsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchData = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getActivePairs(forceRefresh);
      setData(result);
    } catch (err) {
      setError('Erro ao carregar pares ativos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Atualizar a cada 5 minutos
    const interval = setInterval(() => fetchData(), 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const formatChange = (change: number | undefined) => {
    if (change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const getChangeColor = (change: number | undefined) => {
    if (change === undefined) return 'text-gray-500';
    if (change > 0) return 'text-green-500';
    if (change < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  const formatVolume = (volume: number | undefined) => {
    if (!volume) return '-';
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(2)}K`;
    return `$${volume.toFixed(2)}`;
  };

  const filteredPairs = data?.pairs.filter(
    (pair) =>
      pair.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pair.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const displayPairs = isExpanded ? filteredPairs : filteredPairs.slice(0, 10);

  return (
    <div className="h-full bg-surface p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-foreground">
            📊 Pares Ativos
          </h3>
          {data && (
            <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
              {data.count} pares
            </span>
          )}
          {data?.source === 'cryptobubbles' && (
            <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
              CryptoBubbles
            </span>
          )}
          {data?.source === 'config_fallback' && (
            <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
              Fallback
            </span>
          )}
          {data?.source === 'config' && (
            <span className="text-xs bg-gray-500/20 text-gray-400 px-2 py-1 rounded">
              Config
            </span>
          )}
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={loading}
          className="text-xs text-foreground-muted hover:text-foreground transition-colors disabled:opacity-50"
          title="Atualizar dados"
        >
          {loading ? '⏳' : '🔄'}
        </button>
      </div>

      {error && (
        <div className="text-red-500 text-sm mb-4">{error}</div>
      )}

      {data?.source === 'config_fallback' && (
        <div className="text-yellow-500 text-xs mb-3 p-2 bg-yellow-500/10 rounded">
          ⚠️ CryptoBubbles indisponível. Usando símbolos do config.
        </div>
      )}

      {data?.source === 'cryptobubbles' && (
        <p className="text-xs text-foreground-muted mb-3">
          Top {data.limit} pares ordenados por maior variação em 24h (valor absoluto)
        </p>
      )}

      {/* Busca */}
      <div className="mb-3">
        <input
          type="text"
          placeholder="Buscar par..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 text-sm bg-surface-dark border border-border rounded focus:outline-none focus:border-primary"
        />
      </div>

      {/* Lista de pares */}
      <div className="space-y-1 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
        {/* Header */}
        <div className="grid grid-cols-12 gap-1 text-xs font-medium text-foreground-muted px-2 py-1 border-b border-border sticky top-0 bg-surface">
          <div className="col-span-1">#</div>
          <div className="col-span-2">Par</div>
          <div className="col-span-2 text-right">1h</div>
          <div className="col-span-2 text-right">24h</div>
          <div className="col-span-2 text-right">7d</div>
          <div className="col-span-3 text-right">Vol 24h</div>
        </div>

        {displayPairs.map((pair, index) => (
          <div
            key={pair.binance_symbol}
            className="grid grid-cols-12 gap-1 text-sm px-2 py-1.5 hover:bg-surface-dark rounded transition-colors"
          >
            <div className="col-span-1 text-foreground-muted text-xs">
              {index + 1}
            </div>
            <div className="col-span-2">
              <div className="font-medium text-foreground text-xs">{pair.symbol}</div>
              <div className="text-[10px] text-foreground-muted truncate" title={pair.name}>
                {pair.name}
              </div>
            </div>
            <div className={`col-span-2 text-right text-xs ${getChangeColor(pair.change_1h)}`}>
              {formatChange(pair.change_1h)}
            </div>
            <div className={`col-span-2 text-right text-xs font-medium ${getChangeColor(pair.change_24h)}`}>
              {formatChange(pair.change_24h)}
            </div>
            <div className={`col-span-2 text-right text-xs ${getChangeColor(pair.change_7d)}`}>
              {formatChange(pair.change_7d)}
            </div>
            <div className="col-span-3 text-right text-foreground-muted text-xs">
              {formatVolume(pair.volume)}
            </div>
          </div>
        ))}

        {loading && !data && (
          <div className="text-center py-8 text-foreground-muted">
            Carregando pares...
          </div>
        )}

        {!loading && filteredPairs.length === 0 && searchTerm && (
          <div className="text-center py-4 text-foreground-muted">
            Nenhum par encontrado para "{searchTerm}"
          </div>
        )}
      </div>

      {/* Expandir/Contrair */}
      {filteredPairs.length > 10 && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full mt-3 py-2 text-sm text-primary hover:text-primary-light transition-colors border-t border-border"
        >
          {isExpanded ? `Mostrar menos ▲` : `Ver todos (${filteredPairs.length}) ▼`}
        </button>
      )}

      {/* Link CryptoBubbles */}
      {data?.source === 'cryptobubbles' && (
        <div className="mt-3 pt-3 border-t border-border">
          <a
            href="https://cryptobubbles.net/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-foreground-muted hover:text-primary transition-colors flex items-center gap-1"
          >
            <span>🔗</span>
            <span>Dados via CryptoBubbles</span>
          </a>
        </div>
      )}
    </div>
  );
}
