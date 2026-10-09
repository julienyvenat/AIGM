import { useState, useEffect } from 'react';
import { apiFetch } from '../utils/api';
import type { Universe, Character } from '../types';

interface CharacterCreationFormProps {
  universes: Universe[];
  onSuccess: (newChar: Character) => void;
}

export const CharacterCreationForm = ({ universes, onSuccess }: CharacterCreationFormProps) => {
  const [newCharName, setNewCharName] = useState("");
  const [newCharUniverseId, setNewCharUniverseId] = useState("");
  const [stats, setStats] = useState<Record<string, string | number>>({});
  const [creatingChar, setCreatingChar] = useState(false);
  const [charCreateError, setCharCreateError] = useState<string | null>(null);

  useEffect(() => {
    if (universes.length > 0 && !newCharUniverseId) {
      setNewCharUniverseId(universes[0].id);
    }
  }, [universes, newCharUniverseId]);

  // Reset stats when universe changes
  useEffect(() => {
    setStats({});
  }, [newCharUniverseId]);

  const selectedUniverse = universes.find(u => u.id === newCharUniverseId);
  const schema = selectedUniverse?.game_system?.character_schema || {};

  const handleStatChange = (key: string, value: string | number) => {
    setStats(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    setCharCreateError(null);
    setCreatingChar(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      // character_schema only maps each stat key to a human-readable description
      // (e.g. "STR": "Force - Puissance physique"), it carries no type information.
      // Every stat is entered as a number (see the "number" inputs below), so
      // convert to a number here and only fall back to the raw string if that fails.
      const formattedStats: Record<string, string | number> = {};
      Object.keys(schema).forEach(key => {
         const rawValue = stats[key];
         const numericValue = Number(rawValue);
         formattedStats[key] = rawValue !== undefined && rawValue !== '' && !Number.isNaN(numericValue)
           ? numericValue
           : (rawValue || '');
      });

      const response = await apiFetch(`${baseUrl}/characters/`, {
        method: 'POST',
        body: JSON.stringify({
          name: newCharName,
          universe_id: newCharUniverseId,
          description: "Créé depuis le dashboard",
          stats: formattedStats
        })
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || "Erreur lors de la création du personnage");
      }

      const newChar = await response.json();
      onSuccess(newChar);
      setNewCharName("");
      setStats({});
    } catch (err: unknown) {
      setCharCreateError(err instanceof Error ? err.message : "Erreur de création");
    } finally {
      setCreatingChar(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-8">
      <h2 className="text-2xl font-bold text-emerald-400 mb-4">Créer un Nouveau Personnage</h2>
      {charCreateError && <div className="text-red-400 mb-4">{charCreateError}</div>}
      <form onSubmit={handleCreateCharacter} className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row gap-4">
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
        </div>

        {Object.keys(schema).length > 0 && (
          <div className="mt-4">
             <h3 className="text-lg font-bold text-gray-300 mb-3 border-b border-gray-700 pb-2">Statistiques</h3>
             <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                 {Object.entries(schema).map(([key, description]) => (
                    <div key={key} className="flex flex-col">
                       <label className="block text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider" title={String(description)}>{key}</label>
                       <input
                          type="number"
                          value={stats[key] || ''}
                          onChange={(e) => handleStatChange(key, e.target.value)}
                          className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                          required
                       />
                    </div>
                 ))}
             </div>
          </div>
        )}

        <div className="mt-4 flex justify-end">
            <button
              type="submit"
              disabled={creatingChar || !newCharName.trim() || universes.length === 0}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold rounded-md transition-colors"
            >
              {creatingChar ? 'Création...' : 'Créer le personnage'}
            </button>
        </div>
      </form>
    </div>
  );
};
