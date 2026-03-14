import { useState, useEffect, useCallback, useRef } from 'react';

export interface GameMessage {
  type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload?: any;
  timestamp?: number;
  sender?: string;
}

export const useGameWebSocket = () => {
  const [messages, setMessages] = useState<GameMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

  useEffect(() => {
    let isMounted = true;

    const connect = () => {
      try {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          return;
        }

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          setError(null);
          console.log('WebSocket connected');
          if (reconnectTimeoutRef.current !== null) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const message: GameMessage = JSON.parse(event.data);
            setMessages((prev) => [...prev, message]);
          } catch (e) {
            console.error('Failed to parse websocket message', event.data, e);
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          console.log('WebSocket disconnected');

          if (reconnectTimeoutRef.current === null) {
              reconnectTimeoutRef.current = window.setTimeout(() => {
                  reconnectTimeoutRef.current = null;
                  if (isMounted) {
                    console.log('Attempting to reconnect...');
                    connect();
                  }
              }, 3000);
          }
        };

        ws.onerror = (e) => {
          if (!isMounted) return;
          console.error('WebSocket error:', e);
          setError('WebSocket Connection Error');
        };

        wsRef.current = ws;
      } catch (e) {
        if (!isMounted) return;
        console.error('Error establishing websocket connection', e);
        setError('Failed to establish connection');
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current !== null) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [wsUrl]);

  const sendMessage = useCallback((message: GameMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message, WebSocket is not open');
      setError('Cannot send message: Not connected');
    }
  }, []);

  return {
    messages,
    isConnected,
    error,
    sendMessage,
  };
};
