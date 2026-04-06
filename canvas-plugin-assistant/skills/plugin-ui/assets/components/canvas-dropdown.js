if (!customElements.get('canvas-option')) {
  class CanvasOption extends HTMLElement {
    constructor() { super(); }
    connectedCallback() { this.style.display = 'none'; }
  }
  customElements.define('canvas-option', CanvasOption);
}

if (!customElements.get('canvas-dropdown')) {
  class CanvasDropdown extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'placeholder', 'value', 'disabled', 'required', 'error', 'name', 'size'];
    }

    static get formAssociated() { return true; }

    constructor() {
      super();
      this._internals = this.attachInternals();
      this.attachShadow({ mode: 'open' });
      this._options = [];
      this._highlighted = -1;
      this._selectedValue = null;
      this._selectedText = '';
      this._open = false;
      this._onDocClick = this._onDocClick.bind(this);
    }

    connectedCallback() {
      var self = this;
      setTimeout(function() {
        self._readOptions();
        self._render();
        self._bindEvents();
      }, 0);
      document.addEventListener('click', this._onDocClick);
    }

    disconnectedCallback() {
      document.removeEventListener('click', this._onDocClick);
    }

    attributeChangedCallback(name) {
      if (name === 'value') {
        var val = this.getAttribute('value');
        if (val !== this._selectedValue) this._selectByValue(val);
      }
      if (name === 'label' || name === 'placeholder' || name === 'error' || name === 'disabled') {
        if (this.shadowRoot.querySelector('.dropdown')) {
          this._render();
          this._bindEvents();
        }
      }
    }

    get value() { return this._selectedValue || ''; }
    set value(v) {
      this._selectByValue(v);
      this.setAttribute('value', v || '');
    }

    get name() { return this.getAttribute('name'); }

    _readOptions() {
      this._options = [];
      var opts = this.querySelectorAll('canvas-option');
      for (var i = 0; i < opts.length; i++) {
        var opt = opts[i];
        this._options.push({
          value: opt.getAttribute('value') || opt.textContent.trim(),
          label: opt.getAttribute('label') || opt.textContent.trim(),
          html: opt.innerHTML,
          disabled: opt.hasAttribute('disabled'),
          selected: opt.hasAttribute('selected')
        });
      }
      var preselected = this._options.find(function(o) { return o.selected; });
      if (preselected) {
        this._selectedValue = preselected.value;
        this._selectedText = preselected.label;
        this._internals.setFormValue(preselected.value);
      }
    }

    _render() {
      var label = this.getAttribute('label');
      var placeholder = this.getAttribute('placeholder') || '';
      var error = this.getAttribute('error');
      var disabled = this.hasAttribute('disabled');
      var displayText = this._selectedText || '';
      var isPlaceholder = !displayText;

      var optionsHtml = '';
      for (var i = 0; i < this._options.length; i++) {
        var o = this._options[i];
        var classes = 'option';
        if (o.value === this._selectedValue) classes += ' selected';
        var attrs = 'role="option" data-value="' + o.value + '" data-index="' + i + '"';
        if (o.disabled) attrs += ' aria-disabled="true"';
        if (o.value === this._selectedValue) attrs += ' aria-selected="true"';
        optionsHtml += '<li class="' + classes + '" ' + attrs + '>' + o.html + '</li>';
      }

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
          }

          .label {
            display: block;
            margin-bottom: .28571429rem;
            font-size: .92857143em;
            font-weight: 700;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: var(--color-text, rgba(0, 0, 0, 0.87));
            line-height: 1em;
          }

          :host([error]) .label { color: #9f3a38; }

          .dropdown {
            position: relative;
            display: flex;
            align-items: center;
            width: 100%;
            padding: .67857143em 2.1em .67857143em 1em;
            font-size: 1em;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            line-height: 1.21428571em;
            color: var(--color-text, rgba(0, 0, 0, 0.87));
            background: var(--color-surface, #FFFFFF);
            border: 1px solid rgba(34, 36, 38, 0.15);
            border-radius: var(--radius, .28571429rem);
            cursor: pointer;
            outline: none;
            transition: border-color 0.1s ease, box-shadow 0.1s ease, border-radius 0.1s ease;
            box-sizing: border-box;
          }

          .dropdown:focus {
            border-color: #96c8da;
          }

          .dropdown.open {
            border-color: #96c8da;
            border-bottom-color: transparent;
            border-radius: var(--radius, .28571429rem) var(--radius, .28571429rem) 0 0;
            z-index: 10;
          }

          :host([size="sm"]) .dropdown {
            font-size: .75em;
          }

          :host([disabled]) .dropdown {
            opacity: 0.45;
            cursor: default;
            pointer-events: none;
          }

          :host([error]) .dropdown {
            background: #fff6f6;
            border-color: #e0b4b4;
          }

          .text {
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--color-text, rgba(0, 0, 0, 0.87));
          }

          .text.placeholder {
            color: rgba(191, 191, 191, 0.87);
          }

          .arrow {
            position: absolute;
            top: 50%;
            right: 1em;
            transform: translateY(-50%);
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid rgba(0, 0, 0, 0.8);
            pointer-events: none;
          }

          .menu {
            display: none;
            position: absolute;
            top: 100%;
            left: -1px;
            right: -1px;
            max-height: 16.02857143rem;
            overflow-y: auto;
            background: var(--color-surface, #FFFFFF);
            border: 1px solid #96c8da;
            border-top: none;
            border-radius: 0 0 var(--radius, .28571429rem) var(--radius, .28571429rem);
            box-shadow: 0 0px 3px 0 rgba(34, 36, 38, 0.06);
            z-index: 11;
            list-style: none;
            margin: 0;
            padding: 0;
          }

          .dropdown.open .menu {
            display: block;
          }

          .option {
            padding: .78571429rem 1.14285714rem;
            font-size: 1rem;
            line-height: 1.0625rem;
            color: var(--color-text, rgba(0, 0, 0, 0.87));
            cursor: pointer;
            border-top: 1px solid #fafafa;
            transition: background 0.1s ease;
          }

          .option:first-child { border-top: none; }

          .option:hover,
          .option.highlighted {
            background: rgba(0, 0, 0, 0.05);
            color: rgba(0, 0, 0, 0.95);
          }

          .option.selected {
            background: rgba(0, 0, 0, 0.05);
            color: rgba(0, 0, 0, 0.95);
            font-weight: 700;
          }

          .option[aria-disabled="true"] {
            color: #767676;
            cursor: not-allowed;
          }

          .option[aria-disabled="true"]:hover {
            background: transparent;
          }

          .error-text {
            margin-top: .28571429rem;
            font-size: .92857143em;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: #9f3a38;
            line-height: 1.4285em;
          }
        </style>
        ${label ? '<span class="label">' + label + '</span>' : ''}
        <div class="dropdown" tabindex="${disabled ? '-1' : '0'}" role="combobox" aria-expanded="false" aria-haspopup="listbox">
          <span class="text${isPlaceholder ? ' placeholder' : ''}">${isPlaceholder ? placeholder : displayText}</span>
          <span class="arrow"></span>
          <ul class="menu" role="listbox">${optionsHtml}</ul>
        </div>
        ${error ? '<span class="error-text">' + error + '</span>' : ''}
      `;
    }

    _bindEvents() {
      var self = this;
      var dd = this.shadowRoot.querySelector('.dropdown');

      dd.addEventListener('click', function(e) {
        if (self.hasAttribute('disabled')) return;
        var opt = e.target.closest('.option');
        if (opt) {
          if (opt.getAttribute('aria-disabled') === 'true') return;
          self._selectByValue(opt.dataset.value);
          self._close();
        } else {
          if (self._open) self._close();
          else self._openMenu();
        }
      });

      dd.addEventListener('keydown', function(e) {
        if (self.hasAttribute('disabled')) return;
        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            if (!self._open) self._openMenu();
            self._highlightNext(1);
            break;
          case 'ArrowUp':
            e.preventDefault();
            if (!self._open) self._openMenu();
            self._highlightNext(-1);
            break;
          case 'Enter':
          case ' ':
            e.preventDefault();
            if (!self._open) {
              self._openMenu();
            } else if (self._highlighted >= 0) {
              var opts = self.shadowRoot.querySelectorAll('.option:not([aria-disabled="true"])');
              if (opts[self._highlighted]) {
                self._selectByValue(opts[self._highlighted].dataset.value);
                self._close();
              }
            }
            break;
          case 'Escape':
            e.preventDefault();
            self._close();
            break;
          case 'Home':
            if (self._open) {
              e.preventDefault();
              self._highlightIndex(0);
            }
            break;
          case 'End':
            if (self._open) {
              e.preventDefault();
              var opts = self.shadowRoot.querySelectorAll('.option:not([aria-disabled="true"])');
              self._highlightIndex(opts.length - 1);
            }
            break;
          case 'Tab':
            if (self._open) {
              if (self._highlighted >= 0) {
                var opts = self.shadowRoot.querySelectorAll('.option:not([aria-disabled="true"])');
                if (opts[self._highlighted]) {
                  self._selectByValue(opts[self._highlighted].dataset.value);
                }
              }
              self._close();
            }
            break;
        }
      });
    }

    _openMenu() {
      this._open = true;
      this._highlighted = -1;
      var dd = this.shadowRoot.querySelector('.dropdown');
      dd.classList.add('open');
      dd.setAttribute('aria-expanded', 'true');
    }

    _close() {
      this._open = false;
      this._highlighted = -1;
      var dd = this.shadowRoot.querySelector('.dropdown');
      dd.classList.remove('open');
      dd.setAttribute('aria-expanded', 'false');
      this._clearHighlight();
    }

    _onDocClick(e) {
      if (!this.contains(e.target) && !this.shadowRoot.contains(e.target)) {
        if (this._open) this._close();
      }
    }

    _selectByValue(val) {
      var opt = this._options.find(function(o) { return o.value === val; });
      if (!opt || opt.disabled) return;
      this._selectedValue = opt.value;
      this._selectedText = opt.label;
      this._internals.setFormValue(opt.value);

      var text = this.shadowRoot.querySelector('.text');
      if (text) {
        text.textContent = opt.label;
        text.classList.remove('placeholder');
      }

      var items = this.shadowRoot.querySelectorAll('.option');
      for (var i = 0; i < items.length; i++) {
        if (items[i].dataset.value === val) {
          items[i].classList.add('selected');
          items[i].setAttribute('aria-selected', 'true');
        } else {
          items[i].classList.remove('selected');
          items[i].removeAttribute('aria-selected');
        }
      }

      this.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true }));
    }

    _highlightNext(dir) {
      var opts = this.shadowRoot.querySelectorAll('.option:not([aria-disabled="true"])');
      if (opts.length === 0) return;
      this._highlighted += dir;
      if (this._highlighted < 0) this._highlighted = opts.length - 1;
      if (this._highlighted >= opts.length) this._highlighted = 0;
      this._applyHighlight(opts);
    }

    _highlightIndex(index) {
      var opts = this.shadowRoot.querySelectorAll('.option:not([aria-disabled="true"])');
      if (index < 0 || index >= opts.length) return;
      this._highlighted = index;
      this._applyHighlight(opts);
    }

    _applyHighlight(opts) {
      this._clearHighlight();
      if (this._highlighted >= 0 && opts[this._highlighted]) {
        opts[this._highlighted].classList.add('highlighted');
        opts[this._highlighted].scrollIntoView({ block: 'nearest' });
        var dd = this.shadowRoot.querySelector('.dropdown');
        dd.setAttribute('aria-activedescendant', 'opt-' + this._highlighted);
      }
    }

    _clearHighlight() {
      var items = this.shadowRoot.querySelectorAll('.option.highlighted');
      for (var i = 0; i < items.length; i++) {
        items[i].classList.remove('highlighted');
      }
      var dd = this.shadowRoot.querySelector('.dropdown');
      if (dd) dd.removeAttribute('aria-activedescendant');
    }
  }

  customElements.define('canvas-dropdown', CanvasDropdown);
}
