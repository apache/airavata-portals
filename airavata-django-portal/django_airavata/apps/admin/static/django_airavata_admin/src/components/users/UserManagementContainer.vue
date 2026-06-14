<template>
  <main-layout
    title="Manage Users"
    subtitle="Search and manage gateway user accounts and group memberships."
  >
    <template v-slot:actions>
      <Button variant="outline" as-child>
        <router-link :to="{ name: 'extended-user-profile' }"
          >Extended User Profile</router-link
        >
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="outline">{{ menuText }}</Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem as-child>
            <router-link :to="{ name: 'identity-service-users' }"
              >Identity Service</router-link
            >
          </DropdownMenuItem>
          <DropdownMenuItem as-child>
            <router-link :to="{ name: 'unverified-email-users' }"
              >Unverified Emails</router-link
            >
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </template>
    <router-view></router-view>
  </main-layout>
</template>

<script>
import { components } from "django-airavata-common-ui";
export default {
  name: "user-management-container",
  components: { "main-layout": components.MainLayout },
  computed: {
    menuText() {
      if (this.$route.name === "identity-service-users") {
        return "Identity Service";
      } else if (this.$route.name === "unverified-email-users") {
        return "Unverified Emails";
      } else {
        return "Menu";
      }
    },
  },
};
</script>
