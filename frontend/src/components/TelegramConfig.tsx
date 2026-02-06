'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface TelegramStatus {
  enabled: boolean;
  configured: boolean;
  masked_token?: string;
  masked_chat_id?: string;
  strategy_groups?: Record<string, string>;
  masked_summary_group?: string;
}

export function TelegramConfig() {
  const [isOpen, setIsOpen] = useState(false);
  const [botToken, setBotToken] = useState('');
  const [status, setStatus] = useState<TelegramStatus>({ enabled: false, configured: false });
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [summaryGroup, setSummaryGroup] = useState('');
  const [isSavingSummary, setIsSavingSummary] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const telegramStatus = await api.getTelegramStatus();
      setStatus(telegramStatus);
    } catch (error) {
      console.error('Erro ao carregar status do Telegram:', error);
    }
  };

  const handleSave = async () => {
    if (!botToken.trim()) {
      setMessage({ type: 'error', text: 'Preencha o token do bot' });
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      await api.configureTelegram(botToken.trim());
      await loadStatus();
      setMessage({ type: 'success', text: 'Token configurado com sucesso!' });
      setBotToken('');
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao configurar Telegram' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setMessage(null);

    try {
      const strategies = Object.keys(status.strategy_groups || {});
      if (strategies.length > 0) {
        await api.testTelegram(undefined, strategies[0]);
      } else {
        await api.testTelegram();
      }
      setMessage({ type: 'success', text: 'Mensagem de teste enviada!' });
    } catch (error: any) {
      let errorText = 'Falha ao enviar mensagem.';
      try {
        const response = await error?.response?.json?.();
        if (response?.detail) {
          errorText = response.detail;
        }
      } catch {
        if (error?.message?.includes('503') || error?.message?.includes('fetch')) {
          errorText = 'Erro de conexão: verifique sua internet/DNS.';
        }
      }
      setMessage({ type: 'error', text: errorText });
    } finally {
      setIsTesting(false);
    }
  };

  const groupCount = Object.keys(status.strategy_groups || {}).length;
  const summaryConfigured = Boolean(status.masked_summary_group);

  const handleSaveSummaryGroup = async () => {
    if (!summaryGroup.trim()) {
      setMessage({ type: 'error', text: 'Informe o ID do grupo de resumo' });
      return;
    }

    setIsSavingSummary(true);
    setMessage(null);

    try {
      await api.configureSummaryGroup(summaryGroup.trim());
      await loadStatus();
      setMessage({ type: 'success', text: 'Grupo de resumo configurado!' });
      setSummaryGroup('');
    } catch (error) {
      setMessage({ type: 'error', text: 'Erro ao configurar grupo de resumo' });
    } finally {
      setIsSavingSummary(false);
    }
  };

  return (
    <div className="mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 rounded-lg bg-background-tertiary hover:bg-background transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">📱</span>
          <div className="text-left">
            <span className="text-sm font-medium text-foreground block">Telegram</span>
            <span className="text-xs text-foreground-muted">
              {status.configured 
                ? `Token OK • ${groupCount} grupo${groupCount !== 1 ? 's' : ''}`
                : 'Não configurado'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${status.configured ? 'bg-long' : 'bg-foreground-muted'}`} />
          <svg
            className={`w-4 h-4 text-foreground-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="mt-3 p-4 rounded-lg bg-background border border-border space-y-4">
          {/* Mostrar configuração atual se existir */}
          {status.configured && status.masked_token && (
            <div className="p-3 rounded bg-background-secondary border border-border">
              <p className="text-xs text-foreground-muted mb-2">✅ Token configurado:</p>
              <code className="text-sm bg-background-tertiary px-2 py-1 rounded">{status.masked_token}</code>
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            {/* Bot Token */}
            <div className="mb-4">
              <label className="text-xs text-foreground-muted block mb-1">
                {status.configured ? 'Atualizar Token' : 'Token do Bot'}
                <span className="text-foreground-muted ml-1">(do @BotFather)</span>
              </label>
              <input
                type="password"
                autoComplete="off"
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
                className="w-full bg-background-secondary border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none placeholder:text-foreground-muted/50"
              />
            </div>
          </form>

          {/* Mensagem de feedback */}
          {message && (
            <div
              className={`p-3 rounded text-sm ${
                message.type === 'success'
                  ? 'bg-long/20 text-long'
                  : 'bg-short/20 text-short'
              }`}
            >
              {message.text}
            </div>
          )}

          {/* Botões */}
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving || !botToken.trim()}
              className="flex-1 py-2 px-4 rounded-lg bg-accent-blue text-white font-medium text-sm hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? 'Salvando...' : 'Salvar Token'}
            </button>
            <button
              onClick={handleTest}
              disabled={isTesting || !status.configured}
              className="py-2 px-4 rounded-lg bg-background-tertiary text-foreground font-medium text-sm hover:bg-background-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isTesting ? 'Enviando...' : 'Testar'}
            </button>
          </div>

          {/* Grupo do resumo */}
          <div className="pt-3 border-t border-border">
            <p className="text-xs text-foreground-muted mb-2">📊 Grupo do resumo 1H (CryptoBubbles)</p>
            {summaryConfigured && status.masked_summary_group && (
              <div className="text-xs text-foreground-muted mb-2">
                Atual: <code className="bg-background-tertiary px-1 rounded">{status.masked_summary_group}</code>
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                autoComplete="off"
                value={summaryGroup}
                onChange={(e) => setSummaryGroup(e.target.value)}
                placeholder="-1001234567890"
                className="flex-1 bg-background-secondary border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none placeholder:text-foreground-muted/50"
              />
              <button
                onClick={handleSaveSummaryGroup}
                disabled={isSavingSummary || !summaryGroup.trim()}
                className="px-4 py-2 rounded-lg bg-background-tertiary text-foreground text-sm hover:bg-background-secondary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSavingSummary ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>

          {/* Instruções */}
          <div className="pt-3 border-t border-border">
            <p className="text-xs text-foreground-muted">
              <strong>Como configurar:</strong>
            </p>
            <ol className="text-xs text-foreground-muted mt-2 space-y-1 list-decimal list-inside">
              <li>Crie um bot no @BotFather e copie o token</li>
              <li>Cole o token acima e salve</li>
              <li>Configure os grupos em cada estratégia (clique para expandir)</li>
              <li>Defina um grupo para o resumo 1H do CryptoBubbles (opcional)</li>
            </ol>
            
            {groupCount > 0 && (
              <div className="mt-3 pt-3 border-t border-border/50">
                <p className="text-xs text-foreground-muted mb-2">📋 Grupos configurados:</p>
                <div className="space-y-1">
                  {Object.entries(status.strategy_groups || {}).map(([strategy, chatId]) => (
                    <div key={strategy} className="flex justify-between text-xs">
                      <span className="text-foreground">{strategy}</span>
                      <code className="text-foreground-muted">{chatId}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
