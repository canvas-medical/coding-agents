if (!customElements.get('canvas-chip')) {
  class CanvasChip extends HTMLElement {

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: inline-flex;
            vertical-align: baseline;
          }

          span {
            display: inline-flex;
            align-items: center;
            gap: .4em;
            line-height: 1;
            margin: 0 .14285714em;
            padding: var(--canvas-chip-padding, .5833em .708em .5833em .833em);
            font-weight: var(--canvas-chip-font-weight, var(--font-weight-bold, 700));
            font-family: var(--canvas-chip-font-family, var(--font-family, lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif));
            font-size: var(--canvas-chip-font-size, .85714286rem);
            border: var(--canvas-chip-border, 0 solid transparent);
            border-radius: var(--canvas-chip-radius, var(--radius, .28571429rem));
            background: var(--canvas-chip-bg, #e8e8e8);
            color: var(--canvas-chip-color, rgba(0, 0, 0, 0.6));
            white-space: nowrap;
            transition: background 0.1s ease;
          }

          /* Solid colors */
          :host([color="red"]) span { background: var(--canvas-chip-red-bg, var(--palette-red, #db2828)); color: var(--canvas-chip-red-color, #fff); }
          :host([color="orange"]) span { background: var(--canvas-chip-orange-bg, var(--palette-orange, #f2711c)); color: var(--canvas-chip-orange-color, #fff); }
          :host([color="yellow"]) span { background: var(--canvas-chip-yellow-bg, var(--palette-yellow, #fbbd08)); color: var(--canvas-chip-yellow-color, #fff); }
          :host([color="olive"]) span { background: var(--canvas-chip-olive-bg, var(--palette-olive, #b5cc18)); color: var(--canvas-chip-olive-color, #fff); }
          :host([color="green"]) span { background: var(--canvas-chip-green-bg, var(--palette-green, #21ba45)); color: var(--canvas-chip-green-color, #fff); }
          :host([color="teal"]) span { background: var(--canvas-chip-teal-bg, var(--palette-teal, #00b5ad)); color: var(--canvas-chip-teal-color, #fff); }
          :host([color="blue"]) span { background: var(--canvas-chip-blue-bg, var(--palette-blue, #2185d0)); color: var(--canvas-chip-blue-color, #fff); }
          :host([color="violet"]) span { background: var(--canvas-chip-violet-bg, var(--palette-violet, #6435c9)); color: var(--canvas-chip-violet-color, #fff); }
          :host([color="purple"]) span { background: var(--canvas-chip-purple-bg, var(--palette-purple, #a333c8)); color: var(--canvas-chip-purple-color, #fff); }
          :host([color="pink"]) span { background: var(--canvas-chip-pink-bg, var(--palette-pink, #e03997)); color: var(--canvas-chip-pink-color, #fff); }
          :host([color="brown"]) span { background: var(--canvas-chip-brown-bg, var(--palette-brown, #a5673f)); color: var(--canvas-chip-brown-color, #fff); }
          :host([color="grey"]) span { background: var(--canvas-chip-grey-bg, var(--palette-grey, #767676)); color: var(--canvas-chip-grey-color, #fff); }
          :host([color="black"]) span { background: var(--canvas-chip-black-bg, var(--palette-black, #1b1c1d)); color: var(--canvas-chip-black-color, #fff); }

          /* Sizes */
          :host([size="mini"]) span { font-size: var(--canvas-chip-font-size-mini, .64285714rem); }
          :host([size="tiny"]) span { font-size: var(--canvas-chip-font-size-tiny, .71428571rem); }
          :host([size="small"]) span { font-size: var(--canvas-chip-font-size-small, .78571429rem); }

          /* Basic variant */
          :host([basic]) span {
            background: #fff;
            border: 1px solid rgba(34, 36, 38, 0.15);
            color: rgba(0, 0, 0, 0.87);
          }
          :host([basic][color="red"]) span { background: #fff; color: var(--canvas-chip-red-bg, var(--palette-red, #db2828)); border-color: var(--canvas-chip-red-bg, var(--palette-red, #db2828)); }
          :host([basic][color="orange"]) span { background: #fff; color: var(--canvas-chip-orange-bg, var(--palette-orange, #f2711c)); border-color: var(--canvas-chip-orange-bg, var(--palette-orange, #f2711c)); }
          :host([basic][color="yellow"]) span { background: #fff; color: var(--canvas-chip-yellow-bg, var(--palette-yellow, #fbbd08)); border-color: var(--canvas-chip-yellow-bg, var(--palette-yellow, #fbbd08)); }
          :host([basic][color="olive"]) span { background: #fff; color: var(--canvas-chip-olive-bg, var(--palette-olive, #b5cc18)); border-color: var(--canvas-chip-olive-bg, var(--palette-olive, #b5cc18)); }
          :host([basic][color="green"]) span { background: #fff; color: var(--canvas-chip-green-bg, var(--palette-green, #21ba45)); border-color: var(--canvas-chip-green-bg, var(--palette-green, #21ba45)); }
          :host([basic][color="teal"]) span { background: #fff; color: var(--canvas-chip-teal-bg, var(--palette-teal, #00b5ad)); border-color: var(--canvas-chip-teal-bg, var(--palette-teal, #00b5ad)); }
          :host([basic][color="blue"]) span { background: #fff; color: var(--canvas-chip-blue-bg, var(--palette-blue, #2185d0)); border-color: var(--canvas-chip-blue-bg, var(--palette-blue, #2185d0)); }
          :host([basic][color="violet"]) span { background: #fff; color: var(--canvas-chip-violet-bg, var(--palette-violet, #6435c9)); border-color: var(--canvas-chip-violet-bg, var(--palette-violet, #6435c9)); }
          :host([basic][color="purple"]) span { background: #fff; color: var(--canvas-chip-purple-bg, var(--palette-purple, #a333c8)); border-color: var(--canvas-chip-purple-bg, var(--palette-purple, #a333c8)); }
          :host([basic][color="pink"]) span { background: #fff; color: var(--canvas-chip-pink-bg, var(--palette-pink, #e03997)); border-color: var(--canvas-chip-pink-bg, var(--palette-pink, #e03997)); }
          :host([basic][color="brown"]) span { background: #fff; color: var(--canvas-chip-brown-bg, var(--palette-brown, #a5673f)); border-color: var(--canvas-chip-brown-bg, var(--palette-brown, #a5673f)); }
          :host([basic][color="grey"]) span { background: #fff; color: var(--canvas-chip-grey-bg, var(--palette-grey, #767676)); border-color: var(--canvas-chip-grey-bg, var(--palette-grey, #767676)); }
          :host([basic][color="black"]) span { background: #fff; color: var(--canvas-chip-black-bg, var(--palette-black, #1b1c1d)); border-color: var(--canvas-chip-black-bg, var(--palette-black, #1b1c1d)); }

          /* Dismiss button */
          .dismiss {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1em;
            height: 1em;
            padding: 0;
            border: none;
            background: transparent;
            color: inherit;
            opacity: 0.7;
            cursor: pointer;
            line-height: 1;
            transition: opacity 0.1s ease;
            flex-shrink: 0;
          }

          .dismiss:hover { opacity: 1; }
          .dismiss svg { display: block; }

        </style>
        <span part="chip">
          <slot></slot>
          <button class="dismiss" aria-label="Dismiss">
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path d="M1.5 1.5l7 7M8.5 1.5l-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </span>
      `;
      this._dismiss = this.shadowRoot.querySelector('.dismiss');
    }

    connectedCallback() {
      this._dismiss.addEventListener('click', this._handleDismiss.bind(this));
    }

    disconnectedCallback() {
      this._dismiss.removeEventListener('click', this._handleDismiss.bind(this));
    }

    _handleDismiss(e) {
      e.stopPropagation();
      this.dispatchEvent(new CustomEvent('dismiss', { bubbles: true, composed: true }));
    }
  }

  customElements.define('canvas-chip', CanvasChip);
}
