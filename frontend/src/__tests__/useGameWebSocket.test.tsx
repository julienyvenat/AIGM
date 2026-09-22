import { renderHook, act, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { AuthContext } from '../context/AuthContext';

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;

  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: ((e: { code: number; reason: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  sent: string[] = [];
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = 3;
  }
}

function wrapper({ children }: { children: ReactNode }) {
  return (
    <AuthContext.Provider
      value={{
        token: 'fake-token',
        user: null,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
      }}
    >
      <MemoryRouter>{children}</MemoryRouter>
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket);
});

test('grid dimensions default to 15x15 until the backend says otherwise', () => {
  const { result } = renderHook(() => useGameWebSocket('player-1', 'session-1'), { wrapper });

  expect(result.current.gridWidth).toBe(15);
  expect(result.current.gridHeight).toBe(15);
});

test('a combat_state message updates the grid dimensions from GameSession data', async () => {
  const { result } = renderHook(() => useGameWebSocket('player-1', 'session-1'), { wrapper });
  const ws = MockWebSocket.instances[0];

  act(() => {
    ws.onmessage?.({
      data: JSON.stringify({ type: 'combat_state', entities: [], grid_width: 20, grid_height: 12 }),
    });
  });

  await waitFor(() => {
    expect(result.current.gridWidth).toBe(20);
    expect(result.current.gridHeight).toBe(12);
  });
});

test('a combat_state message without grid dimensions leaves the current size alone', async () => {
  const { result } = renderHook(() => useGameWebSocket('player-1', 'session-1'), { wrapper });
  const ws = MockWebSocket.instances[0];

  act(() => {
    ws.onmessage?.({ data: JSON.stringify({ type: 'combat_state', entities: [] }) });
  });

  await waitFor(() => {
    expect(result.current.entities).toEqual([]);
  });
  expect(result.current.gridWidth).toBe(15);
  expect(result.current.gridHeight).toBe(15);
});

test('sendMoveEntity sends a move_entity UI_ACTION over the socket', () => {
  const { result } = renderHook(() => useGameWebSocket('player-1', 'session-1'), { wrapper });
  const ws = MockWebSocket.instances[0];

  act(() => {
    result.current.sendMoveEntity('npc-42', 3, 4);
  });

  expect(ws.sent).toHaveLength(1);
  expect(JSON.parse(ws.sent[0])).toEqual({
    type: 'UI_ACTION',
    action: 'move_entity',
    entity_id: 'npc-42',
    x: 3,
    y: 4,
  });
});
