with open('frontend/src/pages/Dashboard.tsx', 'r') as f:
    content = f.read()

# Imports and interfaces
if 'interface Universe' not in content:
    content = content.replace(
        'interface Character {',
        'interface Universe {\n  id: string;\n  name: string;\n}\n\ninterface Character {'
    )

if 'const [universes, setUniverses] = useState<Universe[]>([]);' not in content:
    content = content.replace(
        'const [sessions, setSessions] = useState<GameSession[]>([]);',
        'const [sessions, setSessions] = useState<GameSession[]>([]);\n  const [universes, setUniverses] = useState<Universe[]>([]);\n  const [newCharName, setNewCharName] = useState("");\n  const [newCharUniverseId, setNewCharUniverseId] = useState("");\n  const [creatingChar, setCreatingChar] = useState(false);\n  const [charCreateError, setCharCreateError] = useState<string | null>(null);'
    )

# Fetching universes
if 'const universesResponse' not in content:
    fetchDataStr = """
        // Fetch Universes
        const universesResponse = await apiFetch(`${baseUrl}/universes`);
        if (universesResponse.ok) {
           const universesData = await universesResponse.json();
           setUniverses(universesData);
           if (universesData.length > 0) setNewCharUniverseId(universesData[0].id);
        }
"""
    content = content.replace(
        '// Fetch Game Sessions',
        fetchDataStr + '\n        // Fetch Game Sessions'
    )

# handleCreateCharacter
if 'const handleCreateCharacter' not in content:
    handleStr = """
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
    } catch (err: any) {
      setCharCreateError(err.message || "Erreur de création");
    } finally {
      setCreatingChar(false);
    }
  };
"""
    content = content.replace(
        'const getSessionForCharacter',
        handleStr + '\n  const getSessionForCharacter'
    )

# The UI
if 'Créer un Nouveau Personnage' not in content:
    uiStr = """
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
"""
    content = content.replace(
        '<div className="grid grid-cols-1 md:grid-cols-2 gap-8">',
        uiStr + '\n      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">'
    )

with open('frontend/src/pages/Dashboard.tsx', 'w') as f:
    f.write(content)
