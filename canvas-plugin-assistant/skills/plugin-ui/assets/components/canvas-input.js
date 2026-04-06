if (!customElements.get('canvas-input')) {
  class CanvasInput extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'placeholder', 'multiline', 'rows', 'required', 'error', 'disabled', 'value', 'name', 'type'];
    }

    static formAssociated = true;

    constructor() {
      super();
      this._internals = this.attachInternals();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
          }

          label {
            display: none;
            margin: 0 0 .28571429rem 0;
            font-size: var(--canvas-input-label-font-size, .92857143em);
            font-weight: var(--canvas-input-label-font-weight, var(--font-weight-bold, 700));
            font-family: var(--canvas-input-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            color: var(--canvas-input-label-color, var(--color-text, rgba(0, 0, 0, 0.87)));
            text-transform: none;
            line-height: 1em;
          }

          :host([label]) label { display: block; }

          input, textarea {
            width: 100%;
            padding: var(--canvas-input-padding, .67857143em 1em);
            font-size: var(--canvas-input-font-size, 1em);
            font-family: var(--canvas-input-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            line-height: var(--canvas-input-line-height, 1.21428571em);
            color: var(--canvas-input-color, var(--color-text, rgba(0, 0, 0, 0.87)));
            background: var(--canvas-input-bg, var(--color-surface, #FFFFFF));
            border: var(--canvas-input-border, 1px solid rgba(34, 36, 38, 0.15));
            border-radius: var(--canvas-input-radius, var(--radius, .28571429rem));
            transition: border-color 0.1s ease, box-shadow 0.1s ease;
            box-shadow: none;
            outline: 0;
            box-sizing: border-box;
          }

          input:focus, textarea:focus {
            border-color: var(--canvas-input-focus-border, #85b7d9);
            background: var(--canvas-input-bg, var(--color-surface, #FFFFFF));
            color: rgba(0, 0, 0, 0.8);
            box-shadow: none;
            outline: none;
          }

          input::placeholder, textarea::placeholder {
            color: var(--canvas-input-placeholder, rgba(191, 191, 191, 0.87));
          }

          input:focus::placeholder, textarea:focus::placeholder {
            color: var(--canvas-input-focus-placeholder, rgba(115, 115, 115, 0.87));
          }

          input:disabled, textarea:disabled {
            background: var(--canvas-input-disabled-bg, var(--color-bg, #F5F5F5));
            cursor: not-allowed;
          }

          textarea {
            min-height: var(--canvas-input-textarea-min-height, 80px);
            resize: vertical;
          }

          :host(:not([multiline])) textarea { display: none; }
          :host([multiline]) input { display: none; }

          /* Error state */
          .error-msg {
            display: none;
            font-size: .92857143em;
            color: var(--canvas-input-error-text, #9f3a38);
            line-height: 1em;
            font-weight: var(--canvas-input-label-font-weight, var(--font-weight-bold, 700));
            font-family: var(--canvas-input-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            margin-top: .28571429rem;
          }

          :host([error]) .error-msg { display: block; }

          :host([error]) label {
            color: var(--canvas-input-error-text, #9f3a38);
          }

          :host([error]) input,
          :host([error]) textarea {
            background: var(--canvas-input-error-bg, #fff6f6);
            border-color: var(--canvas-input-error-border, #e0b4b4);
            color: var(--canvas-input-error-text, #9f3a38);
          }

          :host([error]) input::placeholder,
          :host([error]) textarea::placeholder {
            color: var(--canvas-input-error-border, #e0b4b4);
          }
        </style>
        <label part="label"></label>
        <input part="input" type="text">
        <textarea part="textarea"></textarea>
        <span class="error-msg" part="error" aria-live="polite"></span>
      `;
      this._label = this.shadowRoot.querySelector('label');
      this._input = this.shadowRoot.querySelector('input');
      this._textarea = this.shadowRoot.querySelector('textarea');
      this._errorMsg = this.shadowRoot.querySelector('.error-msg');
      this._boundOnInput = this._onInput.bind(this);
      this._boundOnChange = this._onChange.bind(this);
    }

    connectedCallback() {
      this._input.addEventListener('input', this._boundOnInput);
      this._input.addEventListener('change', this._boundOnChange);
      this._textarea.addEventListener('input', this._boundOnInput);
      this._textarea.addEventListener('change', this._boundOnChange);
      this._syncAll();
    }

    disconnectedCallback() {
      this._input.removeEventListener('input', this._boundOnInput);
      this._input.removeEventListener('change', this._boundOnChange);
      this._textarea.removeEventListener('input', this._boundOnInput);
      this._textarea.removeEventListener('change', this._boundOnChange);
    }

    attributeChangedCallback(name, oldVal, newVal) {
      switch (name) {
        case 'label':
          this._label.textContent = newVal || '';
          break;
        case 'placeholder':
          this._input.placeholder = newVal || '';
          this._textarea.placeholder = newVal || '';
          break;
        case 'rows':
          this._textarea.rows = newVal || 4;
          break;
        case 'required':
          var req = this.hasAttribute('required');
          this._input.required = req;
          this._textarea.required = req;
          this._input.setAttribute('aria-required', req);
          this._textarea.setAttribute('aria-required', req);
          break;
        case 'disabled':
          var dis = this.hasAttribute('disabled');
          this._input.disabled = dis;
          this._textarea.disabled = dis;
          break;
        case 'error':
          this._syncError();
          break;
        case 'value':
          if (newVal !== null) {
            this._activeEl.value = newVal;
            this._internals.setFormValue(newVal);
          }
          break;
        case 'name':
          break;
        case 'type':
          this._input.type = newVal || 'text';
          break;
      }
    }

    get _activeEl() {
      return this.hasAttribute('multiline') ? this._textarea : this._input;
    }

    get value() {
      return this._activeEl.value;
    }

    set value(v) {
      this._activeEl.value = v;
      this._internals.setFormValue(v);
    }

    get name() {
      return this.getAttribute('name');
    }

    _syncAll() {
      this._label.textContent = this.getAttribute('label') || '';
      this._input.placeholder = this.getAttribute('placeholder') || '';
      this._textarea.placeholder = this.getAttribute('placeholder') || '';
      this._textarea.rows = this.getAttribute('rows') || 4;
      this._input.type = this.getAttribute('type') || 'text';

      var req = this.hasAttribute('required');
      this._input.required = req;
      this._textarea.required = req;
      this._input.setAttribute('aria-required', req);
      this._textarea.setAttribute('aria-required', req);

      var dis = this.hasAttribute('disabled');
      this._input.disabled = dis;
      this._textarea.disabled = dis;

      var val = this.getAttribute('value');
      if (val !== null) {
        this._input.value = val;
        this._textarea.value = val;
        this._internals.setFormValue(val);
      }

      this._syncError();
    }

    _syncError() {
      var err = this.getAttribute('error');
      if (err) {
        this._errorMsg.textContent = err;
        this._input.setAttribute('aria-invalid', 'true');
        this._textarea.setAttribute('aria-invalid', 'true');
        this._errorMsg.id = 'err';
        this._input.setAttribute('aria-describedby', 'err');
        this._textarea.setAttribute('aria-describedby', 'err');
      } else {
        this._errorMsg.textContent = '';
        this._input.removeAttribute('aria-invalid');
        this._textarea.removeAttribute('aria-invalid');
        this._input.removeAttribute('aria-describedby');
        this._textarea.removeAttribute('aria-describedby');
      }
    }

    _onInput(e) {
      e.stopPropagation();
      this._internals.setFormValue(this._activeEl.value);
      this.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
    }

    _onChange(e) {
      e.stopPropagation();
      this._internals.setFormValue(this._activeEl.value);
      this.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
    }
  }

  customElements.define('canvas-input', CanvasInput);
}
