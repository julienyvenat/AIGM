import { useState, useRef, useEffect } from 'react';
import { useGameWebSocket } from './hooks/useGameWebSocket';

function App() {
  const [playerIdInput, setPlayerIdInput] = useState('');
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  const { isConnected, messages, sendMessage } = useGameWebSocket(playerId);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (playerIdInput.trim()) {
      setPlayerId(playerIdInput.trim());
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (chatInput.trim()) {
      sendMessage(chatInput.trim());
      setChatInput('');
    }
  };

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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
        <section className="w-1/3 flex flex-col border-r border-gray-700 bg-gray-800/50">
          {/* Chat Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-10 italic">
                {playerId ? 'En attente de messages...' : 'Connectez-vous pour commencer l\'aventure.'}
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col max-w-[85%] ${msg.sender === 'user' ? 'self-end' : 'self-start'}`}
                >
                  <div
                    className={`px-4 py-2 rounded-2xl ${
                      msg.sender === 'user'
                        ? 'bg-emerald-600 text-white rounded-br-sm'
                        : msg.type === 'narrator'
                          ? 'bg-purple-900 border border-purple-700 text-purple-100 rounded-bl-sm italic'
                          : msg.type === 'error'
                            ? 'bg-red-900 border border-red-700 text-red-100 rounded-bl-sm'
                            : 'bg-gray-700 text-gray-200 rounded-bl-sm'
                    }`}
                  >
                    {msg.sender === 'server' && (
                      <div className="text-xs font-semibold mb-1 opacity-70 flex justify-between">
                        <span>{msg.type === 'narrator' ? 'Narrateur' : msg.type === 'error' ? 'Erreur' : 'Système'}</span>
                        {msg.category && <span className="ml-2 uppercase text-[10px]">{msg.category}</span>}
                      </div>
                    )}
                    <div className="text-sm whitespace-pre-wrap">{msg.message}</div>
                  </div>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input Area */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700 bg-gray-800">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Que faites-vous ?"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={!isConnected}
                className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={!isConnected || !chatInput.trim()}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 disabled:bg-gray-600 disabled:text-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
              >
                Envoyer
              </button>
            </div>
          </form>
        </section>

        {/* Right Column: Future Map/Content (2/3) */}
        <section className="w-2/3 p-6 flex items-center justify-center bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwb2x5Z29uIHBvaW50cz0iMjAgMSAzOSAzOSAxIDM5IiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIi8+PC9zdmc+')]">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-500 mb-2">Carte / Plateau de Jeu</h2>
            <p className="text-gray-600 italic">Cet espace sera réservé à l'affichage visuel.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
