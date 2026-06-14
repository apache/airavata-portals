<template>
  <Card>
    <CardHeader>
      <CardTitle>Extended User Profile</CardTitle>
    </CardHeader>
    <CardContent>
      <template v-if="items.length === 0">
        <a href="/admin/extended-user-profile" class="text-primary hover:underline"
          >Add additional user profile fields for gateway users to
          complete</a
        >
      </template>
      <Table v-else>
        <TableBody>
          <TableRow v-for="item in items" :key="item.name">
            <TableCell class="font-medium">{{ item.name }}</TableCell>
            <TableCell>
              <!-- only show a valid checkmark when there is a user provided value -->
              <Check
                v-if="item.value && item.valid"
                class="inline size-4 text-success"
              />
              <X
                v-if="!item.valid"
                class="inline size-4 text-destructive"
              />
              <template v-if="Array.isArray(item.value)">
                <ul class="inline-block list-disc pl-5">
                  <li v-for="result in item.value" :key="result">
                    {{ result }}
                  </li>
                </ul>
              </template>
              <template v-else> {{ item.value }} </template>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <a
        v-if="items.length > 0"
        href="/admin/extended-user-profile"
        class="text-sm text-muted-foreground hover:underline"
        >Add or edit these field definitions</a
      >
    </CardContent>
  </Card>
</template>

<script>
import { Check, X } from "@lucide/vue";
import { models } from "django-airavata-api";
import { mapActions, mapState } from "pinia";
import { useExtendedUserProfileStore } from "../../store/modules/extendedUserProfile";
export default {
  components: { Check, X },
  props: {
    iamUserProfile: {
      type: models.IAMUserProfile,
      required: true,
    },
  },
  created() {
    this.loadExtendedUserProfileFields();
    this.loadExtendedUserProfileValues({
      username: this.iamUserProfile.user_id,
    });
  },
  computed: {
    ...mapState(useExtendedUserProfileStore, [
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
    ...mapActions(useExtendedUserProfileStore, [
      "loadExtendedUserProfileFields",
      "loadExtendedUserProfileValues",
    ]),
    getValue(field) {
      return this.extendedUserProfileValues.find(
        (v) => v.ext_user_profile_field === field.id,
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
