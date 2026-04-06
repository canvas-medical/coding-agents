/* canvas-sidebar-layout: flex row container for sidebar + content split views */
if (!customElements.get('canvas-sidebar-layout')) {
  class CanvasSidebarLayout extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: flex;
            flex-direction: row;
            overflow: hidden;
            height: var(--canvas-sidebar-layout-height, auto);
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
          }
          :host([fullscreen]) {
            position: fixed;
            inset: 0;
          }
        </style>
        <slot></slot>
      `;
    }
  }
  customElements.define('canvas-sidebar-layout', CanvasSidebarLayout);
}

/* canvas-sidebar: scrollable left panel with gray background */
if (!customElements.get('canvas-sidebar')) {
  var SIDEBAR_WIDTHS = { 'default': '260px', 'narrow': '210px', 'wide': '400px' };

  class CanvasSidebar extends HTMLElement {
    static get observedAttributes() {
      return ['variant'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            width: var(--canvas-sidebar-width, 260px);
            flex-shrink: 0;
            background: var(--canvas-sidebar-bg, #f5f5f5);
            padding: var(--canvas-sidebar-padding, 0);
            overflow-y: auto;
            box-sizing: border-box;
          }
          :host::-webkit-scrollbar { width: 8px; }
          :host::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.15); border-radius: 4px; }
          :host::-webkit-scrollbar-track { background: transparent; }
        </style>
        <slot></slot>
      `;
    }

    connectedCallback() {
      this._applyVariant();
    }

    attributeChangedCallback(name) {
      if (name === 'variant') this._applyVariant();
    }

    _applyVariant() {
      var variant = this.getAttribute('variant') || 'default';
      var width = SIDEBAR_WIDTHS[variant] || SIDEBAR_WIDTHS['default'];
      this.style.setProperty('--canvas-sidebar-width', width);
    }
  }
  customElements.define('canvas-sidebar', CanvasSidebar);
}

/* canvas-content: flexible right panel with white background */
if (!customElements.get('canvas-content')) {
  class CanvasContent extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            flex: 1;
            background: var(--canvas-content-bg, #fff);
            padding: var(--canvas-content-padding, 0);
            overflow-y: auto;
            box-sizing: border-box;
          }
        </style>
        <slot></slot>
      `;
    }
  }
  customElements.define('canvas-content', CanvasContent);
}
