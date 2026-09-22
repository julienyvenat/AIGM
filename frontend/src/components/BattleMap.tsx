import React, { useRef, useState, useCallback } from 'react';

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
  /** Grid dimensions in cells, driven by the backend's combat_state /
   * GameSession data instead of a hardcoded 15x15 (see useGameWebSocket). */
  gridWidth?: number;
  gridHeight?: number;
  /** Called when a token is dragged & dropped onto a new cell, so the
   * caller can persist it via the `move_entity` UI_ACTION. */
  onMoveEntity?: (entityId: string, x: number, y: number) => void;
}

// Fixed cell size in px for the underlying map layer. Pan/zoom are applied
// as a CSS transform on top of this, so this only needs to be "big enough"
// to look reasonable at zoom 1 -- it isn't a real-world unit.
export const CELL_SIZE = 40;
const MIN_ZOOM = 0.4;
const MAX_ZOOM = 3;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

export const BattleMap: React.FC<BattleMapProps> = ({
  entities,
  battlemapImageUrl,
  gridWidth = 15,
  gridHeight = 15,
  onMoveEntity,
}) => {
  const gridCells = Array.from({ length: gridWidth * gridHeight }, (_, i) => i);

  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panOriginRef = useRef({ x: 0, y: 0 });

  const [draggingEntityId, setDraggingEntityId] = useState<string | null>(null);
  const [dragScreenPos, setDragScreenPos] = useState<{ x: number; y: number } | null>(null);

  // Converts a viewport (clientX/clientY) point into a grid cell, accounting
  // for the current pan/zoom transform. Clamped to the grid bounds, same as
  // the backend's `set_entity_position` (drops off the edge just land on
  // the nearest valid cell instead of being silently ignored).
  const clientPointToCell = useCallback(
    (clientX: number, clientY: number) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return null;
      const mapX = (clientX - rect.left - pan.x) / zoom;
      const mapY = (clientY - rect.top - pan.y) / zoom;
      const cellX = clamp(Math.floor(mapX / CELL_SIZE), 0, gridWidth - 1);
      const cellY = clamp(Math.floor(mapY / CELL_SIZE), 0, gridHeight - 1);
      return { x: cellX, y: cellY };
    },
    [pan, zoom, gridWidth, gridHeight]
  );

  const handleWheel = useCallback(
    (e: React.WheelEvent<HTMLDivElement>) => {
      e.preventDefault();
      const rect = containerRef.current?.getBoundingClientRect();
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom((prevZoom) => {
        const nextZoom = clamp(prevZoom * zoomFactor, MIN_ZOOM, MAX_ZOOM);
        if (rect) {
          // Keep the point under the cursor stationary while zooming.
          const localX = e.clientX - rect.left;
          const localY = e.clientY - rect.top;
          setPan((prevPan) => ({
            x: localX - ((localX - prevPan.x) / prevZoom) * nextZoom,
            y: localY - ((localY - prevPan.y) / prevZoom) * nextZoom,
          }));
        }
        return nextZoom;
      });
    },
    []
  );

  const handleBackgroundPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    // Only pan when clicking the background itself, not a token (tokens
    // stop propagation in their own handler).
    setIsPanning(true);
    panOriginRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  }, [pan]);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (draggingEntityId) {
      setDragScreenPos({ x: e.clientX, y: e.clientY });
      return;
    }
    if (isPanning) {
      setPan({ x: e.clientX - panOriginRef.current.x, y: e.clientY - panOriginRef.current.y });
    }
  }, [draggingEntityId, isPanning]);

  const endInteraction = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (draggingEntityId) {
      const cell = clientPointToCell(e.clientX, e.clientY);
      if (cell && onMoveEntity) {
        onMoveEntity(draggingEntityId, cell.x, cell.y);
      }
      setDraggingEntityId(null);
      setDragScreenPos(null);
    }
    setIsPanning(false);
  }, [draggingEntityId, clientPointToCell, onMoveEntity]);

  const handleTokenPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>, entityId: string) => {
    if (!onMoveEntity) return;
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    setDraggingEntityId(entityId);
    setDragScreenPos({ x: e.clientX, y: e.clientY });
  }, [onMoveEntity]);

  const draggingEntity = draggingEntityId ? entities.find((ent) => ent.id === draggingEntityId) : null;

  return (
    <div
      ref={containerRef}
      className="relative w-full max-w-3xl aspect-square bg-stone-900 border-4 border-stone-800 rounded-lg overflow-hidden shadow-2xl select-none touch-none"
      onWheel={handleWheel}
      onPointerDown={handleBackgroundPointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={endInteraction}
      onPointerCancel={endInteraction}
      data-testid="battlemap-viewport"
    >
      {/* Pan/zoom layer: everything below moves together as one map. */}
      <div
        data-testid="battlemap-layer"
        className="absolute top-0 left-0"
        style={{
          width: gridWidth * CELL_SIZE,
          height: gridHeight * CELL_SIZE,
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0',
          cursor: isPanning ? 'grabbing' : 'grab',
        }}
      >
        {/* Background Image */}
        {battlemapImageUrl && (
          <div
            className="absolute inset-0 bg-cover bg-center pointer-events-none"
            style={{ backgroundImage: `url(${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${battlemapImageUrl})` }}
          />
        )}

        {/* Grid */}
        <div
          className="absolute inset-0 grid"
          style={{
            gridTemplateColumns: `repeat(${gridWidth}, 1fr)`,
            gridTemplateRows: `repeat(${gridHeight}, 1fr)`,
          }}
        >
          {gridCells.map((cell) => (
            <div key={`cell-${cell}`} className="border border-stone-700/50 pointer-events-none" />
          ))}

          {/* Entities */}
          {entities.map((entity) => {
            const hpPercentage = Math.max(0, Math.min(100, (entity.hp / entity.max_hp) * 100));
            const isBeingDragged = draggingEntityId === entity.id;

            return (
              <div
                key={entity.id}
                data-testid={`token-${entity.id}`}
                onPointerDown={(e) => handleTokenPointerDown(e, entity.id)}
                className="flex flex-col items-center justify-center relative z-10"
                style={{
                  gridColumn: entity.x + 1,
                  gridRow: entity.y + 1,
                  opacity: isBeingDragged ? 0.35 : 1,
                  cursor: onMoveEntity ? 'grab' : 'default',
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
      </div>

      {/* Drag ghost: follows the cursor in viewport space while dragging a token. */}
      {draggingEntity && dragScreenPos && (
        <div
          className="fixed z-50 w-10 h-10 -translate-x-1/2 -translate-y-1/2 rounded-full flex items-center justify-center shadow-2xl border-2 border-white/80 bg-blue-600/80 pointer-events-none"
          style={{ left: dragScreenPos.x, top: dragScreenPos.y }}
        >
          <span className="text-lg font-bold uppercase text-white select-none">
            {draggingEntity.name.charAt(0)}
          </span>
        </div>
      )}

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
