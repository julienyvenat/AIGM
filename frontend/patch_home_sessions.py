with open('frontend/src/pages/Home.tsx', 'r') as f:
    content = f.read()

# Replace interface and states
if 'interface Character' not in content:
    content = content.replace(
        'interface Universe {',
        'interface Character {\n  id: string;\n  name: string;\n  universe_id: string;\n}\n\ninterface Universe {'
    )

if 'const [myCharacters' not in content:
    content = content.replace(
        "const [characterName, setCharacterName] = useState('');",
        "const [myCharacters, setMyCharacters] = useState<Character[]>([]);\n  const [selectedCharacterId, setSelectedCharacterId] = useState('');\n  const [actionError, setActionError] = useState<string | null>(null);\n  const [isCreating, setIsCreating] = useState(false);"
    )

if 'apiFetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/characters/`)' not in content:
    fetchStr = """  useEffect(() => {
    // Fetch characters too
    apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/`)
      .then(res => res.json())
      .then(data => setMyCharacters(data))
      .catch(err => console.error("Failed to load characters", err));
  }, []);"""
    content = content.replace('const handleConnect =', fetchStr + '\n\n  const handleConnect =')

if 'const availableCharacters =' not in content:
    content = content.replace('const handleConnect =', """
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

  const handleConnect =""")

# Replace UI
old_form = """<form onSubmit={handleConnect} className="flex flex-col gap-4">
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
          </form>"""

new_form = """{actionError && <div className="text-red-400 mb-4 text-sm">{actionError}</div>}
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
          </form>"""

content = content.replace(old_form, new_form)

# Remove unused handleConnect
import re
content = re.sub(r'const handleConnect = async \(e: React.FormEvent\) => \{[\s\S]*?navigate\(`/play/\$\{selectedUniverse.id\}\?character=\$\{encodeURIComponent\(characterName\.trim\(\)\)\}`\);\n  \};', '', content)

# Remove unused characterName state
content = content.replace("  const [characterName, setCharacterName] = useState('');\n", "")

with open('frontend/src/pages/Home.tsx', 'w') as f:
    f.write(content)
