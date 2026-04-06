if (!customElements.get('canvas-badge')) {
  class CanvasBadge extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-block;
            vertical-align: baseline;
          }

          span {
            display: inline-block;
            line-height: 1;
            margin: 0 .14285714em;
            padding: var(--canvas-badge-padding, .5833em .833em);
            font-weight: var(--canvas-badge-font-weight, var(--font-weight-bold, 700));
            font-family: var(--canvas-badge-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            font-size: var(--canvas-badge-font-size, .85714286rem);
            border: var(--canvas-badge-border, 0 solid transparent);
            border-radius: var(--canvas-badge-radius, var(--radius, .28571429rem));
            background: var(--canvas-badge-bg, #e8e8e8);
            color: var(--canvas-badge-color, rgba(0, 0, 0, 0.6));
            white-space: nowrap;
            transition: background 0.1s ease;
          }

          /* Solid colors */
          :host([color="red"]) span { background: var(--canvas-badge-red-bg, var(--palette-red, #db2828)); color: var(--canvas-badge-red-color, #fff); }
          :host([color="orange"]) span { background: var(--canvas-badge-orange-bg, var(--palette-orange, #f2711c)); color: var(--canvas-badge-orange-color, #fff); }
          :host([color="yellow"]) span { background: var(--canvas-badge-yellow-bg, var(--palette-yellow, #fbbd08)); color: var(--canvas-badge-yellow-color, #fff); }
          :host([color="olive"]) span { background: var(--canvas-badge-olive-bg, var(--palette-olive, #b5cc18)); color: var(--canvas-badge-olive-color, #fff); }
          :host([color="green"]) span { background: var(--canvas-badge-green-bg, var(--palette-green, #21ba45)); color: var(--canvas-badge-green-color, #fff); }
          :host([color="teal"]) span { background: var(--canvas-badge-teal-bg, var(--palette-teal, #00b5ad)); color: var(--canvas-badge-teal-color, #fff); }
          :host([color="blue"]) span { background: var(--canvas-badge-blue-bg, var(--palette-blue, #2185d0)); color: var(--canvas-badge-blue-color, #fff); }
          :host([color="violet"]) span { background: var(--canvas-badge-violet-bg, var(--palette-violet, #6435c9)); color: var(--canvas-badge-violet-color, #fff); }
          :host([color="purple"]) span { background: var(--canvas-badge-purple-bg, var(--palette-purple, #a333c8)); color: var(--canvas-badge-purple-color, #fff); }
          :host([color="pink"]) span { background: var(--canvas-badge-pink-bg, var(--palette-pink, #e03997)); color: var(--canvas-badge-pink-color, #fff); }
          :host([color="brown"]) span { background: var(--canvas-badge-brown-bg, var(--palette-brown, #a5673f)); color: var(--canvas-badge-brown-color, #fff); }
          :host([color="grey"]) span { background: var(--canvas-badge-grey-bg, var(--palette-grey, #767676)); color: var(--canvas-badge-grey-color, #fff); }
          :host([color="black"]) span { background: var(--canvas-badge-black-bg, var(--palette-black, #1b1c1d)); color: var(--canvas-badge-black-color, #fff); }

          /* Sizes */
          :host([size="mini"]) span { font-size: var(--canvas-badge-font-size-mini, .64285714rem); }
          :host([size="tiny"]) span { font-size: var(--canvas-badge-font-size-tiny, .71428571rem); }
          :host([size="small"]) span { font-size: var(--canvas-badge-font-size-small, .78571429rem); }
          :host([size="large"]) span { font-size: var(--canvas-badge-font-size-large, 1rem); }

          /* Basic variant (white bg, colored border and text) */
          :host([basic]) span {
            background: #fff;
            border: 1px solid rgba(34, 36, 38, 0.15);
            color: rgba(0, 0, 0, 0.87);
          }
          :host([basic][color="red"]) span { background: #fff; color: var(--canvas-badge-red-bg, var(--palette-red, #db2828)); border-color: var(--canvas-badge-red-bg, var(--palette-red, #db2828)); }
          :host([basic][color="orange"]) span { background: #fff; color: var(--canvas-badge-orange-bg, var(--palette-orange, #f2711c)); border-color: var(--canvas-badge-orange-bg, var(--palette-orange, #f2711c)); }
          :host([basic][color="yellow"]) span { background: #fff; color: var(--canvas-badge-yellow-bg, var(--palette-yellow, #fbbd08)); border-color: var(--canvas-badge-yellow-bg, var(--palette-yellow, #fbbd08)); }
          :host([basic][color="olive"]) span { background: #fff; color: var(--canvas-badge-olive-bg, var(--palette-olive, #b5cc18)); border-color: var(--canvas-badge-olive-bg, var(--palette-olive, #b5cc18)); }
          :host([basic][color="green"]) span { background: #fff; color: var(--canvas-badge-green-bg, var(--palette-green, #21ba45)); border-color: var(--canvas-badge-green-bg, var(--palette-green, #21ba45)); }
          :host([basic][color="teal"]) span { background: #fff; color: var(--canvas-badge-teal-bg, var(--palette-teal, #00b5ad)); border-color: var(--canvas-badge-teal-bg, var(--palette-teal, #00b5ad)); }
          :host([basic][color="blue"]) span { background: #fff; color: var(--canvas-badge-blue-bg, var(--palette-blue, #2185d0)); border-color: var(--canvas-badge-blue-bg, var(--palette-blue, #2185d0)); }
          :host([basic][color="violet"]) span { background: #fff; color: var(--canvas-badge-violet-bg, var(--palette-violet, #6435c9)); border-color: var(--canvas-badge-violet-bg, var(--palette-violet, #6435c9)); }
          :host([basic][color="purple"]) span { background: #fff; color: var(--canvas-badge-purple-bg, var(--palette-purple, #a333c8)); border-color: var(--canvas-badge-purple-bg, var(--palette-purple, #a333c8)); }
          :host([basic][color="pink"]) span { background: #fff; color: var(--canvas-badge-pink-bg, var(--palette-pink, #e03997)); border-color: var(--canvas-badge-pink-bg, var(--palette-pink, #e03997)); }
          :host([basic][color="brown"]) span { background: #fff; color: var(--canvas-badge-brown-bg, var(--palette-brown, #a5673f)); border-color: var(--canvas-badge-brown-bg, var(--palette-brown, #a5673f)); }
          :host([basic][color="grey"]) span { background: #fff; color: var(--canvas-badge-grey-bg, var(--palette-grey, #767676)); border-color: var(--canvas-badge-grey-bg, var(--palette-grey, #767676)); }
          :host([basic][color="black"]) span { background: #fff; color: var(--canvas-badge-black-bg, var(--palette-black, #1b1c1d)); border-color: var(--canvas-badge-black-bg, var(--palette-black, #1b1c1d)); }

          /* Circular variant: circle for 1-2 chars, pill for 3+ */
          :host([circular]) span {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2em;
            min-height: 2em;
            padding: 0;
            border-radius: 500rem;
            box-sizing: border-box;
            aspect-ratio: 1;
          }

          :host([circular]) span.pill {
            aspect-ratio: auto;
            padding: 0 .5em;
          }
        </style>
        <span part="badge"><slot></slot></span>
      `;
      this._span = this.shadowRoot.querySelector('span');
      this._slot = this.shadowRoot.querySelector('slot');
    }

    connectedCallback() {
      this._slot.addEventListener('slotchange', () => this._updateShape());
      this._updateShape();
    }

    _updateShape() {
      var text = this.textContent.trim();
      if (text.length > 2) {
        this._span.classList.add('pill');
      } else {
        this._span.classList.remove('pill');
      }
    }
  }

  customElements.define('canvas-badge', CanvasBadge);
}
