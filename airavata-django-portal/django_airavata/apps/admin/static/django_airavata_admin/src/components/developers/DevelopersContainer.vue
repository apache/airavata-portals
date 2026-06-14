<template>
  <div>
    <div>
      <h1 class="mb-4 text-xl font-semibold">Developer Console</h1>
    </div>
    <Card>
      <CardHeader>
        <CardTitle
          >Download a settings_local.py file for local development</CardTitle
        >
      </CardHeader>
      <CardContent>
        <a
          href="/auth/settings-local"
          class="inline-flex items-center gap-1 text-primary hover:underline"
        >
          <Download class="size-4" />
          Download
        </a>
      </CardContent>
    </Card>
  </div>
</template>
<script>
import { Download } from "@lucide/vue";
export default {
  components: { Download },
};
</script>
