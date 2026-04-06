if (!customElements.get('canvas-sortable-item')) {
  class CanvasSortableItem extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
            transition: transform 0.2s ease;
          }

          :host([dragging]) {
            opacity: 0.9;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            background: #fff;
            border-radius: var(--radius, .28571429rem);
            pointer-events: none;
          }

          .handle {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            width: 20px;
            height: 20px;
            cursor: grab;
            color: rgba(0, 0, 0, 0.4);
            border-radius: var(--radius, .28571429rem);
          }

          .handle:hover {
            color: rgba(0, 0, 0, 0.7);
            background: rgba(0, 0, 0, 0.05);
          }

          .handle:active {
            cursor: grabbing;
          }

          .handle svg {
            pointer-events: none;
          }

          .content {
            flex: 1;
            min-width: 0;
          }
        </style>
        <span class="handle">
          <svg width="10" height="16" viewBox="0 0 10 16" fill="currentColor">
            <circle cx="2" cy="2" r="1.5"/>
            <circle cx="8" cy="2" r="1.5"/>
            <circle cx="2" cy="7" r="1.5"/>
            <circle cx="8" cy="7" r="1.5"/>
            <circle cx="2" cy="12" r="1.5"/>
            <circle cx="8" cy="12" r="1.5"/>
          </svg>
        </span>
        <div class="content"><slot></slot></div>
      `;

      var handle = this.shadowRoot.querySelector('.handle');
      handle.setAttribute('tabindex', '0');
      handle.setAttribute('role', 'button');
      handle.setAttribute('aria-label', 'Reorder');
      handle.setAttribute('aria-roledescription', 'sortable');

      var self = this;
      handle.addEventListener('keydown', function(e) {
        if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
        e.preventDefault();

        var list = self.closest('canvas-sortable-list');
        if (!list) return;

        var items = Array.prototype.slice.call(
          list.querySelectorAll('canvas-sortable-item')
        );
        var currentIndex = items.indexOf(self);
        var newIndex;

        if (e.key === 'ArrowUp' && currentIndex > 0) {
          newIndex = currentIndex - 1;
          list.insertBefore(self, items[newIndex]);
        } else if (e.key === 'ArrowDown' && currentIndex < items.length - 1) {
          newIndex = currentIndex + 1;
          list.insertBefore(self, items[newIndex].nextSibling);
        } else {
          return;
        }

        var event = new CustomEvent('reorder', {
          bubbles: true,
          composed: true,
          detail: {
            oldIndex: currentIndex,
            newIndex: newIndex,
            item: self
          }
        });
        list.dispatchEvent(event);

        handle.focus();
      });
    }
  }

  customElements.define('canvas-sortable-item', CanvasSortableItem);
}

if (!customElements.get('canvas-sortable-list')) {
  class CanvasSortableList extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            position: relative;
          }

          ::slotted(canvas-sortable-item) {
            display: flex;
          }
        </style>
        <slot></slot>
      `;

      this._dragging = false;
      this._dragItem = null;
      this._dragSourceIndex = -1;
      this._placeholder = null;
      this._startY = 0;
      this._offsetY = 0;
      this._itemHeight = 0;

      this._onPointerDown = this._onPointerDown.bind(this);
      this._onPointerMove = this._onPointerMove.bind(this);
      this._onPointerUp = this._onPointerUp.bind(this);
    }

    connectedCallback() {
      this.addEventListener('pointerdown', this._onPointerDown);
    }

    disconnectedCallback() {
      this.removeEventListener('pointerdown', this._onPointerDown);
      this._cleanup();
    }

    _getItems() {
      return Array.prototype.slice.call(this.querySelectorAll('canvas-sortable-item:not([dragging])'));
    }

    _getHandleFromEvent(e) {
      /* Walk from the event target up through shadow roots to find .handle */
      var node = e.composedPath ? e.composedPath() : [];
      for (var i = 0; i < node.length; i++) {
        if (node[i].classList && node[i].classList.contains('handle')) return node[i];
      }
      return null;
    }

    _getItemFromHandle(handle) {
      /* The handle lives in the shadow root of a canvas-sortable-item */
      var root = handle.getRootNode();
      if (root && root.host && root.host.tagName === 'CANVAS-SORTABLE-ITEM') {
        return root.host;
      }
      return null;
    }

    _onPointerDown(e) {
      if (this._dragging) return;

      var handle = this._getHandleFromEvent(e);
      if (!handle) return;

      var item = this._getItemFromHandle(handle);
      if (!item) return;

      e.preventDefault();

      var items = this._getItems();
      this._dragSourceIndex = items.indexOf(item);
      this._dragItem = item;

      var rect = item.getBoundingClientRect();
      this._itemHeight = rect.height;
      this._startY = e.clientY;
      this._offsetY = e.clientY - rect.top;

      /* Measure all item positions before we start moving things */
      this._itemRects = [];
      for (var i = 0; i < items.length; i++) {
        this._itemRects.push(items[i].getBoundingClientRect());
      }

      /* Create a plain div placeholder that holds the space */
      this._placeholder = document.createElement('div');
      this._placeholder.style.height = rect.height + 'px';
      this._placeholder.style.transition = 'height 0.2s ease';
      this._placeholder.style.pointerEvents = 'none';
      item.parentNode.insertBefore(this._placeholder, item);

      /* Position the dragged item as fixed overlay */
      item.setAttribute('dragging', '');
      item.style.position = 'fixed';
      item.style.left = rect.left + 'px';
      item.style.top = rect.top + 'px';
      item.style.width = rect.width + 'px';
      item.style.transition = 'none';

      this._dragging = true;

      /* Force grabbing cursor everywhere and disable pointer events on list items
         so shadow DOM cursor rules cannot override the global cursor */
      this._cursorStyle = document.createElement('style');
      this._cursorStyle.textContent = '* { cursor: grabbing !important; user-select: none !important; }';
      document.head.appendChild(this._cursorStyle);
      this.style.pointerEvents = 'none';

      document.addEventListener('pointermove', this._onPointerMove);
      document.addEventListener('pointerup', this._onPointerUp);
    }

    _onPointerMove(e) {
      if (!this._dragging || !this._dragItem) return;

      /* Move the dragged item to follow the cursor */
      var newTop = e.clientY - this._offsetY;
      this._dragItem.style.top = newTop + 'px';

      /* Find where the placeholder should be based on cursor Y */
      var centerY = e.clientY;
      var items = this._getItems();
      var targetIndex = -1;

      for (var i = 0; i < items.length; i++) {
        var rect = items[i].getBoundingClientRect();
        var midY = rect.top + rect.height / 2;
        if (centerY < midY) {
          targetIndex = i;
          break;
        }
      }

      /* If cursor is below all items, place at the end */
      if (targetIndex === -1) {
        targetIndex = items.length;
      }

      /* Figure out which item the placeholder is currently next to */
      var currentNext = this._placeholder.nextElementSibling;
      var desiredNext = (targetIndex < items.length) ? items[targetIndex] : null;

      /* If placeholder is already in the right spot, nothing to do */
      if (currentNext === desiredNext) return;

      /* FLIP animation. Record positions before DOM change. */
      var rects = {};
      for (var i = 0; i < items.length; i++) {
        rects[i] = items[i].getBoundingClientRect();
      }

      /* Move the placeholder in the DOM */
      if (desiredNext) {
        this.insertBefore(this._placeholder, desiredNext);
      } else {
        this.appendChild(this._placeholder);
      }

      /* FLIP. Measure new positions and animate from old to new. */
      for (var i = 0; i < items.length; i++) {
        var oldRect = rects[i];
        var newRect = items[i].getBoundingClientRect();
        var deltaY = oldRect.top - newRect.top;
        if (Math.abs(deltaY) < 1) continue;

        items[i].style.transition = 'none';
        items[i].style.transform = 'translateY(' + deltaY + 'px)';

        /* Force reflow so the browser picks up the transform */
        items[i].offsetHeight;

        items[i].style.transition = 'transform 0.2s ease';
        items[i].style.transform = 'translateY(0)';
      }
    }

    _onPointerUp(e) {
      if (!this._dragging || !this._dragItem) {
        this._cleanup();
        return;
      }

      var item = this._dragItem;

      /* Insert the real item where the placeholder is */
      this.insertBefore(item, this._placeholder);

      /* Remove placeholder */
      if (this._placeholder && this._placeholder.parentNode) {
        this._placeholder.parentNode.removeChild(this._placeholder);
      }

      /* Reset styles on the dragged item */
      item.removeAttribute('dragging');
      item.style.position = '';
      item.style.left = '';
      item.style.top = '';
      item.style.width = '';
      item.style.transition = '';
      item.style.transform = '';

      /* Calculate new index and fire event */
      var items = this._getItems();
      var newIndex = items.indexOf(item);

      if (this._dragSourceIndex !== newIndex) {
        this.dispatchEvent(new CustomEvent('reorder', {
          bubbles: true,
          composed: true,
          cancelable: true,
          detail: {
            oldIndex: this._dragSourceIndex,
            newIndex: newIndex,
            item: item
          }
        }));
      }

      this._cleanup();
    }

    _cleanup() {
      this.style.pointerEvents = '';
      if (this._cursorStyle && this._cursorStyle.parentNode) {
        this._cursorStyle.parentNode.removeChild(this._cursorStyle);
      }
      this._cursorStyle = null;

      /* Clean up inline transition styles on all items */
      var items = this._getItems();
      for (var i = 0; i < items.length; i++) {
        items[i].style.transition = '';
        items[i].style.transform = '';
      }

      this._dragging = false;
      this._dragItem = null;
      this._dragSourceIndex = -1;
      this._itemRects = null;

      if (this._placeholder && this._placeholder.parentNode) {
        this._placeholder.parentNode.removeChild(this._placeholder);
      }
      this._placeholder = null;

      document.removeEventListener('pointermove', this._onPointerMove);
      document.removeEventListener('pointerup', this._onPointerUp);
    }
  }

  customElements.define('canvas-sortable-list', CanvasSortableList);
}
