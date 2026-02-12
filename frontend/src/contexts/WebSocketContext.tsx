import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { WSEventType, WebSocketEvent } from '../types/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  lastMessage: WebSocketEvent<unknown> | null;
  sendMessage: (message: unknown) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws';

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketEvent<unknown> | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>(undefined);

  const connect = useCallback(() => {
    if (!isAuthenticated || !token) return;
    if (ws.current?.readyState === WebSocket.OPEN) return;

    // Append token to query param for auth (common pattern for WS)
    // Alternatively, some backends require ticket or cookie.
    // FastAPI can handle query params in WebSocket endpoint dependency.
    const url = `${WS_URL}?token=${token}`;

    const socket = new WebSocket(url);

    socket.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
    };

    socket.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
      ws.current = null;
      // Auto-reconnect after 3 seconds
      reconnectTimeout.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      socket.close();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (err) {
        console.error('Failed to parse WS message', err);
      }
    };

    ws.current = socket;
  }, [isAuthenticated, token]);

  useEffect(() => {
    if (isAuthenticated) {
      connect();
    }
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [isAuthenticated, connect]);

  const sendMessage = useCallback((message: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  const value = {
    isConnected,
    lastMessage,
    sendMessage,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const useWebSocketEvent = <T = unknown>(
  eventType: WSEventType,
  handler: (data: T) => void
) => {
  const { lastMessage } = useWebSocket();
  // Use ref to store the handler to avoid re-triggering effect on handler change
  const handlerRef = useRef(handler);
  // Track last processed message to prevent duplicates
  const lastProcessedRef = useRef<string | null>(null);

  // Keep handler ref up to date
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (lastMessage && lastMessage.event === eventType) {
      // Create a unique ID for this message to prevent duplicate processing
      const messageId = JSON.stringify(lastMessage);

      // Skip if we already processed this exact message
      if (lastProcessedRef.current === messageId) {
        return;
      }

      lastProcessedRef.current = messageId;
      handlerRef.current(lastMessage.data as T);
    }
  }, [lastMessage, eventType]);
};
