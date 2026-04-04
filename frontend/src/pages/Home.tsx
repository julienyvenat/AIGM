import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface Universe {
  id: string;
  name: string;
  description: string;
  image_url: string | null;
}

export function Home() {
  const [universes, setUniverses] = useState<Universe[]>([]);
  const [selectedUniverse, setSelectedUniverse] = useState<Universe | null>(null);
  const [characterName, setCharacterName] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`)
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

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUniverse || !characterName.trim()) return;

    // We navigate to Play with the state, or Play can fetch it
    navigate(`/play/${selectedUniverse.id}?character=${encodeURIComponent(characterName.trim())}`);
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
          <form onSubmit={handleConnect} className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Nom du personnage</label>
              <input
                type="text"
                required
                placeholder="Ex: Elara, Kael..."
                value={characterName}
                onChange={(e) => setCharacterName(e.target.value)}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={!characterName.trim()}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold rounded-md transition-colors"
            >
              Entrer dans l'aventure
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
