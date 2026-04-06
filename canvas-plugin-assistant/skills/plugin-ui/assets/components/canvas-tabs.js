/* canvas-tab-panel: simple content container, visibility managed by canvas-tabs */
if (!customElements.get('canvas-tab-panel')) {
  class CanvasTabPanel extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = '<style>:host{display:block}:host([hidden]){display:none}.panel-inner{overflow:auto;max-width:100%}</style><div class="panel-inner"><slot></slot></div>';
    }
    connectedCallback() {
      this.setAttribute('role', 'tabpanel');
      if (!this.hasAttribute('hidden')) this.setAttribute('hidden', '');
    }
  }
  customElements.define('canvas-tab-panel', CanvasTabPanel);
}

/* canvas-tab-label: text label inside a canvas-tab. Truncates with ellipsis and sets title automatically. */
if (!customElements.get('canvas-tab-label')) {
  class CanvasTabLabel extends HTMLElement {
    constructor() { super(); }
    connectedCallback() { this.style.display = 'none'; }
  }
  customElements.define('canvas-tab-label', CanvasTabLabel);
}

/* canvas-tab: a single tab button inside canvas-tabs. Rich content via slot. */
if (!customElements.get('canvas-tab')) {
  class CanvasTab extends HTMLElement {
    constructor() { super(); }
    connectedCallback() {
      this.style.display = 'none';
      if (!this.querySelector('canvas-tab-label')) {
        console.warn('canvas-tab: missing <canvas-tab-label>. Wrap your tab text in <canvas-tab-label> for truncation and tooltip support.');
      }
    }
  }
  customElements.define('canvas-tab', CanvasTab);
}

/* canvas-tabs: tab bar container that manages active state, keyboard nav, and panel visibility */
if (!customElements.get('canvas-tabs')) {
  class CanvasTabs extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this._tabs = [];
      this._buttons = [];
      this._focusIndex = 0;
    }

    connectedCallback() {
      var self = this;
      setTimeout(function() {
        self._readTabs();
        self._render();
        self._computeMinWidths();
        self._bindEvents();
        self._activateInitial();
      }, 0);
    }

    _readTabs() {
      this._tabs = [];
      var tabs = this.querySelectorAll(':scope > canvas-tab');
      for (var i = 0; i < tabs.length; i++) {
        var tab = tabs[i];
        var labelEl = tab.querySelector('canvas-tab-label');
        var hasLabel = !!labelEl;
        var labelText = hasLabel ? labelEl.textContent.trim() : tab.textContent.trim();

        /* Collect trailing content (everything after canvas-tab-label) */
        var trailingHtml = '';
        if (hasLabel) {
          var sibling = labelEl.nextElementSibling;
          while (sibling) {
            trailingHtml += sibling.outerHTML;
            sibling = sibling.nextElementSibling;
          }
        }

        this._tabs.push({
          panelId: tab.getAttribute('for'),
          badge: tab.getAttribute('badge'),
          active: tab.hasAttribute('active'),
          hasLabel: hasLabel,
          labelText: labelText,
          trailingHtml: trailingHtml,
          html: tab.innerHTML,
          text: labelText
        });
      }
    }

    _render() {
      var buttonsHtml = '';
      for (var i = 0; i < this._tabs.length; i++) {
        var t = this._tabs[i];
        var badgeHtml = '';
        if (t.badge) {
          badgeHtml = '<span class="tab-badge">' + t.badge + '</span>';
        }
        var titleAttr = t.hasLabel ? ' title="' + t.labelText.replace(/"/g, '&quot;') + '"' : '';

        if (t.hasLabel) {
          buttonsHtml += '<button class="tab-button" role="tab" aria-selected="false" tabindex="-1" data-index="' + i + '" data-panel="' + (t.panelId || '') + '">'
            + '<span class="tab-label-text"' + titleAttr + '>' + t.labelText + '</span>'
            + t.trailingHtml + badgeHtml
            + '</button>';
        } else {
          buttonsHtml += '<button class="tab-button" role="tab" aria-selected="false" tabindex="-1" data-index="' + i + '" data-panel="' + (t.panelId || '') + '">'
            + t.html + badgeHtml
            + '</button>';
        }
      }

      this.shadowRoot.innerHTML = `
        <style>
          :host { display: block; }
          .tab-wrapper {
            position: relative;
            margin-bottom: 1em;
          }
          .tab-wrapper::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: rgba(34, 36, 38, 0.15);
          }
          .tab-bar {
            -webkit-mask-image: linear-gradient(to right, black, black);
            mask-image: linear-gradient(to right, black, black);
            transition: -webkit-mask-image 0.15s ease, mask-image 0.15s ease;
            display: flex;
            align-items: stretch;
            height: var(--tab-bar-height, 45.41px);
            width: 100%;
            background: transparent;
            padding: 0;
            overflow-x: auto;
            overflow-y: visible;
            scrollbar-width: none;
          }
          .tab-bar::-webkit-scrollbar { display: none; }
          .tab-bar.fade-right {
            -webkit-mask-image: linear-gradient(to right, black calc(100% - 50px), transparent);
            mask-image: linear-gradient(to right, black calc(100% - 50px), transparent);
          }
          .tab-bar.fade-left {
            -webkit-mask-image: linear-gradient(to right, transparent, black 50px);
            mask-image: linear-gradient(to right, transparent, black 50px);
          }
          .tab-bar.fade-both {
            -webkit-mask-image: linear-gradient(to right, transparent, black 50px, black calc(100% - 50px), transparent);
            mask-image: linear-gradient(to right, transparent, black 50px, black calc(100% - 50px), transparent);
          }
          .tab-button {
            display: inline-flex;
            align-items: center;
            gap: .50em;
            padding: 0 1.14285714em;
            flex: 0 1 auto;
            font-size: 1em;
            font-weight: 400;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            line-height: 1em;
            color: rgba(0, 0, 0, 0.87);
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            position: relative;
            z-index: 1;
            cursor: pointer;
            transition: border-color 0.1s ease;
            white-space: nowrap;
          }
          .tab-button:focus-visible {
            outline: 2px solid #2185d0;
            outline-offset: -2px;
          }
          .tab-button:hover { color: rgba(0, 0, 0, 0.95); }
          .tab-button[aria-selected="true"] {
            border-bottom-color: rgb(27, 28, 29);
            color: rgba(0, 0, 0, 0.95);
            font-weight: 700;
          }
          .tab-label-text {
            display: block;
            flex: 0 1 var(--tab-label-max-width, 160px);
            min-width: var(--tab-label-min-width, 60px);
            max-width: var(--tab-label-max-width, 160px);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          .tab-badge {
            display: inline-flex;
            align-items: center;
            padding: .21428571em .5625em;
            font-size: .71428571em;
            font-weight: 700;
            color: #767676;
            background: #fff;
            border: 1px solid #767676;
            border-radius: .28571429rem;
            line-height: 1;
            margin: 0;
            gap: 0;
            flex-shrink: 0;
          }
        </style>
        <div class="tab-wrapper">
          <div class="tab-bar" role="tablist">${buttonsHtml}</div>
        </div>
        <slot></slot>
      `;
    }

    _computeMinWidths() {
      var buttons = this.shadowRoot.querySelectorAll('.tab-button');
      var labels = this.shadowRoot.querySelectorAll('.tab-label-text');
      var minWidth = getComputedStyle(this.shadowRoot.host).getPropertyValue('--tab-label-min-width').trim() || '60px';

      /* Force labels to their minimum, measure each button, set as floor */
      for (var i = 0; i < labels.length; i++) {
        labels[i].style.width = minWidth;
        labels[i].style.flexBasis = minWidth;
      }

      for (var i = 0; i < buttons.length; i++) {
        var floor = buttons[i].scrollWidth;
        buttons[i].style.minWidth = floor + 'px';
      }

      /* Reset labels to their natural flex behavior */
      for (var i = 0; i < labels.length; i++) {
        labels[i].style.width = '';
        labels[i].style.flexBasis = '';
      }
    }

    _updateFades() {
      var bar = this.shadowRoot.querySelector('.tab-bar');
      if (!bar) return;
      var scrollLeft = bar.scrollLeft;
      var maxScroll = bar.scrollWidth - bar.clientWidth;
      var hasLeft = scrollLeft > 2;
      var hasRight = maxScroll - scrollLeft > 2;

      bar.classList.remove('fade-left', 'fade-right', 'fade-both');
      if (hasLeft && hasRight) bar.classList.add('fade-both');
      else if (hasLeft) bar.classList.add('fade-left');
      else if (hasRight) bar.classList.add('fade-right');
    }

    _bindEvents() {
      var self = this;
      this._buttons = Array.from(this.shadowRoot.querySelectorAll('.tab-button'));

      var bar = this.shadowRoot.querySelector('.tab-bar');
      bar.addEventListener('scroll', function() { self._updateFades(); });
      self._updateFades();

      bar.addEventListener('click', function(e) {
        var btn = e.target.closest('.tab-button');
        if (!btn) return;
        var index = parseInt(btn.dataset.index, 10);
        self._activate(index);
      });

      this.shadowRoot.querySelector('.tab-bar').addEventListener('keydown', function(e) {
        var btn = e.target.closest('.tab-button');
        if (!btn) return;
        var index = parseInt(btn.dataset.index, 10);
        var last = self._buttons.length - 1;

        switch (e.key) {
          case 'ArrowRight':
            e.preventDefault();
            self._focusTab(index < last ? index + 1 : 0);
            break;
          case 'ArrowLeft':
            e.preventDefault();
            self._focusTab(index > 0 ? index - 1 : last);
            break;
          case 'Home':
            e.preventDefault();
            self._focusTab(0);
            break;
          case 'End':
            e.preventDefault();
            self._focusTab(last);
            break;
        }
      });
    }

    _activateInitial() {
      var initial = 0;
      for (var i = 0; i < this._tabs.length; i++) {
        if (this._tabs[i].active) { initial = i; break; }
      }
      this._activate(initial);
    }

    _activate(index) {
      /* Deactivate all */
      for (var i = 0; i < this._buttons.length; i++) {
        this._buttons[i].setAttribute('aria-selected', 'false');
        this._buttons[i].setAttribute('tabindex', '-1');
      }
      /* Hide all panels */
      var panels = this.querySelectorAll(':scope > canvas-tab-panel');
      for (var i = 0; i < panels.length; i++) {
        panels[i].setAttribute('hidden', '');
        panels[i].removeAttribute('visible');
      }

      /* Activate selected */
      var btn = this._buttons[index];
      if (!btn) return;
      btn.setAttribute('aria-selected', 'true');
      btn.setAttribute('tabindex', '0');

      var panelId = btn.dataset.panel;
      if (panelId) {
        var panel = this.querySelector(':scope > canvas-tab-panel[id="' + panelId + '"]');
        if (panel) {
          panel.removeAttribute('hidden');
          panel.setAttribute('visible', '');
          btn.setAttribute('aria-controls', panelId);
          panel.setAttribute('aria-labelledby', 'tab-' + index);
        }
      }

      btn.id = 'tab-' + index;
      this._focusIndex = index;

      this.dispatchEvent(new CustomEvent('tab-change', {
        bubbles: true,
        composed: true,
        detail: { index: index, panel: panelId }
      }));
    }

    _focusTab(index) {
      if (this._buttons[index]) {
        this._buttons[index].focus();
        this._focusIndex = index;
      }
    }
  }

  customElements.define('canvas-tabs', CanvasTabs);
}
