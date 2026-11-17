/**
 * useWebSocket hook — connects to the backend WebSocket for real-time updates.
 */
import { useEffect, useRef, useCallback } from 'react';
import { getToken } from '../api/client';

export type WSEvent = {
  event: string;
  data: Record<string, unknown>;
  timestamp: string;
  project_id: string;
};

type Handler = (event: WSEvent) => void;

function getWsUrl(): string {
  const envWs = import.meta.env.VITE_WS_URL;
  if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
    return 'wss://devcrew-backend-snto.onrender.com';
  }
  return envWs ?? 'ws://localhost:8000';
}

const WS_BASE = getWsUrl();

export function useWebSocket(projectId: string | null, onMessage: Handler) {
  const ws = useRef<WebSocket | null>(null);
  const handlerRef = useRef<Handler>(onMessage);
  handlerRef.current = onMessage;

  const connect = useCallback(() => {
    if (!projectId) return;
    const token = getToken();
    if (!token) return;

    const url = `${WS_BASE}/ws/${projectId}?token=${token}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      console.log('[WS] Connected', projectId);
      // Keep-alive ping every 25s
      const ping = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) socket.send('ping');
      }, 25_000);
      socket.onclose = () => clearInterval(ping);
    };

    socket.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as WSEvent;
        if (parsed.event !== 'pong') handlerRef.current(parsed);
      } catch {/* ignore */ }
    };

    socket.onerror = () => console.warn('[WS] Error', projectId);

    socket.onclose = (e) => {
      console.log('[WS] Closed', e.code);
      // Reconnect after 3s if not intentional close
      if (e.code !== 1000 && e.code !== 4001) {
        setTimeout(connect, 3_000);
      }
    };
  }, [projectId]);

  useEffect(() => {
    connect();
    return () => {
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on unmount
        ws.current.close(1000, 'Component unmounted');
      }
    };
  }, [connect]);

  return ws;
}
