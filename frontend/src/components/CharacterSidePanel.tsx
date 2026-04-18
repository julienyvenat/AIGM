import { useState } from 'react';
import type { Character } from '../types';

interface CharacterSidePanelProps {
  character: Character;
  onOpenModal: () => void;
}

export function CharacterSidePanel({ character, onOpenModal }: CharacterSidePanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const togglePanel = () => setIsOpen(!isOpen);

  // Helper to render spell slots
  const renderSpellSlots = () => {
    if (!character.spell_slots || Object.keys(character.spell_slots).length === 0) return null;

    return (
      <div className="mb-4">
        <h4 className="text-xs font-bold text-gray-400 mb-1">Spell Slots</h4>
        <div className="flex flex-col gap-1">
          {Object.entries(character.spell_slots).map(([level, data]) => {
            const l = level.replace('level_', '');
            const typedData = data as Record<string, number>;
            const total = typedData.max || 0;
            const used = typedData.used || 0;
            const available = Math.max(0, total - used);

            if (total === 0) return null;

            return (
              <div key={level} className="flex items-center gap-2 text-xs">
                <span className="text-blue-400 w-4">L{l}</span>
                <div className="flex gap-1">
                  {Array.from({ length: total }).map((_, i) => (
                    <div
                      key={i}
                      className={`w-2.5 h-2.5 rounded-full border border-blue-500 ${i < available ? 'bg-blue-500 shadow-[0_0_4px_rgba(59,130,246,0.6)]' : 'bg-transparent'}`}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Toggle Tab */}
      <button
        onClick={togglePanel}
        className={`absolute top-1/2 -translate-y-1/2 z-40 bg-gray-800 border-y border-l border-amber-900/50 p-2 rounded-l-md shadow-[-4px_0_15px_rgba(0,0,0,0.5)] transition-all duration-300 flex items-center justify-center hover:bg-gray-700 ${
          isOpen ? 'right-64' : 'right-0'
        }`}
        title="Ouvrir le panneau du personnage"
      >
        <span className="text-amber-500 font-bold text-lg leading-none transform -rotate-90 origin-center whitespace-nowrap mb-6 mt-6">
          {character.name}
        </span>
      </button>

      {/* Slide-out Panel */}
      <div
        className={`absolute top-0 right-0 h-full w-64 bg-gray-800/95 backdrop-blur-md border-l border-amber-900/50 shadow-[-10px_0_30px_rgba(0,0,0,0.8)] z-30 transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="p-4 flex flex-col flex-1 overflow-y-auto">
          {/* Header / Portrait */}
          <div className="flex flex-col items-center mb-6">
            {character.reference_portrait_url ? (
              <div className="relative w-24 h-24 rounded-full p-1 bg-gradient-to-br from-amber-500 to-amber-900 mb-3 shadow-[0_0_15px_rgba(245,158,11,0.3)]">
                <img
                  src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${character.reference_portrait_url}`}
                  alt={character.name}
                  className="w-full h-full object-cover rounded-full border-2 border-gray-900"
                />
              </div>
            ) : (
              <div className="w-24 h-24 rounded-full bg-gray-700 border-2 border-gray-600 mb-3 flex items-center justify-center text-gray-500 text-3xl font-bold">
                {character.name.charAt(0).toUpperCase()}
              </div>
            )}
            <h3 className="text-xl font-serif font-bold text-amber-500 text-center">{character.name}</h3>
            <span className="text-xs text-gray-400">Niveau {character.level || 1}</span>
          </div>

          {/* Quick Stats */}
          <div className="bg-gray-900/50 rounded-lg p-3 mb-4 border border-gray-700">
            {/* HP */}
            <div className="mb-3">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400 font-bold">HP</span>
                <span className="text-red-400 font-bold">{character.hp} / {character.max_hp}</span>
              </div>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all duration-300"
                  style={{ width: `${Math.max(0, Math.min(100, ((character.hp || 0) / (character.max_hp || 1)) * 100))}%` }}
                />
              </div>
            </div>

            {/* AC & Speed */}
            <div className="flex justify-between items-center px-2">
              <div className="flex flex-col items-center" title="Classe d'Armure">
                <div className="w-8 h-10 flex items-center justify-center relative">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="absolute inset-0 w-full h-full text-blue-500">
                    <path d="M12 2L3 6v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-9-4z" fill="currentColor" fillOpacity="0.2" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/>
                  </svg>
                  <span className="relative text-sm font-bold text-blue-100 z-10">{character.armor_class}</span>
                </div>
                <span className="text-[10px] text-gray-400 mt-1">AC</span>
              </div>

              <div className="flex flex-col items-center" title="Vitesse">
                <div className="w-8 h-10 flex items-center justify-center text-amber-400">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M13 22h8" /><path d="M13 14h8" /><path d="M13 6h8" /><path d="M3 22l6-10-6-10" />
                  </svg>
                </div>
                <span className="text-[10px] text-gray-400">{character.speed} ft</span>
              </div>
            </div>
          </div>

          {/* Resources */}
          <div className="flex-1">
             {renderSpellSlots()}

             {/* Note: class_resources could be rendered here similarly if needed, but keeping it minimalist for now. */}
          </div>

        </div>

        {/* Action Button */}
        <div className="p-4 border-t border-gray-700 bg-gray-900/50">
          <button
            onClick={() => {
              onOpenModal();
              setIsOpen(false);
            }}
            className="w-full py-2.5 px-4 bg-amber-600/20 hover:bg-amber-600/40 border border-amber-600/50 text-amber-500 hover:text-amber-400 font-bold rounded transition-colors text-sm flex items-center justify-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
            </svg>
            Voir le Grimoire & Détails
          </button>
        </div>
      </div>
    </>
  );
}
