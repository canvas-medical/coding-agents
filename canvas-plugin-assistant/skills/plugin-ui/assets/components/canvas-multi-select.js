/* canvas-option: shared marker element used by dropdown, combobox, and multi-select */
if (!customElements.get('canvas-option')) {
  class CanvasOption extends HTMLElement {
    constructor() { super(); }
    connectedCallback() { this.style.display = 'none'; }
  }
  customElements.define('canvas-option', CanvasOption);
}

/* canvas-multi-select: multi-value select with chips, type-to-filter, and form association */
if (!customElements.get('canvas-multi-select')) {
  class CanvasMultiSelect extends HTMLElement {
    static get observedAttributes() {
      return ['label', 'placeholder', 'disabled', 'required', 'error', 'name'];
    }

    static get formAssociated() { return true; }

    constructor() {
      super();
      this._internals = this.attachInternals();
      this.attachShadow({ mode: 'open', delegatesFocus: true });
      this._options = [];
      this._selected = [];
      this._highlighted = -1;
      this._open = false;
      this._onDocClick = this._onDocClick.bind(this);
    }

    connectedCallback() {
      var self = this;
      setTimeout(function() {
        self._readOptions();
        self._render();
        self._bindEvents();
        self._updateFormValue();
      }, 0);
      document.addEventListener('click', this._onDocClick);
    }

    disconnectedCallback() {
      document.removeEventListener('click', this._onDocClick);
    }

    attributeChangedCallback(name) {
      if (name === 'label' || name === 'placeholder' || name === 'error' || name === 'disabled') {
        if (this.shadowRoot.querySelector('.multi-select')) {
          this._render();
          this._bindEvents();
        }
      }
    }

    get value() { return this._selected.slice(); }
    set value(arr) {
      this._selected = Array.isArray(arr) ? arr.slice() : [];
      if (this.shadowRoot.querySelector('.multi-select')) {
        this._renderChips();
        this._syncOptionVisibility();
        this._updateFormValue();
      }
    }

    get name() { return this.getAttribute('name'); }

    _readOptions() {
      this._options = [];
      var opts = this.querySelectorAll('canvas-option');
      for (var i = 0; i < opts.length; i++) {
        var opt = opts[i];
        var val = opt.getAttribute('value') || opt.textContent.trim();
        this._options.push({
          value: val,
          label: opt.getAttribute('label') || opt.textContent.trim(),
          html: opt.innerHTML,
          disabled: opt.hasAttribute('disabled')
        });
        if (opt.hasAttribute('selected') && this._selected.indexOf(val) === -1) {
          this._selected.push(val);
        }
      }
    }

    _render() {
      var label = this.getAttribute('label');
      var placeholder = this.getAttribute('placeholder') || '';
      var error = this.getAttribute('error');
      var disabled = this.hasAttribute('disabled');

      var optionsHtml = '';
      for (var i = 0; i < this._options.length; i++) {
        var o = this._options[i];
        var sel = this._selected.indexOf(o.value) >= 0;
        var attrs = 'role="option" data-value="' + o.value + '" data-index="' + i + '"';
        if (o.disabled) attrs += ' aria-disabled="true"';
        optionsHtml += '<li class="option' + (sel ? ' selected' : '') + '" ' + attrs + '>' + o.html + '</li>';
      }

      this.shadowRoot.innerHTML = `
        <style>
          :host { display: block; }
          .label { display: block; margin-bottom: .28571429rem; font-size: .92857143em; font-weight: 700; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif); color: var(--color-text, rgba(0, 0, 0, 0.87)); line-height: 1em; }
          :host([error]) .label { color: #9f3a38; }
          .multi-select { position: relative; width: 100%; }
          .trigger {
            display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
            min-height: calc(1.21428571em + 2 * .67857143em + 2px);
            padding: .4em .4em; padding-right: 2.1em;
            background: var(--color-surface, #FFFFFF);
            border: 1px solid rgba(34, 36, 38, 0.15);
            border-radius: var(--radius, .28571429rem);
            cursor: text; box-sizing: border-box;
            transition: border-color 0.1s ease, box-shadow 0.1s ease, border-radius 0.1s ease;
          }
          .trigger:focus-within { border-color: #96c8da; }
          .trigger.open { border-color: #96c8da; border-bottom-color: transparent; border-radius: var(--radius, .28571429rem) var(--radius, .28571429rem) 0 0; }
          .trigger.open.flip { border-bottom-color: #96c8da; border-top-color: transparent; border-radius: 0 0 var(--radius, .28571429rem) var(--radius, .28571429rem); }
          :host([disabled]) .trigger { opacity: 0.45; cursor: default; pointer-events: none; }
          :host([error]) .trigger { background: #fff6f6; border-color: #e0b4b4; }
          .input {
            flex: 1; min-width: 80px; padding: .25em .33em;
            font-size: 1em; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            line-height: 1.21428571em; color: var(--color-text, rgba(0, 0, 0, 0.87));
            background: transparent; border: none; outline: none; margin: 0;
          }
          .input::placeholder { color: rgba(191, 191, 191, 0.87); }
          .arrow { position: absolute; right: 1em; top: calc((1.21428571em + 2 * .67857143em + 2px) / 2); transform: translateY(-50%); width: 8px; height: 5px; pointer-events: none; }
          .chip {
            display: inline-flex; align-items: center; gap: .4em;
            padding: .5833em .708em .5833em .833em;
            font-size: .85714286rem; font-weight: 700; line-height: 1;
            color: rgba(0, 0, 0, 0.6); background: #e8e8e8;
            border: 0 solid transparent; border-radius: var(--radius, .28571429rem);
            white-space: nowrap; cursor: default; user-select: none;
            transition: background 0.1s ease;
          }
          .chip:hover { background: #e0e0e0; }
          .chip-dismiss {
            display: inline-flex; align-items: center; justify-content: center;
            width: 1em; height: 1em; flex-shrink: 0;
            padding: 0; margin: 0; background: transparent; border: none;
            cursor: pointer; color: inherit; opacity: .7;
            line-height: 1; transition: opacity 0.1s ease;
          }
          .chip-dismiss:hover { opacity: 1; }
          .chip-dismiss svg { display: block; }
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
            bottom: calc(100% - 1px); top: auto;
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
          .option.selected { display: none; }
          .option.hidden { display: none; }
          .option[aria-disabled="true"] { color: #767676; cursor: not-allowed; }
          .option[aria-disabled="true"]:hover { background: transparent; }
          .empty { padding: .78571429rem 1.14285714rem; font-size: 1rem; color: rgba(0, 0, 0, 0.4); display: none; }
          .empty.visible { display: block; }
          .error-text { margin-top: .28571429rem; font-size: .92857143em; font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif); color: #9f3a38; line-height: 1.4285em; }
        </style>
        ${label ? '<span class="label">' + label + '</span>' : ''}
        <div class="multi-select">
          <div class="trigger">
            <input class="input" type="text" placeholder="${placeholder}" ${disabled ? 'disabled' : ''}>
          </div>
          <svg class="arrow" viewBox="0 0 10 6" fill="#575757"><path d="M1 0h8a1 1 0 01.7 1.7l-4 4a1 1 0 01-1.4 0l-4-4A1 1 0 011 0z"/></svg>
          <ul class="menu" role="listbox" aria-multiselectable="true">
            ${optionsHtml}
            <li class="empty">No results</li>
          </ul>
        </div>
        ${error ? '<span class="error-text">' + error + '</span>' : ''}
      `;
      this._renderChips();
    }

    _renderChips() {
      var trigger = this.shadowRoot.querySelector('.trigger');
      var input = this.shadowRoot.querySelector('.input');
      var existing = trigger.querySelectorAll('.chip');
      for (var i = existing.length - 1; i >= 0; i--) existing[i].remove();

      for (var i = 0; i < this._selected.length; i++) {
        var opt = this._options.find(function(o) { return o.value === this._selected[i]; }.bind(this));
        if (!opt) continue;
        var chip = document.createElement('span');
        chip.className = 'chip';
        chip.dataset.value = opt.value;
        chip.innerHTML = opt.label + '<button class="chip-dismiss" aria-label="Remove ' + opt.label + '"><svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1.5 1.5l7 7M8.5 1.5l-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>';
        trigger.insertBefore(chip, input);
      }
      this._bindChipEvents();
    }

    _syncOptionVisibility() {
      var items = this.shadowRoot.querySelectorAll('.option');
      for (var i = 0; i < items.length; i++) {
        var val = items[i].dataset.value;
        if (this._selected.indexOf(val) >= 0) {
          items[i].classList.add('selected');
        } else {
          items[i].classList.remove('selected');
        }
      }
      this._checkEmpty();
    }

    _checkEmpty() {
      var visible = this.shadowRoot.querySelectorAll('.option:not(.selected):not(.hidden)');
      var empty = this.shadowRoot.querySelector('.empty');
      if (visible.length === 0) empty.classList.add('visible');
      else empty.classList.remove('visible');
    }

    _updateFormValue() {
      var fd = new FormData();
      var name = this.getAttribute('name');
      if (name) {
        for (var i = 0; i < this._selected.length; i++) {
          fd.append(name, this._selected[i]);
        }
      }
      this._internals.setFormValue(fd);
    }

    _bindEvents() {
      var self = this;
      var trigger = this.shadowRoot.querySelector('.trigger');
      var input = this.shadowRoot.querySelector('.input');
      var menu = this.shadowRoot.querySelector('.menu');

      trigger.addEventListener('click', function(e) {
        if (self.hasAttribute('disabled')) return;
        var dismiss = e.target.closest('.chip-dismiss');
        if (dismiss) {
          var chip = dismiss.closest('.chip');
          if (chip) self._deselect(chip.dataset.value);
          return;
        }
        var chip = e.target.closest('.chip');
        if (chip) return;
        if (!self._open) self._openMenu();
        input.focus();
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
                self._selectValue(visible[self._highlighted].dataset.value);
                input.value = '';
                self._clearFilter();
                self._highlighted = -1;
              }
            }
            break;
          case 'Escape':
            e.preventDefault();
            input.value = '';
            self._clearFilter();
            self._close();
            break;
          case 'Backspace':
            if (input.value === '' && self._selected.length > 0) {
              self._deselect(self._selected[self._selected.length - 1]);
            }
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
              input.value = '';
              self._clearFilter();
              self._close();
            }
            break;
        }
      });

      menu.addEventListener('click', function(e) {
        var opt = e.target.closest('.option');
        if (!opt) return;
        if (opt.getAttribute('aria-disabled') === 'true') return;
        self._selectValue(opt.dataset.value);
        input.value = '';
        self._clearFilter();
        input.focus();
      });
    }

    _selectValue(val) {
      if (this._selected.indexOf(val) >= 0) return;
      this._selected.push(val);
      this._renderChips();
      this._syncOptionVisibility();
      this._updateFormValue();
      this.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true }));
    }

    _deselect(val) {
      var idx = this._selected.indexOf(val);
      if (idx < 0) return;
      this._selected.splice(idx, 1);
      this._renderChips();
      this._syncOptionVisibility();
      this._updateFormValue();
      this.dispatchEvent(new CustomEvent('change', { bubbles: true, composed: true }));
    }

    _bindChipEvents() {
      var self = this;
      var chips = this.shadowRoot.querySelectorAll('.chip-dismiss');
      for (var i = 0; i < chips.length; i++) {
        chips[i].onclick = function(e) {
          e.stopPropagation();
          var chip = this.closest('.chip');
          if (chip) self._deselect(chip.dataset.value);
        };
      }
    }

    _openMenu() {
      this._open = true;
      this._highlighted = -1;
      var trigger = this.shadowRoot.querySelector('.trigger');
      var menu = this.shadowRoot.querySelector('.menu');
      trigger.classList.add('open');
      menu.classList.add('visible');
      this._checkEmpty();
      this._checkFlip();
    }

    _close() {
      this._open = false;
      this._highlighted = -1;
      var trigger = this.shadowRoot.querySelector('.trigger');
      var menu = this.shadowRoot.querySelector('.menu');
      trigger.classList.remove('open', 'flip');
      menu.classList.remove('visible', 'flip');
      this._clearHighlight();
    }

    _onDocClick(e) {
      if (!this.contains(e.target) && !this.shadowRoot.contains(e.target)) {
        if (this._open) {
          this.shadowRoot.querySelector('.input').value = '';
          this._clearFilter();
          this._close();
        }
      }
    }

    _filter(query) {
      var q = query.toLowerCase();
      var items = this.shadowRoot.querySelectorAll('.option');
      for (var i = 0; i < items.length; i++) {
        var label = this._options[items[i].dataset.index].label.toLowerCase();
        if (label.indexOf(q) >= 0) {
          items[i].classList.remove('hidden');
        } else {
          items[i].classList.add('hidden');
        }
      }
      this._checkEmpty();
      this._highlighted = -1;
      this._clearHighlight();
    }

    _clearFilter() {
      var items = this.shadowRoot.querySelectorAll('.option');
      for (var i = 0; i < items.length; i++) items[i].classList.remove('hidden');
      this._checkEmpty();
    }

    _checkFlip() {
      var menu = this.shadowRoot.querySelector('.menu');
      var trigger = this.shadowRoot.querySelector('.trigger');
      var rect = menu.getBoundingClientRect();
      if (rect.bottom > window.innerHeight) {
        menu.classList.add('flip');
        trigger.classList.add('flip');
      }
    }

    _getVisibleOptions() {
      return this.shadowRoot.querySelectorAll('.option:not(.selected):not(.hidden):not([aria-disabled="true"])');
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

  customElements.define('canvas-multi-select', CanvasMultiSelect);
}
