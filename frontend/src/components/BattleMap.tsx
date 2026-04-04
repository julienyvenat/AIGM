import React from 'react';

export interface Entity {
  id: string;
  name: string;
  is_pc: boolean;
  hp: number;
  max_hp: number;
  x: number;
  y: number;
}

interface BattleMapProps {
  entities: Entity[];
  battlemapImageUrl?: string | null;
}

export const BattleMap: React.FC<BattleMapProps> = ({ entities, battlemapImageUrl }) => {
  // Hardcoded 15x15 grid for now
  const gridSize = 15;
  const gridCells = Array.from({ length: gridSize * gridSize }, (_, i) => i);

  return (
    <div className="relative w-full max-w-3xl aspect-square flex items-center justify-center bg-stone-900 border-4 border-stone-800 rounded-lg overflow-hidden shadow-2xl">
      {/* Background Image */}
      {battlemapImageUrl && (
        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${battlemapImageUrl})` }} />
      )}

      {/* Background Grid */}
      <div
        className="absolute inset-0 grid"
        style={{
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          gridTemplateRows: `repeat(${gridSize}, 1fr)`,
        }}
      >
        {gridCells.map((cell) => (
          <div key={`cell-${cell}`} className="border border-stone-700/50" />
        ))}

        {/* Entities */}
        {entities.map((entity) => {
          // Calculate HP percentage for the health bar
          const hpPercentage = Math.max(0, Math.min(100, (entity.hp / entity.max_hp) * 100));

          return (
            <div
              key={entity.id}
              className="flex flex-col items-center justify-center relative z-10"
              style={{
                gridColumn: entity.x + 1,
                gridRow: entity.y + 1,
              }}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center shadow-md border-2 ${
                  entity.is_pc
                    ? 'bg-blue-600 border-yellow-400 text-white'
                    : 'bg-red-600 border-black text-white'
                }`}
              >
                <span className="text-lg font-bold uppercase select-none">
                  {entity.name.charAt(0)}
                </span>
              </div>

              {/* Info Overlay (Name & HP Bar) */}
              <div className="absolute -bottom-4 flex flex-col items-center w-max pointer-events-none">
                <span className="text-[10px] font-bold text-white bg-black/70 px-1 rounded whitespace-nowrap mb-0.5">
                  {entity.name}
                </span>
                <div className="w-8 h-1 bg-red-900 rounded-full overflow-hidden border border-black/50">
                  <div
                    className="h-full bg-green-500 transition-all duration-300"
                    style={{ width: `${hpPercentage}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Out of Combat Overlay */}
      {!battlemapImageUrl && (
        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-20 backdrop-blur-sm">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-200 tracking-wider">Exploration en cours...</h3>
            <p className="text-gray-400 mt-2 text-sm italic">Tapez /battle pour commencer un combat</p>
          </div>
        </div>
      )}
    </div>
  );
};
