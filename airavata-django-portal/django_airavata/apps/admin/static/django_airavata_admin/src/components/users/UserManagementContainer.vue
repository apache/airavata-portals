<template>
  <div>
    <div class="mb-4 flex items-center gap-2">
      <h1 class="mr-auto text-xl font-semibold">Manage Users</h1>
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
    </div>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: "user-management-container",
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
