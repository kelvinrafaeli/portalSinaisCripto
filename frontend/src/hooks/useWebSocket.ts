'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useSignalStore, Signal } from '@/lib/store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  
  const addSignal = useSignalStore((state) => state.addSignal);
  const setConnected = useSignalStore((state) => state.setConnected);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'signal') {
            const signal: Signal = message.data;
            addSignal(signal);
            
            // Notificação sonora ou visual
            if (typeof window !== 'undefined' && Notification.permission === 'granted') {
              new Notification(`${signal.direction} Signal - ${signal.symbol}`, {
                body: `${signal.strategy} on ${signal.timeframe}`,
                icon: signal.direction === 'LONG' ? '🟢' : '🔴',
              });
            }
          }
          
          if (message.type === 'heartbeat') {
            console.log('Heartbeat received');
          }
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        setConnected(false);
        
        // Reconectar após 3 segundos
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Reconnecting...');
          connect();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect:', error);
      setConnectionStatus('disconnected');
    }
  }, [addSignal, setConnected]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
    setConnected(false);
  }, [setConnected]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Conectar automaticamente
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Solicitar permissão de notificação
  useEffect(() => {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      if (Notification.permission === 'default') {
        Notification.requestPermission();
      }
    }
  }, []);

  return {
    connect,
    disconnect,
    sendMessage,
    connectionStatus,
    isConnected: connectionStatus === 'connected',
  };
}
