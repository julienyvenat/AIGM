import re

with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

# Add imports
search_imports = """import { CharacterManager } from './components/CharacterManager';"""
replace_imports = """import { CharacterManager } from './components/CharacterManager';
import { CharacterSidePanel } from './components/CharacterSidePanel';
import { CharacterModal } from './components/CharacterModal';"""

content = content.replace(search_imports, replace_imports)

# Add side panel to the layout
search_layout = """      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left Column: Chat (1/3) */}"""
replace_layout = """      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Column: Chat (1/3) */}"""
content = content.replace(search_layout, replace_layout)

search_modals = """        {/* Modals */}
        {showCharacterManager && character && ("""
replace_modals = """        {character && isConnected && (
           <CharacterSidePanel character={character} onOpenModal={() => setIsCharacterModalOpen(true)} />
        )}

        {/* Modals */}
        {isCharacterModalOpen && character && (
           <CharacterModal character={character} onClose={() => setIsCharacterModalOpen(false)} />
        )}

        {showCharacterManager && character && ("""
content = content.replace(search_modals, replace_modals)

with open('frontend/src/App.tsx', 'w') as f:
    f.write(content)
