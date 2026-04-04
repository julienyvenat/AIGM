import re

with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

search_interface = """interface Character {
  id: string;
  name: string;
  hp: number;
  max_hp: number;
  armor_class: number;
  speed: number;
  reference_portrait_url: string | null;
}"""

replace_interface = """export interface Character {
  id: string;
  name: string;
  hp: number;
  max_hp: number;
  armor_class: number;
  speed: number;
  reference_portrait_url: string | null;
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  level: number;
  experience: number;
  known_spells: any[];
  spell_slots: Record<string, any>;
  class_resources: Record<string, any>;
}"""

content = content.replace(search_interface, replace_interface)

search_use_ws = """  const [activePlayerId, setActivePlayerId] = useState<string | null>(null);

  const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(activePlayerId);"""

replace_use_ws = """  const [activePlayerId, setActivePlayerId] = useState<string | null>(null);
  const [isCharacterModalOpen, setIsCharacterModalOpen] = useState(false);

  const handleStatsUpdate = (updatedCharacter: Partial<Character>) => {
    setCharacter(prev => prev ? { ...prev, ...updatedCharacter } as Character : updatedCharacter as Character);
  };

  const { isConnected, messages, sendMessage, entities, currentSceneImage, clearSceneImage } = useGameWebSocket(activePlayerId, handleStatsUpdate);"""

content = content.replace(search_use_ws, replace_use_ws)

with open('frontend/src/App.tsx', 'w') as f:
    f.write(content)
