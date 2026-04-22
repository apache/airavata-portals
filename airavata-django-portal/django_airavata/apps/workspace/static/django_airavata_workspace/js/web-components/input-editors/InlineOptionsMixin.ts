interface SelectOption {
  text: string | null;
  value: string;
}

export default {
  data(): { inlineOptions: SelectOption[] } {
    return {
      inlineOptions: [],
    };
  },
  computed: {
    allOptions(): SelectOption[] | null {
      // Copy options
      const self = this as unknown as {
        options?: SelectOption[];
        inlineOptions: SelectOption[];
      };
      const result: SelectOption[] = self.options ? self.options.slice() : [];
      // Copy inlineOptions into result
      result.push(...self.inlineOptions);
      // return null if empty
      return result.length > 0 ? result : null;
    },
  },
  mounted() {
    (this as unknown as { $nextTick: (fn: () => void) => void }).$nextTick(
      () => {
        // Create default slot programmatically
        const self = this as unknown as {
          $refs: Record<string, Element>;
          $el: Element;
          readInlineOptions: () => void;
          addInlineOptionsChangeListener: () => void;
        };
        self.$refs.optionsSlot.append(document.createElement("slot"));
        self.readInlineOptions();
        self.addInlineOptionsChangeListener();
      }
    );
  },
  unmounted() {
    (
      this as unknown as { removeInlineOptionsChangeListener: () => void }
    ).removeInlineOptionsChangeListener();
  },
  methods: {
    readInlineOptions(): void {
      const self = this as unknown as {
        $el: Element;
        inlineOptions: SelectOption[];
      };
      const slot = self.$el.querySelector("slot") as HTMLSlotElement | null;
      if (!slot) return;
      const els = slot.assignedElements();
      self.inlineOptions = [];
      for (const el of els) {
        if (el.tagName === "OPTION") {
          const opt = el as HTMLOptionElement;
          self.inlineOptions.push({ text: opt.textContent, value: opt.value });
        }
      }
    },
    addInlineOptionsChangeListener(): void {
      const self = this as unknown as {
        $el: Element;
        readInlineOptions: () => void;
      };
      const slot = self.$el.querySelector("slot") as HTMLSlotElement | null;
      if (!slot) return;
      // listen for changing options https://developer.mozilla.org/en-US/docs/Web/API/HTMLSlotElement#examples
      slot.addEventListener("slotchange", self.readInlineOptions);
    },
    removeInlineOptionsChangeListener(): void {
      const self = this as unknown as {
        $el: Element;
        readInlineOptions: () => void;
      };
      const slot = self.$el.querySelector("slot") as HTMLSlotElement | null;
      if (!slot) return;
      slot.removeEventListener("slotchange", self.readInlineOptions);
    },
  },
};
