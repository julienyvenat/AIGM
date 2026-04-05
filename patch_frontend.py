import re

# 1. Update useGameWebSocket.ts
with open("frontend/src/hooks/useGameWebSocket.ts", "r") as f:
    content = f.read()

content = content.replace(
    "export type MessageType = 'narrator' | 'system' | 'error' | 'chat' | 'combat_state' | 'scene_image';",
    "export type MessageType = 'narrator' | 'system' | 'error' | 'chat' | 'combat_state' | 'scene_image' | 'battlemap_update';"
)

content = content.replace(
    "const [currentSceneImage, setCurrentSceneImage] = useState<string | null>(null);",
    "const [currentSceneImage, setCurrentSceneImage] = useState<string | null>(null);\n  const [battlemapImageUrl, setBattlemapImageUrl] = useState<string | null>(null);"
)

hook_return_patch = "return { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage, battlemapImageUrl };"
content = content.replace(
    "return { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage };",
    hook_return_patch
)

msg_handler_patch = """          if (data.type === 'scene_image' && data.url) {
            setCurrentSceneImage(data.url);

            // Add local system message
            const systemMessage: GameMessage = {
              id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
              sender: 'server',
              type: 'system',
              category: 'SYSTEM',
              message: "Le MJ a partagé une vision...",
            };
            setMessages((prev) => [...prev, systemMessage]);
            return;
          }

          if (data.type === 'battlemap_update') {
            setBattlemapImageUrl(data.url);
            return;
          }"""
content = content.replace("""          if (data.type === 'scene_image' && data.url) {
            setCurrentSceneImage(data.url);

            // Add local system message
            const systemMessage: GameMessage = {
              id: Date.now().toString() + Math.random().toString(36).substring(2, 9),
              sender: 'server',
              type: 'system',
              category: 'SYSTEM',
              message: "Le MJ a partagé une vision...",
            };
            setMessages((prev) => [...prev, systemMessage]);
            return;
          }""", msg_handler_patch)

with open("frontend/src/hooks/useGameWebSocket.ts", "w") as f:
    f.write(content)


# 2. Update Play.tsx
with open("frontend/src/pages/Play.tsx", "r") as f:
    content = f.read()

content = content.replace(
    "const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(activePlayerId, universeId || null, handleStatsUpdate);",
    "const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage, battlemapImageUrl } = useGameWebSocket(activePlayerId, universeId || null, handleStatsUpdate);"
)

content = content.replace(
    "<BattleMap entities={entities} />",
    "<BattleMap entities={entities} battlemapImageUrl={battlemapImageUrl} />"
)

with open("frontend/src/pages/Play.tsx", "w") as f:
    f.write(content)


# 3. Update BattleMap.tsx
with open("frontend/src/components/BattleMap.tsx", "r") as f:
    content = f.read()

content = content.replace(
    "interface BattleMapProps {\n  entities: Entity[];\n}",
    "interface BattleMapProps {\n  entities: Entity[];\n  battlemapImageUrl?: string | null;\n}"
)

content = content.replace(
    "export const BattleMap: React.FC<BattleMapProps> = ({ entities }) => {",
    "export const BattleMap: React.FC<BattleMapProps> = ({ entities, battlemapImageUrl }) => {"
)

bg_patch = """      {/* Background Image */}\n      {battlemapImageUrl && (\n        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${battlemapImageUrl})` }} />\n      )}

      {/* Background Grid */}
      <div
        className="absolute inset-0 grid"
        style={{
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          gridTemplateRows: `repeat(${gridSize}, 1fr)`,
        }}
      >"""
content = content.replace("""      {/* Background Grid */}
      <div
        className="absolute inset-0 grid bg-stone-800"
        style={{
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          gridTemplateRows: `repeat(${gridSize}, 1fr)`,
        }}
      >""", bg_patch)

# Only show "Out of combat" if no battlemap is set
overlay_patch = """      {/* Out of Combat Overlay */}
      {!battlemapImageUrl && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-20 backdrop-blur-sm">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-200 tracking-wider">Exploration en cours...</h3>
            <p className="text-gray-400 mt-2 text-sm italic">Tapez /battle pour commencer un combat</p>
          </div>
        </div>
      )}"""
content = content.replace("""      {/* Out of Combat Overlay */}
      {entities.length === 0 && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-20 backdrop-blur-sm">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-200 tracking-wider">Exploration en cours...</h3>
            <p className="text-gray-400 mt-2 text-sm italic">Aucun combat actif</p>
          </div>
        </div>
      )}""", overlay_patch)

with open("frontend/src/components/BattleMap.tsx", "w") as f:
    f.write(content)
