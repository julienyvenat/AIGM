import { render, screen, fireEvent } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { BattleMap, CELL_SIZE, type Entity } from '../components/BattleMap';

function mockViewportRect(widthCells: number, heightCells: number) {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
    x: 0,
    y: 0,
    left: 0,
    top: 0,
    right: widthCells * CELL_SIZE,
    bottom: heightCells * CELL_SIZE,
    width: widthCells * CELL_SIZE,
    height: heightCells * CELL_SIZE,
    toJSON: () => ({}),
  } as DOMRect);
}

const hero: Entity = { id: 'hero', name: 'Hero', is_pc: true, hp: 8, max_hp: 10, x: 2, y: 2 };

test('grid size comes from props instead of a hardcoded 15x15', () => {
  mockViewportRect(10, 8);
  const { container } = render(<BattleMap entities={[]} gridWidth={10} gridHeight={8} />);

  const cells = container.querySelectorAll('.border-stone-700\\/50');
  expect(cells.length).toBe(80);
});

test('defaults to a 15x15 grid when no dimensions are provided (back-compat)', () => {
  mockViewportRect(15, 15);
  const { container } = render(<BattleMap entities={[]} />);

  const cells = container.querySelectorAll('.border-stone-700\\/50');
  expect(cells.length).toBe(225);
});

test('mouse wheel zooms the map layer in and out', () => {
  mockViewportRect(15, 15);
  render(<BattleMap entities={[]} gridWidth={15} gridHeight={15} />);
  const viewport = screen.getByTestId('battlemap-viewport');
  const layer = screen.getByTestId('battlemap-layer');

  expect(layer.style.transform).toContain('scale(1)');

  fireEvent.wheel(viewport, { deltaY: -100, clientX: 100, clientY: 100 });
  expect(layer.style.transform).toMatch(/scale\(1\.1/);

  fireEvent.wheel(viewport, { deltaY: 100, clientX: 100, clientY: 100 });
  fireEvent.wheel(viewport, { deltaY: 100, clientX: 100, clientY: 100 });
  // Zooming back out should bring the scale back down below where it was.
  const scaleMatch = layer.style.transform.match(/scale\(([\d.]+)\)/);
  expect(scaleMatch).not.toBeNull();
  expect(Number(scaleMatch?.[1])).toBeLessThan(1.1);
});

test('click-drag on the background pans the map layer', () => {
  mockViewportRect(15, 15);
  render(<BattleMap entities={[]} gridWidth={15} gridHeight={15} />);
  const viewport = screen.getByTestId('battlemap-viewport');
  const layer = screen.getByTestId('battlemap-layer');

  fireEvent.pointerDown(viewport, { clientX: 100, clientY: 100 });
  fireEvent.pointerMove(viewport, { clientX: 140, clientY: 130 });
  fireEvent.pointerUp(viewport, { clientX: 140, clientY: 130 });

  expect(layer.style.transform).toContain('translate(40px, 30px)');
});

test('dragging a token to a new cell calls onMoveEntity with the dropped grid coordinates', () => {
  mockViewportRect(15, 15);
  const onMoveEntity = vi.fn();
  render(<BattleMap entities={[hero]} gridWidth={15} gridHeight={15} onMoveEntity={onMoveEntity} />);

  const token = screen.getByTestId('token-hero');
  const viewport = screen.getByTestId('battlemap-viewport');

  // Drop in the middle of cell (5, 6).
  fireEvent.pointerDown(token, { clientX: CELL_SIZE * 2 + 5, clientY: CELL_SIZE * 2 + 5 });
  fireEvent.pointerMove(viewport, { clientX: CELL_SIZE * 5 + 5, clientY: CELL_SIZE * 6 + 5 });
  fireEvent.pointerUp(viewport, { clientX: CELL_SIZE * 5 + 5, clientY: CELL_SIZE * 6 + 5 });

  expect(onMoveEntity).toHaveBeenCalledWith('hero', 5, 6);
});

test('dropping a token past the edge clamps to the grid bounds', () => {
  mockViewportRect(15, 15);
  const onMoveEntity = vi.fn();
  render(<BattleMap entities={[hero]} gridWidth={15} gridHeight={15} onMoveEntity={onMoveEntity} />);

  const token = screen.getByTestId('token-hero');
  const viewport = screen.getByTestId('battlemap-viewport');

  fireEvent.pointerDown(token, { clientX: CELL_SIZE * 2 + 5, clientY: CELL_SIZE * 2 + 5 });
  fireEvent.pointerMove(viewport, { clientX: CELL_SIZE * 999, clientY: -999 });
  fireEvent.pointerUp(viewport, { clientX: CELL_SIZE * 999, clientY: -999 });

  expect(onMoveEntity).toHaveBeenCalledWith('hero', 14, 0);
});

test('starting a drag on a token does not also pan the background', () => {
  mockViewportRect(15, 15);
  const onMoveEntity = vi.fn();
  render(<BattleMap entities={[hero]} gridWidth={15} gridHeight={15} onMoveEntity={onMoveEntity} />);

  const token = screen.getByTestId('token-hero');
  const layer = screen.getByTestId('battlemap-layer');

  fireEvent.pointerDown(token, { clientX: 90, clientY: 90 });
  fireEvent.pointerUp(token, { clientX: 90, clientY: 90 });

  expect(layer.style.transform).toContain('translate(0px, 0px)');
});

test('without an onMoveEntity handler, pointer-down on a token falls through to panning', () => {
  mockViewportRect(15, 15);
  render(<BattleMap entities={[hero]} gridWidth={15} gridHeight={15} />);

  const token = screen.getByTestId('token-hero');
  const viewport = screen.getByTestId('battlemap-viewport');
  const layer = screen.getByTestId('battlemap-layer');

  // The token only intercepts the pointer-down (to start a drag) when a
  // move handler is actually wired up; otherwise it's inert and the event
  // bubbles to the background, which pans as usual.
  fireEvent.pointerDown(token, { clientX: 90, clientY: 90 });
  fireEvent.pointerMove(viewport, { clientX: 300, clientY: 300 });
  fireEvent.pointerUp(viewport, { clientX: 300, clientY: 300 });

  expect(layer.style.transform).toContain('translate(210px, 210px)');
});
