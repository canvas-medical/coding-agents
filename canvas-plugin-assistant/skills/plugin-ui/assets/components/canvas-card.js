if (!customElements.get('canvas-card')) {
  class CanvasCard extends HTMLElement {
    static get observedAttributes() {
      return ['raised'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
          }

          .card {
            display: flex;
            flex-direction: column;
            position: relative;
            border: 1px solid rgba(34, 36, 38, 0.15);
            box-shadow: var(--canvas-card-shadow, 0 1px 2px 0 rgba(34, 36, 38, 0.15));
            border-radius: var(--radius, .28571429rem);
            background: var(--color-surface, #FFFFFF);
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: var(--color-text, rgba(0, 0, 0, 0.87));
            overflow: hidden;
          }

          :host([raised]) .card {
            box-shadow: var(--canvas-card-shadow, 0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15));
          }

          ::slotted(canvas-card-body) {
            display: block;
            padding: 1em;
            background: var(--color-surface, #FFFFFF);
          }

          ::slotted(canvas-card-body[no-padding]) {
            padding: 0;
          }

          ::slotted(canvas-card-body + canvas-card-body) {
            border-top: 1px solid rgba(34, 36, 38, 0.15);
          }

          ::slotted(canvas-card-footer) {
            display: block;
            padding: 1em;
            background: #f3f4f5;
            color: rgba(0, 0, 0, 0.6);
            border-top: 1px solid rgba(34, 36, 38, 0.15);
          }

          ::slotted(canvas-card-footer[no-padding]) {
            padding: 0;
          }
        </style>
        <div class="card">
          <slot></slot>
        </div>
      `;
    }
  }

  class CanvasCardBody extends HTMLElement {
    constructor() {
      super();
    }
  }

  class CanvasCardFooter extends HTMLElement {
    constructor() {
      super();
    }
  }

  customElements.define('canvas-card', CanvasCard);
  customElements.define('canvas-card-body', CanvasCardBody);
  customElements.define('canvas-card-footer', CanvasCardFooter);
}
