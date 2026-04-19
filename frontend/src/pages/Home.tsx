import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../utils/api';
import type {  Universe, Character  } from '../types';


export function Home() {
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverse, setSelectedUniverse] = useState<Universe | null>(null);
  const [myCharacters, setMyCharacters] = useState<Character[]>([]);
  const [selectedCharacterId, setSelectedCharacterId] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`)
      .then(res => res.json())
      .then(data => {
        setUniverses(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load universes", err);
        setLoading(false);
      });
  }, []);

    useEffect(() => {
    // Fetch characters too
    apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/`)
      .then(res => res.json())
      .then(data => setMyCharacters(data))
      .catch(err => console.error("Failed to load characters", err));
  }, []);


  const availableCharacters = selectedUniverse
    ? myCharacters.filter(c => c.universe_id === selectedUniverse.id)
    : [];

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionError(null);

    if (!selectedUniverse || !selectedCharacterId) {
      setActionError("Veuillez sélectionner un personnage.");
      return;
    }

    if (availableCharacters.length === 0) {
      setActionError("Vous devez d'abord créer un personnage pour cet univers depuis le Dashboard.");
      return;
    }

    setIsCreating(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // 1. Create session
      const sessionRes = await apiFetch(`${baseUrl}/sessions/`, {
        method: 'POST',
        body: JSON.stringify({ universe_id: selectedUniverse.id })
      });

      if (!sessionRes.ok) throw new Error("Erreur de création de session");
      const sessionData = await sessionRes.json();

      // 2. Join session
      const joinRes = await apiFetch(`${baseUrl}/sessions/${sessionData.id}/join`, {
        method: 'POST',
        body: JSON.stringify({ character_id: selectedCharacterId })
      });

      if (!joinRes.ok) {
         const errData = await joinRes.json();
         throw new Error(errData.detail || "Erreur lors de la jointure");
      }

      // 3. Navigate to play
      navigate(`/play/${sessionData.id}/${selectedCharacterId}`);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setActionError(err.message);
      } else {
        setActionError("Une erreur inattendue s'est produite.");
      }
    } finally {
      setIsCreating(false);
    }
  };



  return (
    <div className="p-8 flex flex-col items-center h-full overflow-y-auto">
      <h1 className="text-3xl font-bold mb-8 text-emerald-400">Sélectionnez un Univers</h1>

      {loading ? (
        <div className="text-gray-400">Chargement des univers...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 w-full max-w-6xl mb-12">
          {universes.length === 0 ? (
            <div className="col-span-full text-center text-gray-500 italic">
              Aucun univers n'existe encore. Allez dans le Studio Pro pour en créer un !
            </div>
          ) : (
            universes.map(u => (
              <div
                key={u.id}
                onClick={() => setSelectedUniverse(u)}
                className={`bg-gray-800 border-2 rounded-xl overflow-hidden cursor-pointer transition-all hover:scale-105 ${selectedUniverse?.id === u.id ? 'border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : 'border-gray-700 hover:border-gray-500'}`}
              >
                <div className="h-48 bg-gray-700 relative">
                  {u.image_url ? (
                    <img src={u.image_url.startsWith('http') ? u.image_url : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${u.image_url}`} alt={u.name} className="w-full h-full object-cover" />
                  ) : (
                     <div className="w-full h-full flex items-center justify-center text-gray-500">Pas d'image</div>
                  )}
                  {selectedUniverse?.id === u.id && (
                    <div className="absolute top-2 right-2 bg-emerald-500 text-white rounded-full p-1">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                    </div>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="text-xl font-bold mb-2">{u.name}</h3>
                  <p className="text-sm text-gray-400 line-clamp-3">{u.description}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {selectedUniverse && (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 w-full max-w-md animate-fade-in-up">
          <h2 className="text-xl font-bold mb-4 text-center">Rejoindre {selectedUniverse.name}</h2>
          {actionError && <div className="text-red-400 mb-4 text-sm">{actionError}</div>}
          <form onSubmit={handleCreateSession} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Jouer avec :</label>
              {availableCharacters.length > 0 ? (
                <select
                  value={selectedCharacterId}
                  onChange={(e) => setSelectedCharacterId(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                >
                  <option value="" disabled>Sélectionnez un de vos personnages</option>
                  {availableCharacters.map(char => (
                    <option key={char.id} value={char.id}>{char.name}</option>
                  ))}
                </select>
              ) : (
                <div className="text-amber-400 text-sm bg-amber-900/30 p-3 rounded">
                  Vous devez d'abord créer un personnage pour cet univers depuis le Dashboard.
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={isCreating || availableCharacters.length === 0 || !selectedCharacterId}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold rounded-md transition-colors"
            >
              {isCreating ? "Création..." : "Lancer une nouvelle session"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
