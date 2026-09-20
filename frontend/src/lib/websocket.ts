import { useEffect, useRef, useCallback } from "react";
import type { DebateEvent } from "@/types";

type EventHandler = (event: DebateEvent) => void;

export function useDebateWebSocket(debateId: string | null, onEvent: EventHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    if (!debateId) return;
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const ws = new WebSocket(`${wsUrl}/debates/${debateId}/live`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as DebateEvent;
        onEventRef.current(parsed);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  }, [debateId]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);
}
