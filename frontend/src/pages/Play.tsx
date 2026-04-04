import { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { ChatPanel } from '../components/ChatPanel';
import { BattleMap } from '../components/BattleMap';
import { SceneViewer } from '../components/SceneViewer';
import { CharacterManager } from '../components/CharacterManager';
import { CharacterSidePanel } from '../components/CharacterSidePanel';
import { CharacterModal } from '../components/CharacterModal';

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

export function Play() {
  const { universeId } = useParams<{ universeId: string }>();
  const [searchParams] = useSearchParams();
  const characterName = searchParams.get('character');
  const navigate = useNavigate();

  const [character, setCharacter] = useState<Character | null>(null);
  const [showCharacterManager, setShowCharacterManager] = useState(false);
  const [activePlayerId, setActivePlayerId] = useState<string | null>(null);
  const [isCharacterModalOpen, setIsCharacterModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const handleStatsUpdate = useCallback((updatedCharacter: Partial<Character>) => {
    setCharacter(prev => prev ? { ...prev, ...updatedCharacter } as Character : updatedCharacter as Character);
  }, []);

  // We pass universeId down to WebSocket hook so it connects properly
  const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(activePlayerId, universeId || null, handleStatsUpdate);

  useEffect(() => {
    if (!universeId || !characterName) {
      navigate('/');
      return;
    }

    const fetchCharacter = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes/${universeId}/characters/by-name/${encodeURIComponent(characterName)}`);
        if (!response.ok) {
            console.error("Failed to fetch character");
            navigate('/');
            return;
        }
        const charData = await response.json();

        setCharacter(charData);

        if (!charData.reference_portrait_url) {
          setShowCharacterManager(true);
          setActivePlayerId(null);
        } else {
          setShowCharacterManager(false);
          setActivePlayerId(charData.id);
        }
      } catch (error) {
        console.error("Error fetching character:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCharacter();
  }, [universeId, characterName, navigate]);

  const handleCharacterManagerComplete = (updatedCharacter: Character) => {
    setCharacter(updatedCharacter);
    setShowCharacterManager(false);
    setActivePlayerId(updatedCharacter.id);
  };

  if (loading) {
    return <div className="h-full flex items-center justify-center text-gray-500">Connexion à l'univers...</div>;
  }

  return (
    <div className="h-full flex flex-col relative">
      {/* Mini-header for character stats */}
      {character && (
        <div className="bg-gray-800/80 border-b border-gray-700 p-2 flex justify-between items-center z-10 shrink-0">
           <div className="flex items-center gap-2">
             <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
             <span className="text-xs text-gray-400">{isConnected ? 'En ligne' : 'Déconnecté'}</span>
           </div>
           <div className="flex items-center gap-4 bg-gray-900 px-3 py-1 rounded-full border border-gray-700">
            <span className="font-bold text-gray-200 text-sm">{character.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">HP</span>
              <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all duration-300"
                  style={{ width: `${Math.max(0, Math.min(100, ((character.hp || 0) / (character.max_hp || 1)) * 100))}%` }}
                />
              </div>
              <span className="text-xs font-bold text-red-400">{character.hp || 0}/{character.max_hp || 0}</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Chat (1/3) */}
        <section className="w-1/3 border-r border-gray-700 bg-gray-800/50 relative">
           {!isConnected ? (
              <div className="absolute inset-0 flex items-center justify-center p-4">
                 <div className="text-center text-gray-500 italic">
                    Connexion au Game Master...
                 </div>
              </div>
           ) : (
             <ChatPanel messages={messages} sendMessage={sendMessage} />
           )}
        </section>

        {/* Right Column: Map/Content (2/3) */}
        <section className="w-2/3 p-6 flex flex-col items-center justify-center relative bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgweiIgZmlsbD0ibm9uZSIvPjxwb2x5Z29uIHBvaW50cz0iMjAgMSAzOSAzOSAxIDM5IiBmaWxsPSJyZ2JhKDI1NSwyNTUsMjU1LDAuMDMpIi8+PC9zdmc+')]">
          <BattleMap entities={entities} />

          {currentSceneImage && (
            <SceneViewer imageUrl={currentSceneImage} onClose={clearSceneImage} />
          )}
        </section>

        {/* Side Panel for Character */}
        {character && isConnected && (
           <CharacterSidePanel character={character} onOpenModal={() => setIsCharacterModalOpen(true)} />
        )}
      </div>

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
    </div>
  );
}
