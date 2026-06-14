<template>
  <Card>
    <CardHeader>
      <CardTitle>External IDP Userinfo</CardTitle>
    </CardHeader>
    <CardContent>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Claim</TableHead>
            <TableHead>Value</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="row in sortedItems" :key="row.claim">
            <TableCell class="font-medium">{{ row.claim }}</TableCell>
            <TableCell>{{ row.value }}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <small class="text-sm text-muted-foreground"
        >This is the user information provided by the user's authentication
        provider. The IDP alias used is
        {{ externalIDPUserInfo.idp_alias || "N/A" }}.
      </small>
    </CardContent>
  </Card>
</template>

<script>
export default {
  name: "external-idp-user-info-panel",
  props: ["externalIDPUserInfo"],
  computed: {
    userinfo() {
      return this.externalIDPUserInfo.userinfo
        ? this.externalIDPUserInfo.userinfo
        : {};
    },
    items() {
      return Object.keys(this.userinfo).map((claim) => {
        return {
          claim: claim,
          value: this.externalIDPUserInfo.userinfo[claim],
        };
      });
    },
    sortedItems() {
      return this.items.slice().sort((a, b) => a.claim.localeCompare(b.claim));
    },
  },
};
</script>

<style></style>
