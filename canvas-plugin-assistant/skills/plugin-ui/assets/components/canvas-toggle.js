if (!customElements.get('canvas-toggle')) {
  class CanvasToggle extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'checked', 'disabled', 'label-position'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            min-height: var(--canvas-toggle-min-height, auto);
            min-width: var(--canvas-toggle-min-width, auto);
            cursor: pointer;
            user-select: none;
            font-size: 1rem;
            line-height: 1;
            font-family: lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          }

          :host([label-position="start"]) {
            flex-direction: row-reverse;
          }

          :host([disabled]) {
            cursor: not-allowed;
            opacity: 0.45;
          }

          .track {
            position: relative;
            flex-shrink: 0;
            width: 3.5rem;
            height: 1.5rem;
            background: #F4F4F4;
            border-radius: 500rem;
            border: none;
            padding: 0;
            cursor: pointer;
            pointer-events: auto;
          }

          .track::after {
            content: "";
            position: absolute;
            top: 0;
            left: -0.05rem;
            width: 1.5rem;
            height: 1.5rem;
            background: #fff linear-gradient(transparent, rgba(0, 0, 0, 0.05));
            border-radius: 500rem;
            box-shadow: 0 1px 2px 0 rgba(34, 36, 38, 0.15), 0 0 0 1px rgba(34, 36, 38, 0.15) inset;
            transition: left 0.3s ease;
          }

          :host([checked]) .track { background: #0D71BC; }
          :host([checked]) .track::after { left: 2.15rem; }

          :host(:not([disabled]):hover) .track { background: #DEDEDE; }
          :host(:not([disabled]):hover[checked]) .track { background: #0D71BC; }

          .track:focus-visible {
            outline: 2px solid #85b7d9;
            outline-offset: 2px;
          }

          :host([disabled]) .track { cursor: not-allowed; }

          .label-text {
            color: rgba(0, 0, 0, 0.87);
          }
        </style>
        <button class="track" role="switch" aria-checked="false" tabindex="0" part="track"></button>
        <span class="label-text" part="label"></span>
      `;
      this._track = this.shadowRoot.querySelector('.track');
      this._labelText = this.shadowRoot.querySelector('.label-text');
      this._boundOnClick = this._onClick.bind(this);
    }

    connectedCallback() {
      this.addEventListener('click', this._boundOnClick);
      this._syncAll();
    }

    disconnectedCallback() {
      this.removeEventListener('click', this._boundOnClick);
    }

    attributeChangedCallback(name) {
      switch (name) {
        case 'label':
          this._labelText.textContent = this.getAttribute('label') || '';
          if (this.getAttribute('label')) {
            this._track.setAttribute('aria-label', this.getAttribute('label'));
          }
          break;
        case 'checked':
          this._track.setAttribute('aria-checked', this.hasAttribute('checked') ? 'true' : 'false');
          break;
        case 'disabled':
          if (this.hasAttribute('disabled')) {
            this._track.setAttribute('disabled', '');
            this._track.setAttribute('tabindex', '-1');
          } else {
            this._track.removeAttribute('disabled');
            this._track.setAttribute('tabindex', '0');
          }
          break;
      }
    }

    get checked() {
      return this.hasAttribute('checked');
    }

    set checked(v) {
      if (v) {
        this.setAttribute('checked', '');
      } else {
        this.removeAttribute('checked');
      }
    }

    _syncAll() {
      this._labelText.textContent = this.getAttribute('label') || '';
      if (this.getAttribute('label')) {
        this._track.setAttribute('aria-label', this.getAttribute('label'));
      }
      this._track.setAttribute('aria-checked', this.hasAttribute('checked') ? 'true' : 'false');
      if (this.hasAttribute('disabled')) {
        this._track.setAttribute('disabled', '');
        this._track.setAttribute('tabindex', '-1');
      }
    }

    _onClick(e) {
      e.stopPropagation();
      if (this.hasAttribute('disabled')) return;
      if (this.hasAttribute('checked')) {
        this.removeAttribute('checked');
      } else {
        this.setAttribute('checked', '');
      }
      this.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
    }
  }

  customElements.define('canvas-toggle', CanvasToggle);
}
