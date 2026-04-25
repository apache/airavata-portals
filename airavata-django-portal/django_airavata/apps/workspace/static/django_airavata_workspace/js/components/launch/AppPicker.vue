<template>
  <div>
    <div class="d-flex flex-wrap gap-1 mb-2">
      <button
        v-for="cat in categories"
        :key="cat"
        type="button"
        class="btn btn-sm"
        :class="cat === activeCat ? 'btn-primary' : 'btn-light'"
        :data-test="`cat-${cat}`"
        @click="activeCat = cat"
      >
        {{ cat }}<span class="ms-1 opacity-50">{{ countByCat[cat] }}</span>
      </button>
    </div>
    <input
      v-model="search"
      type="search"
      class="form-control mb-2"
      data-test="app-search"
      placeholder="Filter…"
    />
    <div class="row g-2">
      <div
        v-for="a in filtered"
        :key="a.app_id"
        class="col-6 col-md-3"
        data-test="app-tile"
      >
        <button
          type="button"
          class="card w-100 text-start p-2"
          :class="{ 'border-primary': store.draft.app_id === a.app_id }"
          :data-test="`app-tile-${a.app_id}`"
          @click="pick(a)"
        >
          <strong>{{ a.name }}</strong>
          <span class="text-muted small d-block">{{ a.content.url }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { Application } from "django-airavata-common-ui/js/stores/launch-types";
import { useLaunchStore } from "django-airavata-common-ui/js/stores/launch";

const props = defineProps<{ applications: Application[] }>();
const store = useLaunchStore();
const activeCat = ref<string>("All");
const search = ref("");

const categories = computed(() => {
  const set = new Set<string>(["All"]);
  for (const a of props.applications) set.add(a.category);
  return Array.from(set);
});

const countByCat = computed<Record<string, number>>(() => {
  const out: Record<string, number> = { All: props.applications.length };
  for (const a of props.applications) out[a.category] = (out[a.category] ?? 0) + 1;
  return out;
});

const filtered = computed(() => {
  let xs = props.applications;
  if (activeCat.value !== "All") xs = xs.filter((a) => a.category === activeCat.value);
  if (search.value) {
    const n = search.value.toLowerCase();
    xs = xs.filter((a) => a.name.toLowerCase().includes(n));
  }
  return xs;
});

function pick(a: Application) {
  store.pickApp(a);
}
</script>
