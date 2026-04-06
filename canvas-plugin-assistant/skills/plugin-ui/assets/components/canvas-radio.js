if (!customElements.get('canvas-radio')) {
  class CanvasRadio extends HTMLElement {
    static get observedAttributes() {
      return ['name', 'label', 'value', 'checked', 'disabled'];
    }

    static formAssociated = true;

    constructor() {
      super();
      this._internals = this.attachInternals();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-flex;
            align-items: center;
            min-height: var(--canvas-radio-min-height, auto);
            min-width: var(--canvas-radio-min-width, auto);
            padding: 4px 8px;
            cursor: pointer;
            font-size: 1rem;
            line-height: 1;
            font-family: lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
          }

          :host([disabled]) {
            cursor: not-allowed;
            opacity: 0.45;
          }

          input {
            position: absolute;
            opacity: 0;
            width: 15px;
            height: 15px;
            cursor: pointer;
            z-index: 3;
            margin: 0;
          }

          :host([disabled]) input { cursor: not-allowed; }

          .dot {
            position: relative;
            flex-shrink: 0;
            box-sizing: content-box;
            width: 15px;
            height: 15px;
            background: #FFFFFF;
            border: 1px solid #d4d4d5;
            border-radius: 500rem;
            transition: border 0.1s ease;
          }

          .dot::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 15px;
            height: 15px;
            border-radius: 500rem;
            background-color: rgba(0, 0, 0, 0.87);
            transform: scale(.46666667);
            opacity: 0;
            transition: opacity 0.1s ease;
          }

          input:checked + .dot {
            border-color: rgba(34, 36, 38, 0.35);
          }

          input:checked + .dot::after { opacity: 1; }

          :host(:hover) .dot { border-color: rgba(34, 36, 38, 0.35); }

          input:focus + .dot,
          :host(:hover) input:focus + .dot {
            border-color: #85b7d9;
          }

          .label-text {
            padding-left: 8px;
            color: rgba(0, 0, 0, 0.87);
          }
        </style>
        <input type="radio" part="input">
        <span class="dot"></span>
        <span class="label-text" part="label"></span>
      `;
      this._input = this.shadowRoot.querySelector('input');
      this._labelText = this.shadowRoot.querySelector('.label-text');
      this._boundOnChange = this._onChange.bind(this);
      this._boundOnClick = this._onClick.bind(this);
    }

    connectedCallback() {
      this._input.addEventListener('change', this._boundOnChange);
      this.addEventListener('click', this._boundOnClick);
      this._syncAll();
    }

    disconnectedCallback() {
      this._input.removeEventListener('change', this._boundOnChange);
      this.removeEventListener('click', this._boundOnClick);
    }

    attributeChangedCallback(name) {
      switch (name) {
        case 'label':
          this._labelText.textContent = this.getAttribute('label') || '';
          break;
        case 'checked':
          this._input.checked = this.hasAttribute('checked');
          this._syncFormValue();
          break;
        case 'disabled':
          this._input.disabled = this.hasAttribute('disabled');
          break;
        case 'name':
          this._input.name = this.getAttribute('name') || '';
          break;
        case 'value':
          this._input.value = this.getAttribute('value') || '';
          this._syncFormValue();
          break;
      }
    }

    get checked() {
      return this._input.checked;
    }

    set checked(v) {
      if (v) {
        this.setAttribute('checked', '');
      } else {
        this.removeAttribute('checked');
      }
      this._input.checked = v;
      this._syncFormValue();
    }

    get value() {
      return this.getAttribute('value') || '';
    }

    get name() {
      return this.getAttribute('name');
    }

    _syncAll() {
      this._labelText.textContent = this.getAttribute('label') || '';
      this._input.name = this.getAttribute('name') || '';
      this._input.value = this.getAttribute('value') || '';
      this._input.checked = this.hasAttribute('checked');
      this._input.disabled = this.hasAttribute('disabled');
      this._syncFormValue();
    }

    _syncFormValue() {
      if (this._input.checked) {
        this._internals.setFormValue(this.getAttribute('value') || '');
      } else {
        this._internals.setFormValue(null);
      }
    }

    _onClick(e) {
      if (this.hasAttribute('disabled')) return;
      if (e.target === this._input) return;
      this._input.checked = true;
      this._input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    _onChange(e) {
      e.stopPropagation();
      this.setAttribute('checked', '');
      this._syncFormValue();
      this._uncheckSiblings();
      this.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
    }

    _uncheckSiblings() {
      var name = this.getAttribute('name');
      if (!name) return;
      var parent = this.parentElement;
      if (!parent) return;
      var siblings = parent.querySelectorAll('canvas-radio[name="' + name + '"]');
      for (var i = 0; i < siblings.length; i++) {
        if (siblings[i] !== this && siblings[i].hasAttribute('checked')) {
          siblings[i].removeAttribute('checked');
          siblings[i]._input.checked = false;
          siblings[i]._syncFormValue();
        }
      }
    }
  }

  customElements.define('canvas-radio', CanvasRadio);
}
