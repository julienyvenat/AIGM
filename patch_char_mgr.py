import re

with open('frontend/src/components/CharacterManager.tsx', 'r') as f:
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

replace_interface = """import type { Character } from '../App';"""

content = content.replace(search_interface, replace_interface)

with open('frontend/src/components/CharacterManager.tsx', 'w') as f:
    f.write(content)
