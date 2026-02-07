'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const AUTH_KEY = 'ps-auth';

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');

    const expected = process.env.NEXT_PUBLIC_LOGIN_PASSWORD || '';
    if (!expected) {
      setError('Defina NEXT_PUBLIC_LOGIN_PASSWORD no .env.local.');
      return;
    }

    if (password !== expected) {
      setError('Senha invalida.');
      return;
    }

    localStorage.setItem(AUTH_KEY, 'true');
    router.replace('/dashboard');
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-6">
      <div className="w-full max-w-md rounded-2xl border border-border bg-background-secondary p-8 shadow-lg">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-foreground">Portal Alertas</h1>
          <p className="text-sm text-foreground-muted">Acesso restrito ao painel</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-foreground-muted block mb-2">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-lg border border-border bg-background-tertiary px-3 py-2 text-sm text-foreground focus:outline-none focus:border-accent-blue"
              placeholder="Digite a senha"
            />
          </div>

          {error && (
            <div className="rounded-lg border border-short/40 bg-short/10 px-3 py-2 text-xs text-short">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full rounded-lg bg-accent-blue py-2 text-sm font-semibold text-white hover:bg-accent-blue/90 transition-colors"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
