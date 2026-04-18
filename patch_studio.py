import re

with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

# Add gameSystems state
if "const [gameSystems" not in content:
    content = content.replace(
        "const [factions, setFactions] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any",
        "const [factions, setFactions] = useState<any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any\n  const [gameSystems, setGameSystems] = useState<any[]>([]);\n  const [selectedSystemId, setSelectedSystemId] = useState<string>('');"
    )

# Add fetchGameSystems
fetch_systems = """
  const fetchGameSystems = async () => {
    try {
      const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/game-systems`);
      const data = await res.json();
      setGameSystems(data);
      if (data.length > 0 && !selectedSystemId) {
        setSelectedSystemId(data[0].id);
      }
    } catch (e) { console.error(e); }
  };
"""

if "const fetchGameSystems" not in content:
    content = content.replace("const fetchUniverses", fetch_systems + "\n  const fetchUniverses")

# Add fetchGameSystems to useEffect
if "fetchGameSystems();" not in content:
    content = content.replace("fetchUniverses();", "fetchGameSystems();\n    fetchUniverses();")


# Update handleGenerate payload
content = content.replace(
    "body: JSON.stringify({ prompt })",
    "body: JSON.stringify({ prompt, game_system_id: selectedSystemId })"
)

# Update UI with the new selector
new_ui = """
      <div className="mb-8 p-6 bg-gray-800 rounded-xl border border-emerald-500/30">
        <h2 className="text-2xl font-bold mb-4 text-emerald-400">Générateur d'Univers</h2>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-400 mb-1">Système de jeu</label>
          <select
            value={selectedSystemId}
            onChange={(e) => setSelectedSystemId(e.target.value)}
            className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500"
            disabled={generating}
          >
            {gameSystems.map(gs => (
              <option key={gs.id} value={gs.id}>{gs.name}</option>
            ))}
          </select>
          {selectedSystemId && gameSystems.find(gs => gs.id === selectedSystemId)?.description && (
            <p className="mt-2 text-sm text-gray-400 italic">
              {gameSystems.find(gs => gs.id === selectedSystemId)?.description}
            </p>
          )}
        </div>

        <div className="flex gap-4">
"""

content = content.replace(
"""      <div className="mb-8 p-6 bg-gray-800 rounded-xl border border-emerald-500/30">
        <h2 className="text-2xl font-bold mb-4 text-emerald-400">Générateur d'Univers</h2>
        <div className="flex gap-4">""", new_ui)

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
