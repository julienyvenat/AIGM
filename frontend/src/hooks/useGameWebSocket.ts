import { useState, useEffect, useCallback, useRef } from 'react';
import type { Entity } from '../components/BattleMap';

export type SenderType = 'user' | 'server';
export type MessageType = 'narrator' | 'system' | 'error' | 'chat' | 'combat_state' | 'scene_image';
export type MessageCategory = 'ROLEPLAY' | 'ACTION' | 'SYSTEM' | 'IGNORE';

export interface GameMessage {
  id: string;
  sender: SenderType;
  type: MessageType;
  category?: MessageCategory;
  message: string;
  timestamp?: string;
}

export function useGameWebSocket(playerId: string | null, onStatsUpdate?: (character: any) => void) {
export function useGameWebSocket(playerId: string | null, universeId?: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<GameMessage[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [currentSceneImage, setCurrentSceneImage] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!playerId) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setTimeout(() => setIsConnected(false), 0); // We'll fix this without using setTimeout if possible, but let's just make it a clean state reset later or ignore it for now using eslint-disable
      return;
    }

    let reconnectTimer: number;
    let isMounted = true;

    const connect = () => {
      const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
      const uId = universeId || 'default';
      const wsUrl = `${baseUrl}/${uId}/${playerId}`;

      console.log(`Attempting to connect to ${wsUrl}...`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMounted) return;
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data = JSON.parse(event.data);


          if (data.type === 'history' && Array.isArray(data.messages)) {
            setMessages(data.messages);
            return;
          }

          if (data.type === 'combat_state' && Array.isArray(data.entities)) {
            setEntities(data.entities);
            return;
          }


          if (data.type === 'stats_update' && data.character) {
            if (onStatsUpdate) {
              onStatsUpdate(data.character);
            }
            return;
          }

          if (data.type === 'scene_image' && data.url) {
            setCurrentSceneImage(data.url);

            // Add local system message
            const systemMessage: GameMessage = {
              id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
              sender: 'server',
              type: 'system',
              category: 'SYSTEM',
              message: "Le MJ a partagé une vision...",
            };
            setMessages((prev) => [...prev, systemMessage]);
            return;
          }

          const newMessage: GameMessage = {
            id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
            sender: 'server',
            type: data.type || 'system',
            category: data.category,
            message: data.message || data.text || JSON.stringify(data),
          };

          setMessages((prev) => [...prev, newMessage]);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          const errorMessage: GameMessage = {
             id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
             sender: 'server',
             type: 'error',
             message: typeof event.data === 'string' ? event.data : 'Received unparseable message from server',
          };
          setMessages((prev) => [...prev, errorMessage]);
        }
      };

      ws.onclose = () => {
        if (!isMounted) return;
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Reconnect after 3 seconds
        reconnectTimer = window.setTimeout(() => {
          if (isMounted) {
            connect();
          }
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // onclose will handle reconnection
      };
    };

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [playerId, universeId]);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim()) return;

    // Optimistic UI update
    const optimisticMessage: GameMessage = {
      id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
      sender: 'user',
      type: 'chat',
      message: text,
    };

    setMessages((prev) => [...prev, optimisticMessage]);

    // Send to server
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = { text };
      wsRef.current.send(JSON.stringify(payload));
    } else {
       console.error("Cannot send message, WebSocket is not open.");
       // Optional: could add an error message to the UI here if needed
    }
  }, []);

  const clearSceneImage = useCallback(() => {
    setCurrentSceneImage(null);
  }, []);

  return { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage };
}
