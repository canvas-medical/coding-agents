if (!customElements.get('canvas-button')) {
  class CanvasButton extends HTMLElement {
    static get observedAttributes() {
      return ['variant', 'size', 'disabled', 'type'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-flex;
          }

          button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--canvas-button-gap, var(--space-tiny, 8px));
            padding: var(--canvas-button-padding, .67857143em 1.5em);
            font-size: var(--canvas-button-font-size, 1rem);
            font-weight: var(--canvas-button-font-weight, var(--font-weight-bold, 700));
            font-family: var(--canvas-button-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            line-height: 1.21428571em;
            border: var(--canvas-button-border, 1px solid transparent);
            border-radius: var(--canvas-button-radius, var(--radius, .28571429rem));
            cursor: pointer;
            transition: background-color var(--canvas-button-transition, var(--transition-fast, 200ms)), opacity var(--canvas-button-transition, var(--transition-fast, 200ms));
            min-height: 1em;
            width: 100%;
            height: 100%;
            background: var(--canvas-button-bg, var(--color-secondary, var(--palette-blue, #2185D0)));
            color: var(--canvas-button-color, #fff);
          }

          button:focus-visible {
            outline: var(--canvas-button-focus-ring, var(--focus-ring, 2px solid #2185D0));
            outline-offset: var(--canvas-button-focus-ring-offset, var(--focus-ring-offset, 2px));
          }

          /* Variants */
          :host([variant="primary"]) button {
            background: var(--canvas-button-primary-bg, var(--color-primary, var(--palette-green, #22BA45)));
            color: var(--canvas-button-primary-color, #fff);
          }

          :host([variant="secondary"]) button,
          :host(:not([variant])) button {
            background: var(--canvas-button-bg, var(--color-secondary, var(--palette-blue, #2185D0)));
            color: var(--canvas-button-color, #fff);
          }

          :host([variant="ghost"]) button {
            background: var(--canvas-button-ghost-bg, #e0e1e2);
            color: var(--canvas-button-ghost-color, rgba(0, 0, 0, 0.6));
          }

          :host([variant="danger"]) button {
            background: var(--canvas-button-danger-bg, var(--color-danger, var(--palette-red, #BD0B00)));
            color: var(--canvas-button-danger-color, #fff);
          }

          /* Hover */
          :host([variant="primary"]) button:hover,
          :host([variant="secondary"]) button:hover,
          :host(:not([variant])) button:hover,
          :host([variant="danger"]) button:hover {
            opacity: 0.9;
          }

          :host([variant="ghost"]) button:hover {
            background: var(--canvas-button-ghost-hover-bg, #cacbcd);
            color: var(--canvas-button-ghost-hover-color, rgba(0, 0, 0, 0.8));
          }

          /* Sizes */
          :host([size="sm"]) button {
            padding: var(--canvas-button-padding-sm, .58928571em 1.125em);
            font-size: var(--canvas-button-font-size-sm, .92857143rem);
            min-height: 36px;
          }

          :host([size="xs"]) button {
            padding: var(--canvas-button-padding-xs, .5em .85714286em);
            font-size: var(--canvas-button-font-size-xs, .78571429rem);
            font-weight: 400;
            min-height: 0;
          }

          /* Disabled */
          :host([disabled]) button {
            opacity: 0.45;
            cursor: default;
            pointer-events: none;
          }
        </style>
        <button type="button" part="button"><slot></slot></button>
      `;
      this._button = this.shadowRoot.querySelector('button');
    }

    connectedCallback() {
      this._syncType();
      this._syncDisabled();
      this._button.addEventListener('click', this._handleClick.bind(this));
    }

    disconnectedCallback() {
      this._button.removeEventListener('click', this._handleClick.bind(this));
    }

    attributeChangedCallback(name) {
      if (name === 'type') this._syncType();
      if (name === 'disabled') this._syncDisabled();
    }

    _syncType() {
      this._button.type = this.getAttribute('type') || 'button';
    }

    _syncDisabled() {
      var disabled = this.hasAttribute('disabled');
      if (disabled) {
        this._button.setAttribute('disabled', '');
      } else {
        this._button.removeAttribute('disabled');
      }
    }

    _handleClick(e) {
      e.stopPropagation();
      if (this.hasAttribute('disabled')) return;
      if (this.getAttribute('type') === 'submit') {
        var form = this.closest('form');
        if (form) form.requestSubmit();
      }
    }
  }

  customElements.define('canvas-button', CanvasButton);
}
