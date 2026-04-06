if (!customElements.get('canvas-banner')) {
  class CanvasBanner extends HTMLElement {
    static get observedAttributes() {
      return ['variant', 'header', 'dismissible'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._render();
      this._onDismissClick = this._onDismissClick.bind(this);
    }

    connectedCallback() {
      var btn = this.shadowRoot.querySelector('.dismiss');
      if (btn) btn.addEventListener('click', this._onDismissClick);
    }

    disconnectedCallback() {
      var btn = this.shadowRoot.querySelector('.dismiss');
      if (btn) btn.removeEventListener('click', this._onDismissClick);
    }

    attributeChangedCallback() {
      this._render();
      var btn = this.shadowRoot.querySelector('.dismiss');
      if (btn) btn.addEventListener('click', this._onDismissClick);
    }

    _onDismissClick(e) {
      e.stopPropagation();
      this.dispatchEvent(new CustomEvent('dismiss', { bubbles: true, composed: true }));
    }

    _render() {
      var header = this.getAttribute('header');
      var dismissible = this.hasAttribute('dismissible');

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
          }

          .banner {
            position: relative;
            min-height: 1em;
            padding: 1em 1.5em;
            line-height: 1.4285em;
            font-size: .92857143em;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: rgba(0, 0, 0, 0.87);
            background: #f8f8f9;
            border-radius: var(--radius, .28571429rem);
            box-shadow: 0 0 0 1px rgba(34, 36, 38, 0.22) inset, 0 0 0 0 transparent;
          }

          :host([dismissible]) .banner {
            padding-right: 2.5em;
          }

          /* Variants */
          :host([variant="warning"]) .banner {
            background-color: #fffaf3;
            color: #573a08;
            box-shadow: 0 0 0 1px #c9ba9b inset, 0 0 0 0 transparent;
          }
          :host([variant="warning"]) .header { color: #794b02; }

          :host([variant="error"]) .banner {
            background-color: #fff6f6;
            color: #9f3a38;
            box-shadow: 0 0 0 1px #e0b4b4 inset, 0 0 0 0 transparent;
          }
          :host([variant="error"]) .header { color: #912d2b; }

          :host([variant="success"]) .banner {
            background-color: #fcfff5;
            color: #2c662d;
            box-shadow: 0 0 0 1px #a3c293 inset, 0 0 0 0 transparent;
          }
          :host([variant="success"]) .header { color: #1a531b; }

          :host([variant="info"]) .banner {
            background-color: #f8ffff;
            color: #276f86;
            box-shadow: 0 0 0 1px #a9d5de inset, 0 0 0 0 transparent;
          }
          :host([variant="info"]) .header { color: #0e566c; }

          /* Header */
          .header {
            font-weight: 700;
            font-size: 1.14285714em;
          }

          /* Slotted content spacing */
          .header + .body { margin-top: .25em; }
          .body { opacity: 0.85; }
          ::slotted(ul) { padding-left: 1.5em; margin: 0; }
          ::slotted(p) { margin: 0; }
          ::slotted(p + ul) { margin-top: .5em; }
          ::slotted(li) { margin-bottom: .25em; }

          /* Dismiss button */
          .dismiss {
            position: absolute;
            top: 1em;
            right: 1em;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            margin: 0;
            background: none;
            border: none;
            cursor: pointer;
            color: inherit;
            opacity: .5;
            line-height: 1;
            transition: opacity 0.1s ease;
          }
          .dismiss:hover { opacity: 1; }
          .dismiss svg { display: block; }
        </style>
        <div class="banner" role="alert">
          ${header ? '<div class="header">' + header + '</div>' : ''}
          <div class="body"><slot></slot></div>
          ${dismissible ? '<button class="dismiss" aria-label="Dismiss"><svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1.5 1.5l7 7M8.5 1.5l-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>' : ''}
        </div>
      `;
    }
  }

  customElements.define('canvas-banner', CanvasBanner);
}
