import '@testing-library/jest-dom';

// jsdom doesn't implement PointerEvent (only the base Event/MouseEvent),
// which breaks `fireEvent.pointerDown/pointerMove/pointerUp` used by the
// Battlemap's pan/zoom/drag-and-drop tests: without this, the synthetic
// event has no clientX/clientY at all. Polyfill a minimal PointerEvent on
// top of MouseEvent so those coordinates flow through as they do in a real
// browser.
if (typeof window !== 'undefined' && typeof window.PointerEvent === 'undefined') {
  class PointerEventPolyfill extends MouseEvent {
    public pointerId: number;
    public pointerType: string;

    constructor(type: string, params: PointerEventInit = {}) {
      super(type, params);
      this.pointerId = params.pointerId ?? 0;
      this.pointerType = params.pointerType ?? 'mouse';
    }
  }

  // @ts-expect-error -- polyfilling a DOM global jsdom doesn't provide.
  window.PointerEvent = PointerEventPolyfill;
}
