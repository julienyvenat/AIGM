import { useState } from 'react';
import { useGameWebSocket } from './hooks/useGameWebSocket';
import { ChatPanel } from './components/ChatPanel';
import { BattleMap } from './components/BattleMap';
import { SceneViewer } from './components/SceneViewer';

function App() {
  const [playerIdInput, setPlayerIdInput] = useState('');
  const [playerId, setPlayerId] = useState<string | null>(null);

  const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(playerId);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (playerIdInput.trim()) {
      setPlayerId(playerIdInput.trim());
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Header / Connection Bar */}
      <header className="p-4 border-b border-gray-700 bg-gray-800 flex justify-between items-center shrink-0">
        <h1 className="text-xl font-bold text-emerald-400">RPG AI Game Master</h1>

        <form onSubmit={handleConnect} className="flex gap-2 items-center">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]'}`}></span>
            <span className="text-sm font-medium text-gray-300">
              {isConnected ? 'Connecté' : 'Déconnecté'}
            </span>
          </div>

          <input
            type="text"
            placeholder="Entrez votre nom..."
            value={playerIdInput}
            onChange={(e) => setPlayerIdInput(e.target.value)}
            className="px-3 py-1.5 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm ml-4"
          />
          <button
            type="submit"
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-medium rounded-md transition-colors text-sm"
          >
            Se connecter
          </button>
        </form>
      </header>

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Column: Chat (1/3) */}
        <section className="w-1/3 border-r border-gray-700 bg-gray-800/50 relative">
           {!isConnected ? (
              <div className="absolute inset-0 flex items-center justify-center p-4">
                 <div className="text-center text-gray-500 mt-10 italic">
                    Connectez-vous pour commencer l'aventure.
                 </div>
              </div>
           ) : (
             <ChatPanel messages={messages} sendMessage={sendMessage} />
           )}
        </section>

        {/* Right Column: Future Map/Content (2/3) */}
        <section className="w-2/3 p-6 flex flex-col items-center justify-center relative bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwb2x5Z29uIHBvaW50cz0iMjAgMSAzOSAzOSAxIDM5IiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIi8+PC9zdmc+')]">
          <BattleMap entities={entities} />

          {currentSceneImage && (
            <SceneViewer imageUrl={currentSceneImage} onClose={clearSceneImage} />
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
