import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Portal Alertas | Trading Alerts Dashboard',
  description: 'Dashboard de alertas de trading em tempo real - RSI, MACD, GCM',
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
