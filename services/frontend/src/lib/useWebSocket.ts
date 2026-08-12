import { useCallback, useEffect, useReducer, useRef } from "react";

export type WebSocketStatus = "idle" | "connecting" | "open" | "closed";

export type UseWebSocketResult<TMessage> = {
  closeReason: string | null;
  messages: TMessage[];
  sendJson: (payload: unknown) => boolean;
  status: WebSocketStatus;
};

type WebSocketState<TMessage> = {
  closeReason: string | null;
  messages: TMessage[];
  status: WebSocketStatus;
};

type WebSocketAction<TMessage> =
  | { type: "closed"; reason: string | null }
  | { type: "connecting" }
  | { type: "idle" }
  | { type: "message"; message: TMessage }
  | { type: "open" };

function webSocketReducer<TMessage>(
  state: WebSocketState<TMessage>,
  action: WebSocketAction<TMessage>,
): WebSocketState<TMessage> {
  switch (action.type) {
    case "closed":
      return { ...state, closeReason: action.reason, status: "closed" };
    case "connecting":
      return { closeReason: null, messages: [], status: "connecting" };
    case "idle":
      return { closeReason: null, messages: [], status: "idle" };
    case "message":
      return { ...state, messages: [...state.messages, action.message] };
    case "open":
      return { ...state, status: "open" };
  }
}

export function useWebSocket<TMessage = unknown>(
  url: string | null,
): UseWebSocketResult<TMessage> {
  const socketRef = useRef<WebSocket | null>(null);
  const [state, dispatch] = useReducer(webSocketReducer<TMessage>, {
    closeReason: null,
    messages: [],
    status: "idle",
  });

  useEffect(() => {
    if (url === null) {
      dispatch({ type: "idle" });
      socketRef.current = null;
      return;
    }

    dispatch({ type: "connecting" });

    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      dispatch({ type: "open" });
    };

    socket.onmessage = (event) => {
      dispatch({
        type: "message",
        message: JSON.parse(String(event.data)) as TMessage,
      });
    };

    socket.onclose = (event) => {
      dispatch({ type: "closed", reason: event.reason || null });
      socketRef.current = null;
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [url]);

  const sendJson = useCallback((payload: unknown) => {
    const socket = socketRef.current;

    if (socket === null || socket.readyState !== WebSocket.OPEN) {
      return false;
    }

    socket.send(JSON.stringify(payload));
    return true;
  }, []);

  return {
    closeReason: state.closeReason,
    messages: state.messages,
    sendJson,
    status: state.status,
  };
}
