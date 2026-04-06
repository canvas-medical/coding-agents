if (!customElements.get('canvas-checkbox')) {
  class CanvasCheckbox extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'checked', 'disabled', 'name', 'value'];
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
            min-height: var(--canvas-checkbox-min-height, auto);
            min-width: var(--canvas-checkbox-min-width, auto);
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
            width: 17px;
            height: 17px;
            cursor: pointer;
            z-index: 3;
            margin: 0;
          }

          :host([disabled]) input { cursor: not-allowed; }

          .box {
            position: relative;
            flex-shrink: 0;
            width: 17px;
            height: 17px;
            background: #FFFFFF;
            border: 1px solid #d4d4d5;
            border-radius: .21428571rem;
            transition: border 0.1s ease, background 0.1s ease;
            box-sizing: border-box;
          }

          .box::after {
            content: "";
            position: absolute;
            top: 1px;
            left: 4px;
            width: 3.5px;
            height: 8px;
            border: solid rgba(0, 0, 0, 0.95);
            border-width: 0 3px 3px 0;
            transform: rotate(45deg);
            opacity: 0;
            transition: opacity 0.1s ease;
          }

          input:checked ~ .box {
            border-color: rgba(34, 36, 38, 0.35);
          }

          input:checked ~ .box::after { opacity: 1; }

          :host(:hover) .box { border-color: rgba(34, 36, 38, 0.35); }

          input:focus ~ .box,
          :host(:hover) input:focus ~ .box {
            border-color: #85b7d9;
          }

          .label-text {
            padding-left: 8px;
            color: rgba(0, 0, 0, 0.87);
          }
        </style>
        <input type="checkbox" part="input">
        <span class="box"></span>
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
          this._input.value = this.getAttribute('value') || 'on';
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
      return this.getAttribute('value') || 'on';
    }

    get name() {
      return this.getAttribute('name');
    }

    _syncAll() {
      this._labelText.textContent = this.getAttribute('label') || '';
      this._input.name = this.getAttribute('name') || '';
      this._input.value = this.getAttribute('value') || 'on';
      this._input.checked = this.hasAttribute('checked');
      this._input.disabled = this.hasAttribute('disabled');
      this._syncFormValue();
    }

    _syncFormValue() {
      if (this._input.checked) {
        this._internals.setFormValue(this.getAttribute('value') || 'on');
      } else {
        this._internals.setFormValue(null);
      }
    }

    _onClick(e) {
      if (this.hasAttribute('disabled')) return;
      if (e.target === this._input) return;
      this._input.checked = !this._input.checked;
      this._input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    _onChange(e) {
      e.stopPropagation();
      if (this._input.checked) {
        this.setAttribute('checked', '');
      } else {
        this.removeAttribute('checked');
      }
      this._syncFormValue();
      this.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
    }
  }

  customElements.define('canvas-checkbox', CanvasCheckbox);
}
