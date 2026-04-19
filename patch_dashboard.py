with open("frontend/src/pages/Dashboard.tsx", "r") as f:
    content = f.read()

# Replace session display
old_session_display = """                 <li key={session.id} className="bg-gray-700 p-4 rounded-md">
                    <h3 className="font-bold text-white">Session #{session.id}</h3>
                    <p className="text-sm text-gray-400">Univers: {session.universe_id}</p>
                 </li>"""

new_session_display = """                 <li key={session.id} className="bg-gray-700 p-4 rounded-md">
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
                 </li>"""

content = content.replace(old_session_display, new_session_display)

with open("frontend/src/pages/Dashboard.tsx", "w") as f:
    f.write(content)
