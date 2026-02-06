import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Portal Sinais | Trading Signals Dashboard',
  description: 'Dashboard de sinais de trading em tempo real - RSI, MACD, GCM',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className="bg-background text-foreground min-h-screen">
        {children}
      </body>
    </html>
  );
}
