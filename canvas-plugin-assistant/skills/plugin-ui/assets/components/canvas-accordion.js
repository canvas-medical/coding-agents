/* canvas-accordion-title: title bar content. Has its own shadow DOM slot so children render. */
if (!customElements.get('canvas-accordion-title')) {
  class CanvasAccordionTitle extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = '<style>:host{display:flex;align-items:center;gap:8px;flex:1;min-width:0}</style><slot></slot>';
    }
  }
  customElements.define('canvas-accordion-title', CanvasAccordionTitle);
}

/* canvas-accordion-content: collapsible content area, hidden by default */
if (!customElements.get('canvas-accordion-content')) {
  class CanvasAccordionContent extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = '<style>:host{display:none;padding:.5em 0 1em}:host([visible]){display:block}</style><slot></slot>';
    }
    connectedCallback() {
      this.setAttribute('role', 'region');
    }
  }
  customElements.define('canvas-accordion-content', CanvasAccordionContent);
}

/* canvas-accordion-item: collapsible section with chevron, title slot, and content slot */
if (!customElements.get('canvas-accordion-item')) {
  class CanvasAccordionItem extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._isOpen = false;
    }

    connectedCallback() {
      var self = this;
      this._isOpen = this.hasAttribute('open');
      this._render();
      this._bindEvents();
      setTimeout(function() {
        self._assignSlots();
        if (self._isOpen) self._expand(false);
      }, 0);
    }

    get open() { return this._isOpen; }
    set open(val) {
      if (val) this._expand(true);
      else this._collapse(true);
    }

    toggle() {
      if (this._isOpen) this._collapse(true);
      else this._expand(true);
    }

    _render() {
      this.shadowRoot.innerHTML = `
        <style>
          :host { display: block; }
          .title {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 7px 0;
            font-size: 1.125em;
            font-weight: 700;
            line-height: 1.14285714em;
            color: rgba(0, 0, 0, 0.87);
            background: transparent;
            border: none;
            width: 100%;
            text-align: left;
            cursor: pointer;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            transition: color 0.1s ease;
          }
          .title:hover { color: rgba(0, 0, 0, 0.95); }
          .title:focus-visible {
            outline: 2px solid #2185d0;
            outline-offset: -2px;
          }
          .icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 10px;
            height: 10px;
            flex-shrink: 0;
            transition: transform 0.1s ease;
            transform: rotate(-90deg);
          }
          :host([open]) .icon {
            transform: rotate(0deg);
          }
        </style>
        <div class="title" role="button" tabindex="0" aria-expanded="false">
          <span class="icon"><svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor"><path d="M1 0h8a1 1 0 01.7 1.7l-4 4a1 1 0 01-1.4 0l-4-4A1 1 0 011 0z"/></svg></span>
          <slot name="title"></slot>
        </div>
        <slot name="content"></slot>
      `;
    }

    _assignSlots() {
      var titleEl = this.querySelector('canvas-accordion-title');
      if (titleEl) titleEl.setAttribute('slot', 'title');
      var contentEl = this.querySelector('canvas-accordion-content');
      if (contentEl) contentEl.setAttribute('slot', 'content');
    }

    _bindEvents() {
      var self = this;
      var title = this.shadowRoot.querySelector('.title');

      title.addEventListener('click', function() {
        self.toggle();
      });

      title.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          self.toggle();
        }
      });
    }

    _expand(fireEvent) {
      this._isOpen = true;
      this.setAttribute('open', '');
      this.shadowRoot.querySelector('.title').setAttribute('aria-expanded', 'true');
      var content = this.querySelector('canvas-accordion-content');
      if (content) content.setAttribute('visible', '');
      if (fireEvent) {
        this.dispatchEvent(new CustomEvent('toggle', { bubbles: true, composed: true, detail: { open: true } }));
      }
    }

    _collapse(fireEvent) {
      this._isOpen = false;
      this.removeAttribute('open');
      this.shadowRoot.querySelector('.title').setAttribute('aria-expanded', 'false');
      var content = this.querySelector('canvas-accordion-content');
      if (content) content.removeAttribute('visible');
      if (fireEvent) {
        this.dispatchEvent(new CustomEvent('toggle', { bubbles: true, composed: true, detail: { open: false } }));
      }
    }
  }
  customElements.define('canvas-accordion-item', CanvasAccordionItem);
}

/* canvas-accordion: thin container, no shadow DOM */
if (!customElements.get('canvas-accordion')) {
  class CanvasAccordion extends HTMLElement {
    constructor() { super(); }
    connectedCallback() { this.style.display = 'block'; this.style.width = '100%'; }
  }
  customElements.define('canvas-accordion', CanvasAccordion);
}
