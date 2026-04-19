with open("frontend/src/pages/Play.tsx", "r") as f:
    content = f.read()

# Add imports
if "RulebookModal" not in content:
    content = content.replace("import { CharacterModal } from '../components/CharacterModal';", "import { CharacterModal } from '../components/CharacterModal';\nimport { RulebookModal } from '../components/RulebookModal';\nimport { GameSession } from '../types';")

# Add state for GameSession Context
if "const [sessionContext" not in content:
    content = content.replace(
        "const [showCharacterManager, setShowCharacterManager] = useState(false);",
        "const [showCharacterManager, setShowCharacterManager] = useState(false);\n  const [showRulebook, setShowRulebook] = useState(false);\n  const [sessionContext, setSessionContext] = useState<GameSession | null>(null);"
    )

# Add fetch for session context
fetch_context = """
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
"""

if "/sessions/${sessionId}/context" not in content:
    content = content.replace("setCharacter(charData);", "setCharacter(charData);\n" + fetch_context)

# Add Rulebook Button
button_html = """
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
"""

content = content.replace('<div className="flex items-center gap-2">', button_html, 1)

# Add Modal rendering
modal_html = """
      {showRulebook && sessionContext?.universe?.game_system && (
        <RulebookModal
          system={sessionContext.universe.game_system}
          onClose={() => setShowRulebook(false)}
        />
      )}
    </div>
"""

content = content.replace("</div>\n  );\n}", modal_html + "\n  );\n}")

with open("frontend/src/pages/Play.tsx", "w") as f:
    f.write(content)
