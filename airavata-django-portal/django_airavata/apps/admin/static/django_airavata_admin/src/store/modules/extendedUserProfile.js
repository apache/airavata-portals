import { defineStore } from "pinia";
import { models, services } from "django-airavata-api";

function getField(state, field) {
  return state.extendedUserProfileFields.find((f) => f === field);
}
function setFieldProp(state, field, prop, value) {
  const extendedUserProfileField = getField(state, field);
  extendedUserProfileField[prop] = value;
}

// Pinia store replacing the namespaced Vuex `extendedUserProfile` module. Pinia
// has no mutations, so the former mutations are folded in as actions.
export const useExtendedUserProfileStore = defineStore("extendedUserProfile", {
  state: () => ({
    extendedUserProfileFields: null,
    extendedUserProfileValues: null,
    deletedExtendedUserProfileFields: [],
  }),
  getters: {
    getExtendedUserProfileFields: (state) => state.extendedUserProfileFields,
    getExtendedUserProfileValues: (state) => state.extendedUserProfileValues,
  },
  actions: {
    async loadExtendedUserProfileFields() {
      const extendedUserProfileFields =
        await services.ExtendedUserProfileFieldService.list();
      this.setExtendedUserProfileFields({ extendedUserProfileFields });
    },
    async loadExtendedUserProfileValues({ username }) {
      const extendedUserProfileValues =
        await services.ExtendedUserProfileValueService.list({ username });
      this.setExtendedUserProfileValues({ extendedUserProfileValues });
    },
    async saveExtendedUserProfileFields() {
      let order = 1;
      for (const field of this.extendedUserProfileFields) {
        this.setOrder({ field, order: order++ });
        if (field.supportsChoices) {
          for (let index = 0; index < field.choices.length; index++) {
            const choice = field.choices[index];
            this.setChoiceOrder({ choice, order: index });
          }
        }
        for (let index = 0; index < field.links.length; index++) {
          const link = field.links[index];
          this.setLinkOrder({ link, order: index });
        }
        // Create or update each field
        if (field.id) {
          await services.ExtendedUserProfileFieldService.update({
            lookup: field.id,
            data: field,
          });
        } else {
          await services.ExtendedUserProfileFieldService.create({
            data: field,
          });
        }
      }
      if (this.deletedExtendedUserProfileFields.length > 0) {
        for (const field of this.deletedExtendedUserProfileFields) {
          await services.ExtendedUserProfileFieldService.delete({
            lookup: field.id,
          });
        }
        this.resetDeletedExtendedUserProfileFields();
      }
      // Reload the fields
      this.loadExtendedUserProfileFields();
    },
    addExtendedUserProfileFieldOfType({ field_type }) {
      const field = new models.ExtendedUserProfileField({
        field_type,
        name: `New Field ${this.extendedUserProfileFields.length + 1}`,
        description: "",
        help_text: "",
        required: true,
        links: [],
        other: false,
        choices: [],
        checkbox_label: "",
      });
      this.addExtendedUserProfileField({ field });
    },
    setExtendedUserProfileFields({ extendedUserProfileFields }) {
      this.extendedUserProfileFields = extendedUserProfileFields;
    },
    setExtendedUserProfileValues({ extendedUserProfileValues }) {
      this.extendedUserProfileValues = extendedUserProfileValues;
    },
    setName({ value, field }) {
      setFieldProp(this, field, "name", value);
    },
    setCheckboxLabel({ value, field }) {
      setFieldProp(this, field, "checkbox_label", value);
    },
    setHelpText({ value, field }) {
      setFieldProp(this, field, "help_text", value);
    },
    setRequired({ value, field }) {
      setFieldProp(this, field, "required", value);
    },
    setOrder({ order, field }) {
      setFieldProp(this, field, "order", order);
    },
    setOther({ value, field }) {
      setFieldProp(this, field, "other", value);
    },
    addExtendedUserProfileField({ field }) {
      if (!this.extendedUserProfileFields) {
        this.extendedUserProfileFields = [];
      }
      this.extendedUserProfileFields.push(field);
    },
    addChoice({ field }) {
      field.choices.push(
        new models.ExtendedUserProfileFieldChoice({
          display_text: "",
        }),
      );
    },
    setChoiceOrder({ choice, order }) {
      choice.order = order;
    },
    updateChoiceDisplayText({ choice, display_text }) {
      choice.display_text = display_text;
    },
    updateChoiceIndex({ field, choice, index }) {
      const currentIndex = field.choices.indexOf(choice);
      field.choices.splice(currentIndex, 1);
      field.choices.splice(index, 0, choice);
    },
    deleteChoice({ field, choice }) {
      const index = field.choices.indexOf(choice);
      field.choices.splice(index, 1);
    },
    addLink({ field }) {
      field.links.push(
        new models.ExtendedUserProfileFieldLink({
          label: "",
          url: "",
          display_link: true,
          display_inline: false,
        }),
      );
    },
    updateLinkLabel({ link, label }) {
      link.label = label;
    },
    updateLinkURL({ link, url }) {
      link.url = url;
    },
    updateLinkDisplayLink({ link, display_link }) {
      link.display_link = display_link;
    },
    updateLinkDisplayInline({ link, display_inline }) {
      link.display_inline = display_inline;
    },
    setLinkOrder({ link, order }) {
      link.order = order;
    },
    deleteLink({ field, link }) {
      const index = field.links.indexOf(link);
      field.links.splice(index, 1);
    },
    updateFieldIndex({ field, index }) {
      const currentIndex = this.extendedUserProfileFields.indexOf(field);
      this.extendedUserProfileFields.splice(currentIndex, 1);
      this.extendedUserProfileFields.splice(index, 0, field);
    },
    deleteField({ field }) {
      const index = this.extendedUserProfileFields.indexOf(field);
      this.extendedUserProfileFields.splice(index, 1);
      // later when we save we'll need to sync this delete with the server
      if (field.id) {
        this.deletedExtendedUserProfileFields.push(field);
      }
    },
    resetDeletedExtendedUserProfileFields() {
      this.deletedExtendedUserProfileFields = [];
    },
  },
});
