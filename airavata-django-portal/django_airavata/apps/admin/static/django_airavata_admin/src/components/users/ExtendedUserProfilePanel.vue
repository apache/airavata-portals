<template>
  <div class="card">
    <div class="card-header">Extended User Profile</div>
    <div class="card-body">
      <template v-if="items.length === 0">
        <a href="/admin/extended-user-profile"
          >Add additional user profile fields for gateway users to
          complete</a
        >
      </template>
      <table class="table table-sm table-borderless mb-0" v-else>
        <thead>
          <tr>
            <th>name</th>
            <th>value</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.name">
            <td>{{ item.name }}</td>
            <td>
              <!-- only show a valid checkmark when there is a user provided value -->
              <i v-if="item.value && item.valid" class="fas fa-check text-success"></i>
              <i v-if="!item.valid" class="fas fa-times text-danger"></i>
              <template v-if="Array.isArray(item.value)">
                <ul>
                  <li v-for="result in item.value" :key="result">
                    {{ result }}
                  </li>
                </ul>
              </template>
              <template v-else> {{ item.value }} </template>
            </td>
          </tr>
        </tbody>
      </table>
      <a
        v-if="items.length > 0"
        href="/admin/extended-user-profile"
        class="text-muted small"
        >Add or edit these field definitions</a
      >
    </div>
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { mapActions, mapGetters } from "vuex";
export default {
  props: {
    iamUserProfile: {
      type: models.IAMUserProfile,
      required: true,
    },
  },
  created() {
    this.loadExtendedUserProfileFields();
    this.loadExtendedUserProfileValues({
      username: this.iamUserProfile.userId,
    });
  },
  computed: {
    ...mapGetters("extendedUserProfile", [
      "extendedUserProfileFields",
      "extendedUserProfileValues",
    ]),
    fields() {
      return ["name", "value"];
    },
    items() {
      if (this.extendedUserProfileFields && this.extendedUserProfileValues) {
        const items = [];
        for (const field of this.extendedUserProfileFields) {
          const value = this.getValue(field);
          items.push({
            name: field.name,
            value: value ? value.value_display : null,
            // if no value, consider it invalid only if it is required
            valid: value ? value.valid : !field.required,
          });
        }
        return items;
      } else {
        return [];
      }
    },
  },
  methods: {
    ...mapActions("extendedUserProfile", [
      "loadExtendedUserProfileFields",
      "loadExtendedUserProfileValues",
    ]),
    getValue(field) {
      return this.extendedUserProfileValues.find(
        (v) => v.ext_user_profile_field === field.id
      );
    },
  },
};
</script>

<style scoped>
ul {
  display: inline-block;
  padding-left: 20px;
}
</style>
