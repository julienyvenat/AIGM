import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { apiFetch } from '../utils/api';
import type {  Universe, GameSession, Character  } from '../types';


export const Dashboard = () => {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [sessions, setSessions] = useState<GameSession[]>([]);
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [newCharName, setNewCharName] = useState("");
  const [newCharUniverseId, setNewCharUniverseId] = useState("");
  const [creatingChar, setCreatingChar] = useState(false);
  const [charCreateError, setCharCreateError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

        // Fetch User's Characters
        const charsResponse = await apiFetch(`${baseUrl}/characters/`);

        if (!charsResponse.ok) {
           throw new Error('Failed to fetch characters');
        }

        const charsData = await charsResponse.json();
        setCharacters(charsData);


        // Fetch Universes
        const universesResponse = await apiFetch(`${baseUrl}/universes`);
        if (universesResponse.ok) {
           const universesData = await universesResponse.json();
           setUniverses(universesData);
           if (universesData.length > 0) setNewCharUniverseId(universesData[0].id);
        }

        // Fetch Game Sessions
        const sessionsResponse = await apiFetch(`${baseUrl}/sessions/`);

        if (!sessionsResponse.ok) {
           throw new Error('Failed to fetch game sessions');
        }

        const sessionsData = await sessionsResponse.json();
        setSessions(sessionsData);

      } catch (err: unknown) {
        if (err instanceof Error) {
           console.error(err);
        }
        setError('Impossible de charger les données du dashboard.');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchData();
    }
  }, [token]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };


  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    setCharCreateError(null);
    setCreatingChar(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await apiFetch(`${baseUrl}/characters/`, {
        method: 'POST',
        body: JSON.stringify({
          name: newCharName,
          universe_id: newCharUniverseId,
          description: "Créé depuis le dashboard"
        })
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la création du personnage");
      }

      const newChar = await response.json();
      setCharacters([...characters, newChar]);
      setNewCharName("");
    } catch (err: unknown) {
      setCharCreateError(err instanceof Error ? err.message : "Erreur de création");
    } finally {
      setCreatingChar(false);
    }
  };

  const getSessionForCharacter = (char: Character) => {
     return sessions.find((s: GameSession) => s.id === char.game_session_id);
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-300">Chargement du dashboard...</div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Bienvenue, {user?.username}</h1>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-md transition-colors"
        >
          Déconnexion
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-300 p-4 rounded mb-8">
          {error}
        </div>
      )}


      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
        <h2 className="text-2xl font-bold text-emerald-400 mb-4">Créer un Nouveau Personnage</h2>
        {charCreateError && <div className="text-red-400 mb-4">{charCreateError}</div>}
        <form onSubmit={handleCreateCharacter} className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-400 mb-1">Univers</label>
            <select
              value={newCharUniverseId}
              onChange={(e) => setNewCharUniverseId(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            >
              {universes.map(u => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-400 mb-1">Nom du personnage</label>
            <input
              type="text"
              value={newCharName}
              onChange={(e) => setNewCharName(e.target.value)}
              placeholder="Ex: Kael..."
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={creatingChar || !newCharName.trim() || universes.length === 0}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold rounded-md transition-colors w-full md:w-auto h-[42px]"
          >
            {creatingChar ? 'Création...' : 'Créer'}
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-2xl font-bold text-emerald-400 mb-4">Mes Personnages</h2>
          {characters.length === 0 ? (
            <p className="text-gray-400">Vous n'avez pas encore de personnage.</p>
          ) : (
            <ul className="space-y-4">
              {characters.map((char: Character) => {
                const session = getSessionForCharacter(char);
                return (
                  <li key={char.id} className="bg-gray-700 p-4 rounded-md flex justify-between items-center">
                    <div>
                      <h3 className="font-bold text-lg text-white">{char.name}</h3>
                      <p className="text-sm text-gray-400">
                        {session ? `En partie (Session #${session.id})` : 'Aucune partie active'}
                      </p>
                    </div>
                    {session && (
                      <button
                        onClick={() => navigate(`/play/${session.id}/${char.id}`)}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-md text-sm transition-colors"
                      >
                        Reprendre la partie
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
           <h2 className="text-2xl font-bold text-emerald-400 mb-4">Mes Parties (Sessions)</h2>
           {sessions.length === 0 ? (
            <p className="text-gray-400">Aucune partie en cours.</p>
          ) : (
            <ul className="space-y-4">
              {sessions.map((session: GameSession) => (
                 <li key={session.id} className="bg-gray-700 p-4 rounded-md">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-bold text-white">Session #{session.id}</h3>
                        <p className="text-sm text-gray-400">Univers: {session.universe?.name || session.universe_id}</p>
                      </div>
                      {session.universe?.game_system && (
                        <span className="bg-emerald-900/50 border border-emerald-500 text-emerald-300 text-xs px-2 py-1 rounded-full whitespace-nowrap">
                          Système : {session.universe.game_system.name}
                        </span>
                      )}
                    </div>
                 </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};
