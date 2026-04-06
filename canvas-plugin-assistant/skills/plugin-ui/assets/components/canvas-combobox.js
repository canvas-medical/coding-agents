/* canvas-option: shared marker element used by dropdown, combobox, and multi-select */
if (!customElements.get('canvas-option')) {
  class CanvasOption extends HTMLElement {
    constructor() { super(); }
    connectedCallback() { this.style.display = 'none'; }
  }
  customElements.define('canvas-option', CanvasOption);
}

/* canvas-combobox: searchable single-select dropdown with type-to-filter */
if (!customElements.get('canvas-combobox')) {
  class CanvasCombobox extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'placeholder', 'value', 'disabled', 'required', 'error', 'name'];
    }

    static get formAssociated() { return true; }

    constructor() {
      super();
      this._internals = this.attachInternals();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this._options = [];
      this._highlighted = -1;
      this._selectedValue = null;
      this._selectedText = '';
      this._previousText = '';
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
        if (val !== this._selectedValue) this._selectByValue(val, true);
      }
      if (name === 'label' || name === 'placeholder' || name === 'error' || name === 'disabled') {
        if (this.shadowRoot.querySelector('.combobox')) {
          this._render();
          this._bindEvents();
        }
      }
    }

    get value() { return this._selectedValue || ''; }
    set value(v) {
      this._selectByValue(v, true);
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
        this._previousText = preselected.label;
        this._internals.setFormValue(preselected.value);
      }
    }

    _render() {
      var label = this.getAttribute('label');
      var placeholder = this.getAttribute('placeholder') || '';
      var error = this.getAttribute('error');
      var disabled = this.hasAttribute('disabled');
      var displayText = this._selectedText || '';

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
          :host { display: block; }
          .label { display: block; margin-bottom: .28571429rem; font-size: .92857143em; font-weight: 700; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif); color: var(--color-text, rgba(0, 0, 0, 0.87)); line-height: 1em; }
          :host([error]) .label { color: #9f3a38; }
          .combobox { position: relative; width: 100%; }
          .input {
            width: 100%; margin: 0; padding: .67857143em 2.1em .67857143em 1em;
            font-size: 1em; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            line-height: 1.21428571em; color: var(--color-text, rgba(0, 0, 0, 0.87));
            background: var(--color-surface, #FFFFFF);
            border: 1px solid rgba(34, 36, 38, 0.15);
            border-radius: var(--radius, .28571429rem);
            outline: none; box-sizing: border-box;
            transition: border-color 0.1s ease, box-shadow 0.1s ease, border-radius 0.1s ease;
          }
          .input:focus { border-color: #96c8da; }
          .input.open { border-color: #96c8da; border-bottom-color: transparent; border-radius: var(--radius, .28571429rem) var(--radius, .28571429rem) 0 0; z-index: 10; }
          .input.open.flip { border-color: #96c8da; border-top-color: transparent; border-radius: 0 0 var(--radius, .28571429rem) var(--radius, .28571429rem); }
          :host([disabled]) .input { opacity: 0.45; cursor: default; pointer-events: none; }
          :host([error]) .input { background: #fff6f6; border-color: #e0b4b4; }
          .arrow { position: absolute; right: 1em; top: 50%; transform: translateY(-50%); width: 8px; height: 5px; pointer-events: none; }
          .menu {
            display: none; position: absolute; top: calc(100% - 1px); left: 0; right: 0;
            max-height: 16.02857143rem; overflow-y: auto;
            background: var(--color-surface, #FFFFFF);
            border: 1px solid #96c8da; border-top: none;
            border-radius: 0 0 var(--radius, .28571429rem) var(--radius, .28571429rem);
            box-shadow: 0 0px 3px 0 rgba(34, 36, 38, 0.06);
            z-index: 11; list-style: none; margin: 0; padding: 0;
          }
          .menu.visible { display: block; }
          .menu.flip {
            bottom: 100%; top: auto;
            border-top: 1px solid #96c8da; border-bottom: none;
            border-radius: var(--radius, .28571429rem) var(--radius, .28571429rem) 0 0;
            box-shadow: 0 0px 3px 0 rgba(34, 36, 38, 0.06);
          }
          .option {
            padding: .78571429rem 1.14285714rem; font-size: 1rem; line-height: 1.0625rem;
            color: var(--color-text, rgba(0, 0, 0, 0.87)); cursor: pointer;
            border-top: 1px solid #fafafa; transition: background 0.1s ease;
          }
          .option:first-child { border-top: none; }
          .option:hover, .option.highlighted { background: rgba(0, 0, 0, 0.05); color: rgba(0, 0, 0, 0.95); }
          .option.selected { background: rgba(0, 0, 0, 0.05); color: rgba(0, 0, 0, 0.95); font-weight: 700; }
          .option[aria-disabled="true"] { color: #767676; cursor: not-allowed; }
          .option[aria-disabled="true"]:hover { background: transparent; }
          .option.hidden { display: none; }
          .empty { padding: .78571429rem 1.14285714rem; font-size: 1rem; color: rgba(0, 0, 0, 0.4); display: none; }
          .empty.visible { display: block; }
          .error-text { margin-top: .28571429rem; font-size: .92857143em; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif); color: #9f3a38; line-height: 1.4285em; }
        </style>
        ${label ? '<span class="label">' + label + '</span>' : ''}
        <div class="combobox">
          <input class="input" type="text" role="combobox"
            aria-autocomplete="list" aria-expanded="false" aria-controls="listbox"
            placeholder="${placeholder}" value="${displayText}"
            ${disabled ? 'disabled' : ''}>
          <svg class="arrow" viewBox="0 0 10 6" fill="#575757"><path d="M1 0h8a1 1 0 01.7 1.7l-4 4a1 1 0 01-1.4 0l-4-4A1 1 0 011 0z"/></svg>
          <ul class="menu" id="listbox" role="listbox">
            ${optionsHtml}
            <li class="empty">No results</li>
          </ul>
        </div>
        ${error ? '<span class="error-text">' + error + '</span>' : ''}
      `;
    }

    _bindEvents() {
      var self = this;
      var input = this.shadowRoot.querySelector('.input');
      var menu = this.shadowRoot.querySelector('.menu');

      input.addEventListener('click', function() {
        if (self.hasAttribute('disabled')) return;
        if (!self._open) self._openMenu();
      });

      input.addEventListener('input', function() {
        if (!self._open) self._openMenu();
        self._filter(input.value);
      });

      input.addEventListener('keydown', function(e) {
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
            e.preventDefault();
            if (!self._open) {
              self._openMenu();
            } else if (self._highlighted >= 0) {
              var visible = self._getVisibleOptions();
              if (visible[self._highlighted]) {
                self._selectByValue(visible[self._highlighted].dataset.value, false);
                self._close();
              }
            }
            break;
          case 'Escape':
            e.preventDefault();
            self._restore();
            self._close();
            break;
          case 'Home':
            if (self._open) { e.preventDefault(); self._highlightIndex(0); }
            break;
          case 'End':
            if (self._open) {
              e.preventDefault();
              var visible = self._getVisibleOptions();
              self._highlightIndex(visible.length - 1);
            }
            break;
          case 'Tab':
            if (self._open) {
              if (self._highlighted >= 0) {
                var visible = self._getVisibleOptions();
                if (visible[self._highlighted]) self._selectByValue(visible[self._highlighted].dataset.value, false);
              } else {
                self._restore();
              }
              self._close();
            }
            break;
        }
      });

      menu.addEventListener('click', function(e) {
        var opt = e.target.closest('.option');
        if (!opt) return;
        if (opt.getAttribute('aria-disabled') === 'true') return;
        self._selectByValue(opt.dataset.value, false);
        self._close();
        input.focus();
      });
    }

    _openMenu() {
      this._open = true;
      this._highlighted = -1;
      this._previousText = this._selectedText;
      var input = this.shadowRoot.querySelector('.input');
      var menu = this.shadowRoot.querySelector('.menu');
      input.classList.add('open');
      input.setAttribute('aria-expanded', 'true');
      menu.classList.add('visible');
      this._showAll();
      this._checkFlip();
    }

    _close() {
      this._open = false;
      this._highlighted = -1;
      var input = this.shadowRoot.querySelector('.input');
      var menu = this.shadowRoot.querySelector('.menu');
      input.classList.remove('open', 'flip');
      input.setAttribute('aria-expanded', 'false');
      menu.classList.remove('visible', 'flip');
      this._clearHighlight();
      this._showAll();
    }

    _restore() {
      var input = this.shadowRoot.querySelector('.input');
      input.value = this._previousText;
    }

    _onDocClick(e) {
      if (!this.contains(e.target) && !this.shadowRoot.contains(e.target)) {
        if (this._open) {
          this._restore();
          this._close();
        }
      }
    }

    _filter(query) {
      var q = query.toLowerCase();
      var items = this.shadowRoot.querySelectorAll('.option');
      var anyVisible = false;
      for (var i = 0; i < items.length; i++) {
        var label = this._options[items[i].dataset.index].label.toLowerCase();
        if (label.indexOf(q) >= 0) {
          items[i].classList.remove('hidden');
          anyVisible = true;
        } else {
          items[i].classList.add('hidden');
        }
      }
      var empty = this.shadowRoot.querySelector('.empty');
      if (anyVisible) {
        empty.classList.remove('visible');
      } else {
        empty.classList.add('visible');
      }
      this._highlighted = -1;
      this._clearHighlight();
    }

    _showAll() {
      var items = this.shadowRoot.querySelectorAll('.option');
      for (var i = 0; i < items.length; i++) items[i].classList.remove('hidden');
      var empty = this.shadowRoot.querySelector('.empty');
      empty.classList.remove('visible');
    }

    _checkFlip() {
      var menu = this.shadowRoot.querySelector('.menu');
      var input = this.shadowRoot.querySelector('.input');
      var rect = menu.getBoundingClientRect();
      if (rect.bottom > window.innerHeight) {
        menu.classList.add('flip');
        input.classList.add('flip');
      }
    }

    _selectByValue(val, silent) {
      var opt = this._options.find(function(o) { return o.value === val; });
      if (!opt || opt.disabled) return;
      this._selectedValue = opt.value;
      this._selectedText = opt.label;
      this._previousText = opt.label;
      this._internals.setFormValue(opt.value);

      var input = this.shadowRoot.querySelector('.input');
      if (input) input.value = opt.label;

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

      if (!silent) {
        this.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true }));
      }
    }

    _getVisibleOptions() {
      return this.shadowRoot.querySelectorAll('.option:not(.hidden):not([aria-disabled="true"])');
    }

    _highlightNext(dir) {
      var opts = this._getVisibleOptions();
      if (opts.length === 0) return;
      this._highlighted += dir;
      if (this._highlighted < 0) this._highlighted = opts.length - 1;
      if (this._highlighted >= opts.length) this._highlighted = 0;
      this._applyHighlight(opts);
    }

    _highlightIndex(index) {
      var opts = this._getVisibleOptions();
      if (index < 0 || index >= opts.length) return;
      this._highlighted = index;
      this._applyHighlight(opts);
    }

    _applyHighlight(opts) {
      this._clearHighlight();
      if (this._highlighted >= 0 && opts[this._highlighted]) {
        opts[this._highlighted].classList.add('highlighted');
        opts[this._highlighted].scrollIntoView({ block: 'nearest' });
      }
    }

    _clearHighlight() {
      var items = this.shadowRoot.querySelectorAll('.option.highlighted');
      for (var i = 0; i < items.length; i++) items[i].classList.remove('highlighted');
    }
  }

  customElements.define('canvas-combobox', CanvasCombobox);
}
