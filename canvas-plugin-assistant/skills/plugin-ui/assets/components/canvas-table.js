if (!customElements.get('canvas-table')) {
  class CanvasTable extends HTMLElement {
    static get observedAttributes() {
      return ['compact', 'celled', 'selectable', 'sticky', 'striped'];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: table;
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif);
            color: var(--color-text, rgba(0, 0, 0, 0.87));
            font-size: 1em;
          }

          ::slotted(canvas-table-head) {
            display: table-header-group;
          }

          ::slotted(canvas-table-body) {
            display: table-row-group;
          }
        </style>
        <slot></slot>
      `;
    }

    connectedCallback() {
      this._applyVariants();
    }

    attributeChangedCallback() {
      this._applyVariants();
    }

    _applyVariants() {
      if (this.hasAttribute('compact')) {
        this.style.setProperty('--canvas-table-cell-padding', '0.35rem 0.7rem');
        this.style.setProperty('--canvas-table-header-padding', '0.5rem 0.7rem');
      } else {
        this.style.removeProperty('--canvas-table-cell-padding');
        this.style.removeProperty('--canvas-table-header-padding');
      }
    }
  }

  class CanvasTableHead extends HTMLElement {
    connectedCallback() {
      this.style.display = 'table-header-group';
    }
  }

  class CanvasTableBody extends HTMLElement {
    connectedCallback() {
      this.style.display = 'table-row-group';
    }
  }

  class CanvasTableRow extends HTMLElement {
    static get observedAttributes() {
      return ['positive', 'warning', 'negative', 'active'];
    }

    connectedCallback() {
      this.style.display = 'table-row';

      const inHead = this.parentElement && this.parentElement.tagName === 'CANVAS-TABLE-HEAD';

      if (inHead) {
        this.style.borderBottom = 'none';
      } else {
        this.style.borderBottom = '1px solid var(--canvas-table-border, rgba(34, 36, 38, 0.1))';
      }

      this._applyState();

      if (!inHead) {
        const table = this._getTable();

        if (table && table.hasAttribute('striped')) {
          const siblings = Array.from(this.parentElement.children).filter(
            (el) => el.tagName === 'CANVAS-TABLE-ROW'
          );
          const index = siblings.indexOf(this);
          if (index % 2 === 1) {
            this._stripeBackground = 'var(--canvas-table-stripe-bg, rgba(0, 0, 50, 0.02))';
          }
          this._applyState();
        }

        if (table && table.hasAttribute('selectable')) {
          this.style.cursor = 'pointer';
          this._onMouseEnter = () => {
            if (!this.hasAttribute('positive') && !this.hasAttribute('warning') &&
                !this.hasAttribute('negative') && !this.hasAttribute('active')) {
              this.style.background = 'rgba(0, 0, 50, 0.025)';
            }
          };
          this._onMouseLeave = () => {
            this._applyState();
          };
          this.addEventListener('mouseenter', this._onMouseEnter);
          this.addEventListener('mouseleave', this._onMouseLeave);
        }
      }
    }

    disconnectedCallback() {
      if (this._onMouseEnter) {
        this.removeEventListener('mouseenter', this._onMouseEnter);
      }
      if (this._onMouseLeave) {
        this.removeEventListener('mouseleave', this._onMouseLeave);
      }
    }

    attributeChangedCallback() {
      this._applyState();
    }

    _applyState() {
      if (this.hasAttribute('positive')) {
        this.style.background = 'var(--canvas-table-row-positive-bg, #fcfff5)';
        this.style.color = 'var(--canvas-table-row-positive-text, #2c662d)';
      } else if (this.hasAttribute('warning')) {
        this.style.background = 'var(--canvas-table-row-warning-bg, #fffaf3)';
        this.style.color = 'var(--canvas-table-row-warning-text, #573a08)';
      } else if (this.hasAttribute('negative')) {
        this.style.background = 'var(--canvas-table-row-negative-bg, #fff6f6)';
        this.style.color = 'var(--canvas-table-row-negative-text, #9f3a38)';
      } else if (this.hasAttribute('active')) {
        this.style.background = 'var(--canvas-table-row-active-bg, #e0e0e0)';
        this.style.color = '';
      } else if (this._stripeBackground) {
        this.style.background = this._stripeBackground;
        this.style.color = '';
      } else {
        this.style.background = '';
        this.style.color = '';
      }
    }

    _getTable() {
      let el = this.parentElement;
      while (el) {
        if (el.tagName === 'CANVAS-TABLE') {
          return el;
        }
        el = el.parentElement;
      }
      return null;
    }
  }

  class CanvasTableCell extends HTMLElement {
    static get observedAttributes() {
      return ['actions', 'bold', 'colspan', 'width'];
    }

    connectedCallback() {
      this.style.display = 'table-cell';
      this.style.verticalAlign = 'middle';
      this.style.textAlign = 'left';

      const inHead = this._isInHead();
      const table = this._getTable();

      if (inHead) {
        this.style.fontWeight = '700';
        this.style.padding = 'var(--canvas-table-header-padding, 0.5rem 1rem)';
        this.style.background = 'var(--canvas-table-header-bg, #FFFFFF)';
        this.style.borderBottom = '2px solid var(--canvas-table-border, rgba(34, 36, 38, 0.1))';

        if (table && table.hasAttribute('sticky')) {
          this.style.position = 'sticky';
          this.style.top = '0';
          this.style.zIndex = '2';
        }
      } else {
        this.style.padding = 'var(--canvas-table-cell-padding, 0.5rem 1rem)';
      }

      if (table && table.hasAttribute('celled')) {
        this.style.border = '1px solid var(--canvas-table-border, rgba(34, 36, 38, 0.1))';
      }

      if (this.hasAttribute('bold')) {
        this.style.fontWeight = '700';
      }

      if (this.hasAttribute('actions')) {
        this.style.whiteSpace = 'nowrap';
        this.style.textAlign = 'right';
        this.style.width = '1%';
      }

      if (this.hasAttribute('width')) {
        this.style.width = this.getAttribute('width');
      }

      if (this.hasAttribute('colspan')) {
        this.style.display = 'block';
        this.style.width = '100%';
        const row = this.parentElement;
        if (row) {
          Array.from(row.children).forEach((sibling) => {
            if (sibling !== this && sibling.tagName === 'CANVAS-TABLE-CELL') {
              sibling.style.display = 'none';
            }
          });
        }
      }
    }

    _isInHead() {
      const row = this.parentElement;
      if (!row) return false;
      const group = row.parentElement;
      if (!group) return false;
      return group.tagName === 'CANVAS-TABLE-HEAD';
    }

    _getTable() {
      let el = this.parentElement;
      while (el) {
        if (el.tagName === 'CANVAS-TABLE') {
          return el;
        }
        el = el.parentElement;
      }
      return null;
    }
  }

  customElements.define('canvas-table', CanvasTable);
  customElements.define('canvas-table-head', CanvasTableHead);
  customElements.define('canvas-table-body', CanvasTableBody);
  customElements.define('canvas-table-row', CanvasTableRow);
  customElements.define('canvas-table-cell', CanvasTableCell);
}
