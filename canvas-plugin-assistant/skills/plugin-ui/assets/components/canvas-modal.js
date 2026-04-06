/*
  canvas-modal compositional API

  <canvas-modal> - overlay container. Attributes: size, persistent
  <canvas-modal-header> - optional header bar. Attributes: dismissable
  <canvas-modal-content> - optional padded content area. Attributes: flush
  <canvas-modal-footer> - optional actions footer. No attributes.

  All three inner elements are optional. Without them, children render
  directly inside the modal box with no padding or structure.
*/

/* canvas-modal-header: title bar with optional close button */
if (!customElements.get('canvas-modal-header')) {
  class CanvasModalHeader extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: flex; align-items: center; justify-content: space-between;
            padding: 1.25rem 1.5rem;
            font-size: 1.42857143rem; font-weight: 700; line-height: 1.28571429em;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: rgba(0, 0, 0, 0.85);
            border-bottom: 1px solid rgba(34, 36, 38, 0.15);
          }
          .title { flex: 1; }
          .close {
            display: none; align-items: center; justify-content: center;
            width: 2rem; height: 2rem; flex-shrink: 0;
            padding: 0; margin: 0 -.5rem 0 .5rem;
            background: transparent; border: none; border-radius: var(--radius, .28571429rem);
            cursor: pointer; color: rgba(0, 0, 0, 0.6);
            transition: color 0.1s ease, background 0.1s ease;
          }
          .close:hover { color: rgba(0, 0, 0, 0.87); background: rgba(0, 0, 0, 0.05); }
          .close svg { display: block; }
          :host([dismissable]) .close { display: inline-flex; }
        </style>
        <span class="title"><slot></slot></span>
        <button class="close" aria-label="Close">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1.5 1.5l11 11M12.5 1.5l-11 11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      `;
    }
    connectedCallback() {
      var self = this;
      this.shadowRoot.querySelector('.close').addEventListener('click', function() {
        var modal = self.closest('canvas-modal');
        if (modal) modal.dismiss();
      });
    }
  }
  customElements.define('canvas-modal-header', CanvasModalHeader);
}

/* canvas-modal-content: padded content area */
if (!customElements.get('canvas-modal-content')) {
  class CanvasModalContent extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: flex; flex-direction: column; min-height: 0;
            padding: 1.5rem;
            font-size: 1em; line-height: 1.4;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: var(--color-text, rgba(0, 0, 0, 0.87));
          }
          :host([flush]) { padding: 0; }
          ::slotted(*) { flex-shrink: 0; }
          ::slotted([data-fill]) { flex: 1; min-height: 0; }
        </style>
        <slot></slot>
      `;
    }
  }
  customElements.define('canvas-modal-content', CanvasModalContent);
}

/* canvas-modal-footer: actions bar */
if (!customElements.get('canvas-modal-footer')) {
  class CanvasModalFooter extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: flex; justify-content: flex-end; gap: 8px;
            padding: 1rem;
            background: #f9fafb;
            border-top: 1px solid rgba(34, 36, 38, 0.15);
            border-radius: 0 0 var(--radius, .28571429rem) var(--radius, .28571429rem);
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
          }
        </style>
        <slot></slot>
      `;
    }
  }
  customElements.define('canvas-modal-footer', CanvasModalFooter);
}

/* canvas-modal: the overlay container */
if (!customElements.get('canvas-modal')) {
  class CanvasModal extends HTMLElement {
    static get observedAttributes() {
      return ['size'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._isOpen = false;
      this._previousFocus = null;
      this._onKeyDown = this._onKeyDown.bind(this);
    }

    connectedCallback() {
      this._render();
      this._bindEvents();
    }

    attributeChangedCallback() {
      if (this.shadowRoot.querySelector('.modal')) {
        this._render();
        this._bindEvents();
      }
    }

    get isOpen() { return this._isOpen; }

    open() {
      if (this._isOpen) return;
      this._isOpen = true;
      this._previousFocus = document.activeElement;
      var backdrop = this.shadowRoot.querySelector('.backdrop');
      var scroll = this.shadowRoot.querySelector('.scroll');
      backdrop.classList.add('active');
      scroll.classList.add('active');
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', this._onKeyDown);
      var self = this;
      requestAnimationFrame(function() { self._focusFirst(); });
      this.dispatchEvent(new CustomEvent('open', { bubbles: true, composed: true }));
    }

    dismiss() {
      if (!this._isOpen) return;
      this._isOpen = false;
      var backdrop = this.shadowRoot.querySelector('.backdrop');
      var scroll = this.shadowRoot.querySelector('.scroll');
      backdrop.classList.remove('active');
      scroll.classList.remove('active');
      document.body.style.overflow = '';
      document.removeEventListener('keydown', this._onKeyDown);
      if (this._previousFocus && this._previousFocus.focus) {
        this._previousFocus.focus();
      }
      this._previousFocus = null;
      this.dispatchEvent(new CustomEvent('dismiss', { bubbles: true, composed: true }));
    }

    _render() {
      var size = this.getAttribute('size') || 'medium';
      var sizeClass = 'modal modal-' + size;

      this.shadowRoot.innerHTML = `
        <style>
          :host { display: contents; }
          .backdrop {
            display: none; position: fixed; inset: 0;
            background-color: rgba(0, 0, 0, 0.5); z-index: 1000;
          }
          .backdrop.active { display: block; }
          .scroll {
            display: none; position: fixed; inset: 0;
            overflow-y: auto; z-index: 1001; padding: 2rem;
          }
          .scroll.active { display: flex; align-items: flex-start; justify-content: center; }
          .modal {
            position: relative;
            display: flex; flex-direction: column;
            background: var(--color-surface, #FFFFFF);
            border: none;
            border-radius: var(--radius, .28571429rem);
            box-shadow: 1px 3px 3px 0 rgba(0, 0, 0, 0.2), 1px 3px 15px 2px rgba(0, 0, 0, 0.2);
            margin: auto;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
          }
          .modal-small { width: 35rem; max-width: calc(100vw - 4rem); }
          .modal-medium { width: 52.5rem; max-width: calc(100vw - 4rem); }
          .modal-full { width: calc(100vw - 6rem); min-height: calc(100vh - 6rem); }
          ::slotted(canvas-modal-content) { flex: 1 0 auto; }
        </style>
        <div class="backdrop"></div>
        <div class="scroll">
          <div class="${sizeClass}" role="dialog" aria-modal="true">
            <slot></slot>
          </div>
        </div>
      `;
    }

    _bindEvents() {
      var self = this;
      var scroll = this.shadowRoot.querySelector('.scroll');
      scroll.addEventListener('click', function(e) {
        if (self.hasAttribute('persistent')) return;
        if (e.target === scroll) self.dismiss();
      });
    }

    _onKeyDown(e) {
      if (e.key === 'Escape') {
        if (this.hasAttribute('persistent')) return;
        e.preventDefault();
        this.dismiss();
        return;
      }
      if (e.key === 'Tab') {
        this._trapFocus(e);
      }
    }

    _getFocusable() {
      var modal = this.shadowRoot.querySelector('.modal');
      var focusable = [];
      var slot = modal.querySelector('slot');
      if (!slot) return focusable;
      var assigned = slot.assignedElements({ flatten: true });
      for (var i = 0; i < assigned.length; i++) {
        this._collectFocusable(assigned[i], focusable);
      }
      return focusable;
    }

    _collectFocusable(el, list) {
      if (this._isFocusable(el)) list.push(el);
      if (el.shadowRoot) {
        var shadowChildren = el.shadowRoot.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        for (var i = 0; i < shadowChildren.length; i++) {
          if (this._isFocusable(shadowChildren[i])) list.push(shadowChildren[i]);
        }
      }
      var children = el.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), canvas-button, canvas-input, canvas-dropdown, canvas-combobox, canvas-multi-select');
      for (var i = 0; i < children.length; i++) {
        this._collectFocusable(children[i], list);
      }
    }

    _isFocusable(el) {
      if (el.disabled) return false;
      if (el.tabIndex < 0) return false;
      return true;
    }

    _trapFocus(e) {
      var focusable = this._getFocusable();
      if (focusable.length === 0) return;
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first || (first.shadowRoot && first.shadowRoot.activeElement)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last || (last.shadowRoot && last.shadowRoot.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    _focusFirst() {
      var focusable = this._getFocusable();
      if (focusable.length > 0) focusable[0].focus();
    }
  }

  customElements.define('canvas-modal', CanvasModal);
}
