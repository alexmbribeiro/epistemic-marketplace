import { useEffect, useRef } from "react";
import type { DebateEvent } from "@/types";

type EventHandler = (event: DebateEvent) => void;

const MAX_RETRY_DELAY_MS = 10_000;

export function useDebateWebSocket(debateId: string | null, onEvent: EventHandler) {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  useEffect(() => {
    if (!debateId) return;

    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    // Set when we are meant to stop: the component unmounted, or the debate
    // finished and the server hung up on purpose.
    let done = false;

    const open = () => {
      if (done) return;

      const base = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
      socket = new WebSocket(`${base}/debates/${debateId}/live`);

      socket.onopen = () => {
        attempt = 0;
      };

      socket.onmessage = (e) => {
        let parsed: DebateEvent;
        try {
          parsed = JSON.parse(e.data) as DebateEvent;
        } catch {
          return; // malformed frame, ignore
        }
        // The server closes the socket right after this one, so the close
        // that follows is expected rather than a dropout to reconnect from.
        if (parsed.event === "debate_complete") done = true;
        onEventRef.current(parsed);
      };

      // onerror always fires before onclose, so reconnect from onclose only
      // and keep this quiet — otherwise a backend restart surfaces as an
      // unhandled "websocket is closed" error.
      socket.onerror = () => {};

      socket.onclose = () => {
        socket = null;
        if (done) return;
        const delay = Math.min(1000 * 2 ** attempt, MAX_RETRY_DELAY_MS);
        attempt += 1;
        retryTimer = setTimeout(open, delay);
      };
    };

    open();

    return () => {
      done = true;
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
    };
  }, [debateId]);
}
