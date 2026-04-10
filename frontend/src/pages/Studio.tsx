import { apiFetch } from "../utils/api";
import { useState, useEffect } from 'react';

export function Studio() {
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [universes, setUniverses] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [selectedUniverseId, setSelectedUniverseId] = useState<string | null>(null);

  const [npcs, setNpcs] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [locations, setLocations] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [factions, setFactions] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any

  // Modal states
  const [editModal, setEditModal] = useState<{type: 'npc'|'faction', data: any} | null>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  const fetchUniverses = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`);
      const data = await res.json();
      setUniverses(data);
      if (data.length > 0 && !selectedUniverseId) {
        setSelectedUniverseId(data[0].id);
      }
    } catch (e) { console.error(e); }
  };

  const fetchUniverseEntities = async (id: string) => {
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const [nRes, lRes, fRes] = await Promise.all([
        fetch(`${baseUrl}/universes/${id}/npcs`),
        fetch(`${baseUrl}/universes/${id}/locations`),
        fetch(`${baseUrl}/universes/${id}/factions`)
      ]);
      setNpcs(await nRes.json());
      setLocations(await lRes.json());
      setFactions(await fRes.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchUniverses();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedUniverseId) {
      fetchUniverseEntities(selectedUniverseId);
    }
  }, [selectedUniverseId]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/world/generate-from-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      await fetchUniverses();
      setSelectedUniverseId(data.universe.id);
      setPrompt('');
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editModal) return;

    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const endpoint = editModal.type === 'npc' ? `/npcs/${editModal.data.id}` : `/factions/${editModal.data.id}`;

      await fetch(`${baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editModal.data)
      });

      setEditModal(null);
      if (selectedUniverseId) fetchUniverseEntities(selectedUniverseId);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="h-full flex flex-col p-6 overflow-y-auto">
      <div className="mb-8 p-6 bg-gray-800 rounded-xl border border-emerald-500/30">
        <h2 className="text-2xl font-bold mb-4 text-emerald-400">Générateur d'Univers</h2>
        <div className="flex gap-4">
          <input
            type="text"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Décrivez votre monde en une phrase... (ex: Un monde cyberpunk dirigé par des vampires de silicium)"
            className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-emerald-500"
            disabled={generating}
          />
          <button
            onClick={handleGenerate}
            disabled={generating || !prompt.trim()}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-8 py-3 rounded-lg flex items-center justify-center min-w-[200px]"
          >
            {generating ? 'Création en cours...' : 'Forger l\'Univers'}
          </button>
        </div>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Sidebar Universes */}
        <div className="w-64 bg-gray-800 rounded-xl border border-gray-700 overflow-y-auto p-4 flex-shrink-0">
          <h3 className="text-lg font-bold mb-4 text-gray-300">Mes Univers</h3>
          <div className="flex flex-col gap-2">
            {universes.map(u => (
              <button
                key={u.id}
                onClick={() => setSelectedUniverseId(u.id)}
                className={`text-left p-3 rounded-lg transition-colors ${selectedUniverseId === u.id ? 'bg-emerald-900/50 border border-emerald-500 text-emerald-100' : 'bg-gray-900 border border-gray-700 text-gray-400 hover:bg-gray-700'}`}
              >
                <div className="font-bold truncate">{u.name}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Entities View */}
        {selectedUniverseId ? (
          <div className="flex-1 bg-gray-800 rounded-xl border border-gray-700 p-6 overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">{universes.find(u => u.id === selectedUniverseId)?.name}</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Factions */}
              <div>
                <h3 className="text-xl font-bold text-emerald-400 border-b border-gray-700 pb-2 mb-4">Factions</h3>
                <div className="flex flex-col gap-3">
                  {factions.map(f => (
                    <div key={f.id} className="bg-gray-900 p-4 rounded-lg border border-gray-700 group relative">
                      <div className="font-bold text-lg">{f.nom}</div>
                      <div className="text-sm text-gray-400 mt-1">{f.description}</div>
                      <button onClick={() => setEditModal({type: 'faction', data: {...f}})} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-emerald-400 hover:text-emerald-300">
                         Editer
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* NPCs */}
              <div>
                <h3 className="text-xl font-bold text-emerald-400 border-b border-gray-700 pb-2 mb-4">Personnages Notables</h3>
                <div className="flex flex-col gap-3">
                  {npcs.map(n => (
                    <div key={n.id} className="bg-gray-900 p-4 rounded-lg border border-gray-700 group relative">
                      <div className="font-bold text-lg">{n.nom}</div>
                      {n.faction && <div className="text-xs font-semibold text-emerald-500 mb-1">{n.faction}</div>}
                      <div className="text-sm text-gray-400 mt-1">{n.description}</div>
                      <button onClick={() => setEditModal({type: 'npc', data: {...n}})} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-emerald-400 hover:text-emerald-300">
                         Editer
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Locations */}
              <div className="col-span-1 lg:col-span-2">
                <h3 className="text-xl font-bold text-emerald-400 border-b border-gray-700 pb-2 mb-4">Lieux Importants</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {locations.map(l => (
                    <div key={l.id} className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <div className="font-bold text-lg">{l.nom}</div>
                      <div className="text-sm text-gray-400 mt-1">{l.description}</div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 italic">
            Sélectionnez un univers pour voir ses détails
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl border border-gray-600 p-6 w-full max-w-lg">
            <h2 className="text-2xl font-bold mb-4">Editer {editModal.type === 'npc' ? 'le PNJ' : 'la Faction'}</h2>
            <form onSubmit={handleSaveEdit} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nom</label>
                <input
                  type="text"
                  value={editModal.data.nom}
                  onChange={e => setEditModal({...editModal, data: {...editModal.data, nom: e.target.value}})}
                  className="w-full bg-gray-900 border border-gray-700 rounded p-2"
                />
              </div>

              {editModal.type === 'npc' && (
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Faction</label>
                  <input
                    type="text"
                    value={editModal.data.faction || ''}
                    onChange={e => setEditModal({...editModal, data: {...editModal.data, faction: e.target.value}})}
                    className="w-full bg-gray-900 border border-gray-700 rounded p-2"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-1">Description</label>
                <textarea
                  rows={5}
                  value={editModal.data.description}
                  onChange={e => setEditModal({...editModal, data: {...editModal.data, description: e.target.value}})}
                  className="w-full bg-gray-900 border border-gray-700 rounded p-2"
                />
              </div>

              <div className="flex justify-end gap-3 mt-4">
                <button type="button" onClick={() => setEditModal(null)} className="px-4 py-2 text-gray-400 hover:text-white">Annuler</button>
                <button type="submit" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded">Sauvegarder</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
