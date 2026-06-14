<template>
  <main-layout
    title="Developer Console"
    subtitle="Resources and tools for local gateway development."
  >
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
  </main-layout>
</template>
<script>
import { Download } from "@lucide/vue";
import { components } from "django-airavata-common-ui";
export default {
  components: { Download, "main-layout": components.MainLayout },
};
</script>
