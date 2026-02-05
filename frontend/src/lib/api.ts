const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Config endpoints
  async getConfig() {
    return this.request('/config/');
  }

  async updateConfig(config: Record<string, unknown>) {
    return this.request('/config/update', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async getSymbols() {
    return this.request('/config/symbols');
  }

  async updateSymbols(symbols: string[]) {
    return this.request('/config/symbols', {
      method: 'PUT',
      body: JSON.stringify(symbols),
    });
  }

  async getTimeframes() {
    return this.request('/config/timeframes');
  }

  // Signal endpoints
  async getRecentSignals(params?: { symbol?: string; strategy?: string; timeframe?: string }) {
    const query = new URLSearchParams();
    if (params?.symbol) query.set('symbol', params.symbol);
    if (params?.strategy) query.set('strategy', params.strategy);
    if (params?.timeframe) query.set('timeframe', params.timeframe);
    
    const queryString = query.toString();
    return this.request(`/signals/${queryString ? `?${queryString}` : ''}`);
  }

  async runAnalysis(params?: { symbols?: string[]; timeframes?: string[]; strategies?: string[] }) {
    return this.request('/signals/analyze', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  async analyzeSymbol(symbol: string, timeframe: string, strategies?: string[]) {
    const query = strategies ? `?strategies=${strategies.join(',')}` : '';
    return this.request(`/signals/analyze/${symbol}/${timeframe}${query}`);
  }

  async getStats() {
    return this.request('/signals/stats');
  }

  async getStrategiesStatus() {
    return this.request('/signals/strategies');
  }

  // Market endpoints
  async getTicker(symbol: string) {
    return this.request(`/market/ticker/${symbol}`);
  }

  async getTickers(symbols: string[]) {
    return this.request(`/market/tickers?symbols=${symbols.join(',')}`);
  }

  async getOHLCV(symbol: string, timeframe: string = '1h', limit: number = 100) {
    return this.request(`/market/ohlcv/${symbol}?timeframe=${timeframe}&limit=${limit}`);
  }

  async getPrice(symbol: string) {
    return this.request(`/market/price/${symbol}`);
  }

  // Engine endpoints
  async startEngine() {
    return this.request('/engine/start', { method: 'POST' });
  }

  async stopEngine() {
    return this.request('/engine/stop', { method: 'POST' });
  }

  async getEngineStatus() {
    return this.request<{ running: boolean }>('/engine/status');
  }

  // Health check
  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

export const api = new ApiClient(API_URL);
