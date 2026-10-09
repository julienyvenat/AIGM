import { useState, useEffect, useCallback, useRef } from 'react';
import type { Entity } from '../components/BattleMap';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';

export type SenderType = 'user' | 'server';
export type MessageType = 'narrator' | 'system' | 'error' | 'chat' | 'combat_state' | 'scene_image' | 'battlemap_update' | 'audio_ready';
// 'GM' / 'PLAYER': a human-GM session's narration (see Phase D) -- the GM's
// own chat is broadcast as `narrator`/`GM` (authoritative), a regular
// player's chat as `chat`/`PLAYER` (not auto-narrated by the AI).
export type MessageCategory = 'ROLEPLAY' | 'ACTION' | 'SYSTEM' | 'IGNORE' | 'GM' | 'PLAYER';

export interface GameMessage {
  id: string;
  sender: SenderType;
  type: MessageType;
  category?: MessageCategory;
  message: string;
  timestamp?: string;
}

// Result of a human GM's on-demand, advisory-only AI consultation (Phase D):
// never auto-broadcast, only ever sent back to the GM who asked.
export interface GmAdvisory {
  advisoryType: 'narrator' | 'arbitrator';
  message?: string;
  result?: {
    action_type: string;
    narrative: string;
    success: boolean;
    hp_change: number;
    consumed_resource_type: string | null;
    consumed_resource_name: string | null;
  };
}

export function useGameWebSocket(playerId: string | null, sessionId: string | null, onStatsUpdate?: (character: Record<string, unknown>) => void, isGm = false) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<GameMessage[]>([]);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [currentSceneImage, setCurrentSceneImage] = useState<string | null>(null);
  const [battlemapImageUrl, setBattlemapImageUrl] = useState<string | null>(null);
  // Latest advisory response to a GM's on-demand consult (Phase D) --
  // personal-only, never appended to `messages`.
  const [gmAdvisory, setGmAdvisory] = useState<GmAdvisory | null>(null);
  // Battlemap grid size, driven by the backend (GameSession.grid_width/height
  // via the combat_state message) instead of a hardcoded 15x15.
  const [gridWidth, setGridWidth] = useState(15);
  const [gridHeight, setGridHeight] = useState(15);
  const wsRef = useRef<WebSocket | null>(null);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!playerId || !sessionId || !token) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setTimeout(() => setIsConnected(false), 0);
      return;
    }

    let reconnectTimer: number;
    let isMounted = true;

    const connect = () => {
      const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
      const wsUrl = `${baseUrl}/ws/${sessionId}/${playerId}?token=${token}`;

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
            if (typeof data.grid_width === 'number') {
              setGridWidth(data.grid_width);
            }
            if (typeof data.grid_height === 'number') {
              setGridHeight(data.grid_height);
            }
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

          // Skip echoing our own broadcast back as a second bubble: the
          // sender already shows it optimistically (see sendMessage below).
          // Regular player chat is de-duped per-sender via player_id; the
          // GM's authoritative narration carries no player_id (a session
          // has one GM), so the GM client de-dupes it via `isGm` instead.
          if (data.type === 'chat' && data.player_id && data.player_id === playerId) {
            return;
          }
          if (data.type === 'narrator' && data.category === 'GM' && isGm) {
            return;
          }

          if (data.type === 'gm_advisory') {
            setGmAdvisory({
              advisoryType: data.advisory_type,
              message: data.message,
              result: data.result,
            });
            return;
          }

          if (data.type === 'battlemap_update') {
            setBattlemapImageUrl(data.url);
            return;
          }

          if (data.type === 'audio_ready' && data.url) {
            // Narration/NPC dialogue TTS clip is ready: play it immediately
            // with the plain HTML5 Audio API (no library needed for a first
            // version). Same URL-prefixing convention as BattleMap's
            // battlemap image (backend-served static file, separate origin
            // in dev).
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            try {
              const audio = new Audio(`${baseUrl}${data.url}`);
              audio.play().catch((err) => console.error('Failed to play narration audio:', err));
            } catch (err) {
              console.error('Failed to play narration audio:', err);
            }
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

      ws.onclose = (event) => {
        if (!isMounted) return;
        console.log(`WebSocket disconnected (Code: ${event.code}, Reason: ${event.reason})`);
        setIsConnected(false);
        wsRef.current = null;

        if (event.code === 1008) {
           window.alert('Violation de politique (Erreur 1008) : Session invalide ou non autorisée.');
           navigate('/dashboard');
           return;
        }

        // Reconnect after 3 seconds for unexpected closures
        if (event.code !== 1000) {
           reconnectTimer = window.setTimeout(() => {
             if (isMounted) {
               connect();
             }
           }, 3000);
        }
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
        wsRef.current.close(1000, "Unmounting component");
        wsRef.current = null;
      }
    };
  }, [playerId, sessionId, token, navigate, onStatsUpdate, isGm]);

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
    }
  }, []);


  const sendAction = useCallback((action: string, itemId: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'UI_ACTION',
        action,
        item_id: itemId
      }));
    }
  }, []);

  // Manual Battlemap token placement (drag & drop of a PC or NPC token to a
  // new cell). Same UI_ACTION channel as sendAction above, but keyed on
  // entity_id/x/y rather than item_id (see src/main.py's move_entity branch).
  const sendMoveEntity = useCallback((entityId: string, x: number, y: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'UI_ACTION',
        action: 'move_entity',
        entity_id: entityId,
        x,
        y
      }));
    }
  }, []);

  const clearSceneImage = useCallback(() => {
    setCurrentSceneImage(null);
  }, []);

  // Human-GM on-demand AI consultation (Phase D): advisory only, backend
  // rejects these unless the caller is the session's GM in a HUMAN-GM
  // session (see gm_consult_narrator/gm_consult_arbitrator in main.py).
  const sendGmConsultNarrator = useCallback((text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'UI_ACTION', action: 'gm_consult_narrator', text }));
    }
  }, []);

  const sendGmConsultArbitrator = useCallback((entityId: string, text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'UI_ACTION', action: 'gm_consult_arbitrator', entity_id: entityId, text }));
    }
  }, []);

  const sendGmGenerateScene = useCallback((description: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'UI_ACTION', action: 'gm_generate_scene', description }));
    }
  }, []);

  const clearGmAdvisory = useCallback(() => {
    setGmAdvisory(null);
  }, []);

  return {
    isConnected,
    messages,
    sendMessage,
    sendAction,
    sendMoveEntity,
    entities,
    currentSceneImage,
    clearSceneImage,
    battlemapImageUrl,
    gridWidth,
    gridHeight,
    gmAdvisory,
    clearGmAdvisory,
    sendGmConsultNarrator,
    sendGmConsultArbitrator,
    sendGmGenerateScene,
  };
}
