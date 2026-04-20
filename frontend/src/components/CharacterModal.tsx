import type { Character } from '../types';

interface CharacterModalProps {
  character: Character;
  onClose: () => void;
  sendAction?: (action: string, itemId: string) => void;
}

export function CharacterModal({ character, onClose, sendAction }: CharacterModalProps) {

  const getModifier = (score: number) => {
    const mod = Math.floor((score - 10) / 2);
    return mod >= 0 ? `+${mod}` : `${mod}`;
  };

  const statBoxes = character.stats ? Object.entries(character.stats).map(([key, value]) => ({
    name: key.substring(0, 3).toUpperCase(),
    full: key.charAt(0).toUpperCase() + key.slice(1),
    value: typeof value === 'number' ? value : parseInt(value as string) || 0
  })) : [];

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center p-8 bg-gray-900/80 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-gray-800 border-2 border-amber-900/50 rounded-lg shadow-[0_0_40px_rgba(0,0,0,0.8)] w-full max-w-5xl h-full max-h-[80vh] flex flex-col overflow-hidden relative"
        onClick={(e) => e.stopPropagation()} // Prevent clicks inside from closing
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white bg-gray-900/50 hover:bg-gray-700 p-2 rounded-full transition-colors z-10"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>

        {/* Header */}
        <div className="bg-gray-900 border-b border-gray-700 p-6 flex items-center gap-6">
          {character.reference_portrait_url ? (
            <div className="relative w-20 h-20 rounded-full p-1 bg-gradient-to-br from-amber-500 to-amber-900 shadow-[0_0_15px_rgba(245,158,11,0.3)] shrink-0">
              <img
                src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${character.reference_portrait_url}`}
                alt={character.name}
                className="w-full h-full object-cover rounded-full border-2 border-gray-900"
              />
            </div>
          ) : (
             <div className="w-20 h-20 rounded-full bg-gray-700 border-2 border-gray-600 flex items-center justify-center text-gray-500 text-3xl font-bold shrink-0">
               {character.name.charAt(0).toUpperCase()}
             </div>
          )}

          <div className="flex-1">
            <h2 className="text-3xl font-serif font-bold text-amber-500">{character.name}</h2>
            <div className="flex gap-4 mt-2 text-sm text-gray-300">
              <span className="bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                Niveau <strong className="text-white">{character.level || 1}</strong>
              </span>
              <span className="bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                XP <strong className="text-amber-400">{character.experience || 0}</strong>
              </span>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col lg:flex-row gap-8">

          {/* Left Column: Stats */}
          <div className="lg:w-1/3 flex flex-col gap-6">

            {/* Ability Scores */}
            <div className="grid grid-cols-2 gap-4">
              {statBoxes.length === 0 ? (
                <div className="col-span-2 text-center text-gray-500 italic p-4 bg-gray-900/50 rounded-lg border border-gray-700">
                  Aucune statistique définie.
                </div>
              ) : statBoxes.map((stat) => (
                <div key={stat.name} className="bg-gray-900/50 border border-gray-700 rounded-lg p-3 flex flex-col items-center relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-amber-900/30"></div>
                  <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider mb-1">{stat.full}</span>
                  <span className="text-3xl font-serif text-gray-200">{stat.value}</span>
                  <div className="mt-2 bg-gray-800 border border-gray-600 rounded-full w-12 h-8 flex items-center justify-center shadow-inner">
                    <span className="text-sm font-bold text-amber-400">{getModifier(stat.value)}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Combat Stats Mini */}
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4 grid grid-cols-3 gap-2 text-center">
               <div>
                  <div className="text-sm text-gray-400 mb-1">AC</div>
                  <div className="text-xl font-bold text-blue-400">{character.armor_class}</div>
               </div>
               <div className="border-x border-gray-700">
                  <div className="text-sm text-gray-400 mb-1">Init</div>
                  <div className="text-xl font-bold text-gray-200">{character.stats && character.stats.dexterity ? getModifier(typeof character.stats.dexterity === "number" ? character.stats.dexterity : parseInt(character.stats.dexterity) || 10) : 0}</div>
               </div>
               <div>
                  <div className="text-sm text-gray-400 mb-1">Speed</div>
                  <div className="text-xl font-bold text-amber-400">{character.speed}</div>
               </div>
            </div>
          </div>

          {/* Right Column: Spells & Inventory (Placeholder) */}
          <div className="lg:w-2/3 flex flex-col gap-6">

            {/* Spells List */}
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg flex flex-col h-full">
              <div className="bg-gray-800/80 p-3 border-b border-gray-700 rounded-t-lg">
                <h3 className="font-serif font-bold text-lg text-emerald-500 flex items-center gap-2">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
                  </svg>
                  Grimoire & Sorts Connus
                </h3>
              </div>
              <div className="p-4 flex-1 overflow-y-auto">
                {(!character.known_spells || character.known_spells.length === 0) ? (
                  <div className="h-full flex items-center justify-center text-gray-500 italic">
                    Aucun sort connu.
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {character.known_spells.map((spell: Record<string, unknown> | string, idx: number) => {
                       const spellName = typeof spell === 'string' ? spell : (spell as Record<string, string>).name;
                       const spellDesc = typeof spell === 'string' ? '' : (spell as Record<string, string>).description;
                       return (
                        <li key={idx} className="bg-gray-800/50 p-3 rounded border border-gray-700/50 hover:border-gray-600 transition-colors">
                          <h4 className="font-bold text-indigo-400">{spellName}</h4>
                          {spellDesc && <p className="text-sm text-gray-400 mt-1">{spellDesc}</p>}
                        </li>
                       )
                    })}
                  </ul>
                )}
              </div>
            </div>

            {/* Inventory List */}
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg flex flex-col h-full mt-6">
              <div className="bg-gray-800/80 p-3 border-b border-gray-700 rounded-t-lg">
                <h3 className="font-serif font-bold text-lg text-amber-500 flex items-center gap-2">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 16V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v12"/>
                    <rect x="2" y="16" width="20" height="6" rx="2"/>
                  </svg>
                  Inventaire
                </h3>
              </div>
              <div className="p-4 flex-1 overflow-y-auto">
                {(!character.inventory || character.inventory.length === 0) ? (
                  <div className="h-full flex items-center justify-center text-gray-500 italic">
                    Inventaire vide.
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {character.inventory.map((slot: { id: string; quantity: number; is_equipped: boolean; item?: { name: string; description: string; item_type: string; attributes: Record<string, unknown> } }) => (
                        <li key={slot.id} className="bg-gray-800/50 p-3 rounded border border-gray-700/50 hover:border-gray-600 transition-colors flex justify-between items-center">
                          <div>
                              <h4 className="font-bold text-amber-400">
                                {slot.quantity}x {slot.item?.name}
                                {slot.is_equipped && <span className="ml-2 text-xs bg-amber-900/50 text-amber-500 border border-amber-700/50 px-2 py-0.5 rounded-full">Équipé</span>}
                              </h4>
                              {slot.item?.description && <p className="text-sm text-gray-400 mt-1">{slot.item.description}</p>}
                          </div>
                          <div>
                              {['WEAPON', 'ARMOR'].includes(slot.item?.item_type as string) && sendAction && (
                                  <button onClick={() => sendAction('equip', slot.id)} className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded transition">
                                      {slot.is_equipped ? 'Déséquiper' : 'Équiper'}
                                  </button>
                              )}
                              {slot.item?.item_type === 'CONSUMABLE' && sendAction && (
                                  <button onClick={() => sendAction('use', slot.id)} className="text-xs bg-emerald-700 hover:bg-emerald-600 text-white px-3 py-1.5 rounded transition">
                                      Utiliser
                                  </button>
                              )}
                          </div>
                        </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  );
}
