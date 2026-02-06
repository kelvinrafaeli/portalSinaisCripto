'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface TelegramStatus {
  enabled: boolean;
  configured: boolean;
  masked_token?: string;
  masked_chat_id?: string;
}

export function TelegramConfig() {
  const [isOpen, setIsOpen] = useState(false);
  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [status, setStatus] = useState<TelegramStatus>({ enabled: false, configured: false });
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    // Carregar status inicial
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
    // Se não está configurado, ambos são obrigatórios
    if (!status.configured && (!botToken.trim() || !chatId.trim())) {
      setMessage({ type: 'error', text: 'Preencha todos os campos' });
      return;
    }
    
    // Se já está configurado mas nenhum campo foi preenchido
    if (status.configured && !botToken.trim() && !chatId.trim()) {
      setMessage({ type: 'error', text: 'Preencha pelo menos um campo para atualizar' });
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      // Buscar configuração atual se precisar manter algum valor
      let tokenToSave = botToken.trim();
      let chatIdToSave = chatId.trim();
      
      // Se já configurado e campo vazio, usar valor atual (enviar vazio e deixar backend manter)
      if (status.configured) {
        if (!tokenToSave || !chatIdToSave) {
          setMessage({ type: 'error', text: 'Preencha ambos os campos para atualizar' });
          setIsSaving(false);
          return;
        }
      }
      
      await api.configureTelegram(tokenToSave, chatIdToSave);
      
      // Recarregar status para mostrar dados mascarados
      await loadStatus();
      
      setMessage({ type: 'success', text: 'Telegram configurado com sucesso!' });
      
      // Limpar campos após salvar (segurança)
      setBotToken('');
      setChatId('');
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
      await api.testTelegram();
      setMessage({ type: 'success', text: 'Mensagem de teste enviada!' });
    } catch (error: any) {
      // Tentar extrair mensagem de erro da API
      let errorText = 'Falha ao enviar mensagem.';
      try {
        const response = await error?.response?.json?.();
        if (response?.detail) {
          errorText = response.detail;
        }
      } catch {
        // Se não conseguir extrair, usar mensagem padrão
        if (error?.message?.includes('503') || error?.message?.includes('fetch')) {
          errorText = 'Erro de conexão: verifique sua internet/DNS.';
        }
      }
      setMessage({ type: 'error', text: errorText });
    } finally {
      setIsTesting(false);
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
              {status.configured ? 'Configurado' : 'Não configurado'}
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
              <p className="text-xs text-foreground-muted mb-2">✅ Configuração atual:</p>
              <div className="space-y-1">
                <p className="text-sm text-foreground">
                  <span className="text-foreground-muted">Token: </span>
                  <code className="bg-background-tertiary px-1 rounded">{status.masked_token}</code>
                </p>
                <p className="text-sm text-foreground">
                  <span className="text-foreground-muted">Chat ID: </span>
                  <code className="bg-background-tertiary px-1 rounded">{status.masked_chat_id}</code>
                </p>
              </div>
            </div>
          )}

          <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            {/* Bot Token */}
            <div className="mb-4">
              <label className="text-xs text-foreground-muted block mb-1">
                {status.configured ? 'Novo Token do Bot' : 'Token do Bot'}
                <span className="text-foreground-muted ml-1">(do @BotFather)</span>
              </label>
              <input
                type="password"
                autoComplete="off"
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder={status.configured ? 'Deixe vazio para manter atual' : '123456789:ABCdefGHIjklMNOpqrSTUvwxYZ'}
                className="w-full bg-background-secondary border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none placeholder:text-foreground-muted/50"
              />
            </div>

            {/* Chat ID */}
            <div className="mb-4">
              <label className="text-xs text-foreground-muted block mb-1">
                {status.configured ? 'Novo ID do Grupo/Chat' : 'ID do Grupo/Chat'}
                <span className="text-foreground-muted ml-1">(use @userinfobot)</span>
              </label>
              <input
                type="text"
                autoComplete="off"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                placeholder={status.configured ? 'Deixe vazio para manter atual' : '-1001234567890'}
                className="w-full bg-background-secondary border border-border rounded px-3 py-2 text-sm text-foreground focus:border-accent-blue focus:outline-none placeholder:text-foreground-muted/50"
              />
              <p className="text-xs text-foreground-muted mt-1">
                💡 Grupos têm ID negativo (ex: -1001234567890)
              </p>
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
              disabled={isSaving || !botToken.trim() || !chatId.trim()}
              className="flex-1 py-2 px-4 rounded-lg bg-accent-blue text-white font-medium text-sm hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? 'Salvando...' : 'Salvar'}
            </button>
            <button
              onClick={handleTest}
              disabled={isTesting || !status.configured}
              className="py-2 px-4 rounded-lg bg-background-tertiary text-foreground font-medium text-sm hover:bg-background-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isTesting ? 'Enviando...' : 'Testar'}
            </button>
          </div>

          {/* Instruções */}
          <div className="pt-3 border-t border-border">
            <p className="text-xs text-foreground-muted">
              <strong>Como configurar:</strong>
            </p>
            <ol className="text-xs text-foreground-muted mt-2 space-y-1 list-decimal list-inside">
              <li>Crie um bot no @BotFather e copie o token</li>
              <li>Adicione o bot ao seu grupo</li>
              <li>Use @userinfobot para obter o ID do grupo</li>
              <li>Cole as informações acima e salve</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
