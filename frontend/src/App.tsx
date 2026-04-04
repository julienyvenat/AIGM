import { useState } from 'react';
import { useGameWebSocket } from './hooks/useGameWebSocket';
import { ChatPanel } from './components/ChatPanel';
import { BattleMap } from './components/BattleMap';
import { SceneViewer } from './components/SceneViewer';
import { CharacterManager } from './components/CharacterManager';
import { CharacterSidePanel } from './components/CharacterSidePanel';
import { CharacterModal } from './components/CharacterModal';

export interface Character {
  id: string;
  name: string;
  hp: number;
  max_hp: number;
  armor_class: number;
  speed: number;
  reference_portrait_url: string | null;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  level: number;
  experience: number;
  known_spells: any[];
  spell_slots: Record<string, any>;
  class_resources: Record<string, any>;
}

function App() {
  const [playerIdInput, setPlayerIdInput] = useState('');
  const [character, setCharacter] = useState<Character | null>(null);
  const [showCharacterManager, setShowCharacterManager] = useState(false);
  const [activePlayerId, setActivePlayerId] = useState<string | null>(null);
  const [isCharacterModalOpen, setIsCharacterModalOpen] = useState(false);

  const handleStatsUpdate = (updatedCharacter: Partial<Character>) => {
    setCharacter(prev => prev ? { ...prev, ...updatedCharacter } as Character : updatedCharacter as Character);
  };

  const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(activePlayerId, handleStatsUpdate);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerIdInput.trim()) return;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/by-name/${playerIdInput.trim()}`);
      if (!response.ok) {
          console.error("Failed to fetch character");
          return;
      }
      const charData = await response.json();

      setCharacter(charData);

      if (!charData.reference_portrait_url) {
        setShowCharacterManager(true);
        setActivePlayerId(null); // Wait for character manager to complete before connecting WS
      } else {
        setShowCharacterManager(false);
        setActivePlayerId(charData.id); // Connect WS immediately if portrait exists
      }
    } catch (error) {
      console.error("Error fetching character:", error);
    }
  };

  const handleCharacterManagerComplete = (updatedCharacter: Character) => {
    setCharacter(updatedCharacter);
    setShowCharacterManager(false);
    setActivePlayerId(updatedCharacter.id); // Now we connect to the WebSocket
  };

import { Routes, Route, Link } from 'react-router-dom';
import { Home } from './pages/Home';
import { Studio } from './pages/Studio';
import { Play } from './pages/Play';

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Global Header */}
      <header className="p-4 border-b border-gray-700 bg-gray-800 flex justify-between items-center shrink-0">
        <Link to="/" className="text-xl font-bold text-emerald-400 hover:text-emerald-300">
          RPG AI Game Master
        </Link>
        <nav className="flex gap-4">
          <Link to="/" className="text-gray-300 hover:text-white font-medium">Lobby</Link>
          <Link to="/studio" className="text-gray-300 hover:text-white font-medium">Studio Pro</Link>
        </nav>
      </header>

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative">
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

        {character && isConnected && (
           <CharacterSidePanel character={character} onOpenModal={() => setIsCharacterModalOpen(true)} />
        )}

        {/* Modals */}
        {isCharacterModalOpen && character && (
           <CharacterModal character={character} onClose={() => setIsCharacterModalOpen(false)} />
        )}

        {showCharacterManager && character && (
          <CharacterManager
            character={character}
            onComplete={handleCharacterManagerComplete}
          />
        )}
      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/play/:universeId" element={<Play />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
