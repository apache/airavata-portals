<template>
  <Card>
    <CardHeader>
      <CardTitle>User Profile</CardTitle>
    </CardHeader>
    <CardContent>
      <Table>
        <TableBody>
          <TableRow v-for="item in items" :key="item.name">
            <TableCell class="font-medium">{{ item.name }}</TableCell>
            <TableCell>
              <Check
                v-if="item.valid"
                class="inline size-4 text-success"
              />
              <X v-if="!item.valid" class="inline size-4 text-destructive" />
              {{ item.value }}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </CardContent>
  </Card>
</template>

<script>
import { Check, X } from "@lucide/vue";
import { models } from "django-airavata-api";
export default {
  components: { Check, X },
  props: {
    iamUserProfile: {
      type: models.IAMUserProfile,
      required: true,
    },
  },
  computed: {
    fields() {
      return ["name", "value"];
    },
    items() {
      if (!this.iamUserProfile) {
        return [];
      } else {
        return [
          {
            name: "Username",
            value: this.iamUserProfile.user_id,
            valid: this.isValid("username"),
          },
          {
            name: "Email",
            value: this.iamUserProfile.email,
            valid: this.isValid("email"),
          },
          {
            name: "First Name",
            value: this.iamUserProfile.first_name,
            valid: this.isValid("first_name"),
          },
          {
            name: "Last Name",
            value: this.iamUserProfile.last_name,
            valid: this.isValid("last_name"),
          },
        ];
      }
    },
  },
  methods: {
    isValid(fieldName) {
      return (
        this.iamUserProfile.user_profile_invalid_fields.indexOf(fieldName) < 0
      );
    },
  },
};
</script>

<style></style>
