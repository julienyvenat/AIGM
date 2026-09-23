import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import { ChatPanel } from '../components/ChatPanel';
import { BattleMap } from '../components/BattleMap';
import { SceneViewer } from '../components/SceneViewer';
import { CharacterManager } from '../components/CharacterManager';
import { CharacterSidePanel } from '../components/CharacterSidePanel';
import { CharacterModal } from '../components/CharacterModal';
import { RulebookModal } from '../components/RulebookModal';
import type { GameSession } from '../types';
import { useAuth } from '../hooks/useAuth';
import type { Character } from '../types';


export function Play() {
  const { sessionId, characterId } = useParams<{ sessionId: string, characterId: string }>();
  const navigate = useNavigate();
  const { token, user } = useAuth();

  const [character, setCharacter] = useState<Character | null>(null);
  const [showCharacterManager, setShowCharacterManager] = useState(false);
  const [showRulebook, setShowRulebook] = useState(false);
  const [sessionContext, setSessionContext] = useState<GameSession | null>(null);
  const [activePlayerId, setActivePlayerId] = useState<string | null>(characterId || null);
  const [isCharacterModalOpen, setIsCharacterModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [voiceToggleLoading, setVoiceToggleLoading] = useState(false);

  const handleStatsUpdate = useCallback((updatedCharacter: Partial<Character>) => {
    setCharacter(prev => prev ? { ...prev, ...updatedCharacter } as Character : updatedCharacter as Character);
  }, []);

  const {
    isConnected,
    messages,
    sendMessage,
    sendAction,
    sendMoveEntity,
    entities,
    currentSceneImage,
    clearSceneImage,
    battlemapImageUrl,
    gridWidth,
    gridHeight,
  } = useGameWebSocket(activePlayerId, sessionId || null, handleStatsUpdate);

  useEffect(() => {
    if (!sessionId || !characterId || !token) {
      navigate('/dashboard');
      return;
    }

    const fetchCharacter = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/${characterId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
            console.error("Failed to fetch character");
            navigate('/dashboard');
            return;
        }
        const charData = await response.json();

        setCharacter(charData);

      // Fetch Session Context for Rulebook
      try {
        const sessionRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/sessions/${sessionId}/context`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (sessionRes.ok) {
          setSessionContext(await sessionRes.json());
        }
      } catch (e) {
        console.error("Failed to fetch session context", e);
      }


        if (!charData.reference_portrait_url) {
          setShowCharacterManager(true);
        } else {
          setShowCharacterManager(false);
        }
      } catch (error) {
        console.error("Error fetching character:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchCharacter();
  }, [sessionId, characterId, navigate, token]);

  const handleCharacterManagerComplete = (updatedCharacter: Character) => {
    setCharacter(updatedCharacter);
    setShowCharacterManager(false);
    setActivePlayerId(updatedCharacter.id);
  };

  // Only the session host can toggle voice on/off (enforced backend-side by
  // PUT /sessions/{id}/voice, host_id check) -- this costs a real OpenAI TTS
  // API call per narrator reply once enabled, so it isn't exposed as a
  // free-for-all switch.
  const isHost = !!user?.sub && !!sessionContext?.host_id && String(sessionContext.host_id) === String(user.sub);

  const handleToggleVoice = async () => {
    if (!sessionId || !sessionContext || !token) return;
    const nextValue = !sessionContext.voice_enabled;
    setVoiceToggleLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/sessions/${sessionId}/voice`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ voice_enabled: nextValue })
      });
      if (!response.ok) {
        console.error('Failed to toggle voice narration');
        return;
      }
      const data = await response.json();
      setSessionContext(prev => prev ? { ...prev, voice_enabled: data.voice_enabled } : prev);
    } catch (error) {
      console.error('Error toggling voice narration:', error);
    } finally {
      setVoiceToggleLoading(false);
    }
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
             {sessionContext?.universe?.game_system && (
               <button
                 onClick={() => setShowRulebook(true)}
                 className="p-1.5 bg-emerald-900/50 hover:bg-emerald-800 border border-emerald-500/50 rounded text-emerald-400 transition-colors mr-2"
                 title="Livre de règles"
               >
                 <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>
               </button>
             )}

             {sessionContext && (
               isHost ? (
                 <button
                   onClick={handleToggleVoice}
                   disabled={voiceToggleLoading}
                   className={`p-1.5 border rounded transition-colors mr-2 disabled:opacity-50 ${
                     sessionContext.voice_enabled
                       ? 'bg-emerald-900/50 hover:bg-emerald-800 border-emerald-500/50 text-emerald-400'
                       : 'bg-gray-800/50 hover:bg-gray-700 border-gray-600 text-gray-400'
                   }`}
                   title={sessionContext.voice_enabled ? 'Narration vocale activée (cliquer pour désactiver)' : 'Narration vocale désactivée (cliquer pour activer)'}
                   aria-label="Basculer la narration vocale"
                 >
                   {sessionContext.voice_enabled ? (
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
                   ) : (
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
                   )}
                 </button>
               ) : (
                 <span
                   className="p-1.5 rounded text-gray-500 mr-2"
                   title={sessionContext.voice_enabled ? 'Narration vocale activée par le MJ' : 'Narration vocale désactivée'}
                 >
                   {sessionContext.voice_enabled ? (
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                   ) : (
                     <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>
                   )}
                 </span>
               )
             )}

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
          <BattleMap
            entities={entities}
            battlemapImageUrl={battlemapImageUrl}
            gridWidth={gridWidth}
            gridHeight={gridHeight}
            onMoveEntity={sendMoveEntity}
          />

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
         <CharacterModal character={character} onClose={() => setIsCharacterModalOpen(false)} sendAction={sendAction} />
      )}

      {showCharacterManager && character && (
        <CharacterManager
          character={character}
          onComplete={handleCharacterManagerComplete}
        />
      )}

      {showRulebook && sessionContext?.universe?.game_system && (
        <RulebookModal
          system={sessionContext.universe.game_system}
          onClose={() => setShowRulebook(false)}
        />
      )}
    </div>

  );
}
