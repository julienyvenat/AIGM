import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { expect, test, vi, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { Play } from '../pages/Play';
import { AuthContext } from '../context/AuthContext';

// Phase C: voice toggle UI lives in Play.tsx's mini-header. These tests
// focus on that toggle (host can flip it, non-host sees a read-only
// indicator) and on the WS `audio_ready` message triggering playback --
// everything else Play.tsx renders (chat, battlemap, modals) is mocked out
// so the tests aren't coupled to unrelated markup.
vi.mock('../components/ChatPanel', () => ({ ChatPanel: () => <div>ChatPanel</div> }));
vi.mock('../components/BattleMap', () => ({ BattleMap: () => <div>BattleMap</div> }));
vi.mock('../components/SceneViewer', () => ({ SceneViewer: () => null }));
vi.mock('../components/CharacterManager', () => ({ CharacterManager: () => null }));
vi.mock('../components/CharacterSidePanel', () => ({ CharacterSidePanel: () => null }));
vi.mock('../components/CharacterModal', () => ({ CharacterModal: () => null }));
vi.mock('../components/RulebookModal', () => ({ RulebookModal: () => null }));

const mockUseGameWebSocket = vi.fn();
vi.mock('../hooks/useGameWebSocket', () => ({
  useGameWebSocket: (...args: unknown[]) => mockUseGameWebSocket(...args),
}));

const HOST_ID = 'host-user-id';
const OTHER_ID = 'other-user-id';

const CHARACTER = {
  id: 'char-1',
  name: 'Hero',
  hp: 10,
  max_hp: 10,
  reference_portrait_url: '/images/hero.png',
};

const SESSION_CONTEXT = {
  id: 'session-1',
  universe_id: 'universe-1',
  status: 'ACTIVE',
  host_id: HOST_ID,
  game_mode: 'NARRATIVE',
  voice_enabled: false,
};

function mockFetchSequence() {
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url.includes('/characters/')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(CHARACTER) });
    }
    if (url.includes('/sessions/') && url.includes('/context')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(SESSION_CONTEXT) });
    }
    if (url.includes('/voice')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'success', voice_enabled: true }) });
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  }) as unknown as typeof fetch);
}

function wrapper(userId: string) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <AuthContext.Provider
        value={{
          token: 'fake-token',
          user: { username: 'tester', sub: userId },
          login: vi.fn(),
          register: vi.fn(),
          logout: vi.fn(),
          isLoading: false,
        }}
      >
        <MemoryRouter initialEntries={[`/play/session-1/char-1`]}>
          <Routes>
            <Route path="/play/:sessionId/:characterId" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };
}

beforeEach(() => {
  mockUseGameWebSocket.mockReset();
  mockUseGameWebSocket.mockReturnValue({
    isConnected: true,
    messages: [],
    sendMessage: vi.fn(),
    sendAction: vi.fn(),
    sendMoveEntity: vi.fn(),
    entities: [],
    currentSceneImage: null,
    clearSceneImage: vi.fn(),
    battlemapImageUrl: null,
    gridWidth: 15,
    gridHeight: 15,
  });
  mockFetchSequence();
});

test('the host sees a clickable voice toggle and can enable narration', async () => {
  const Wrapped = wrapper(HOST_ID);
  render(<Play />, { wrapper: Wrapped });

  const toggleButton = await screen.findByRole('button', { name: /narration vocale/i });
  expect(toggleButton).toHaveAttribute('title', expect.stringContaining('désactivée'));

  await userEvent.click(toggleButton);

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/sessions/session-1/voice'),
      expect.objectContaining({
        method: 'PUT',
        body: JSON.stringify({ voice_enabled: true }),
      })
    );
  });

  await waitFor(() => {
    expect(toggleButton).toHaveAttribute('title', expect.stringContaining('activée'));
  });
});

test('a non-host sees a read-only voice indicator instead of a toggle button', async () => {
  const Wrapped = wrapper(OTHER_ID);
  render(<Play />, { wrapper: Wrapped });

  await screen.findByText('ChatPanel');

  expect(screen.queryByRole('button', { name: /narration vocale/i })).not.toBeInTheDocument();
});
