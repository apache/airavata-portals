<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Datasets</h1>
        <p class="text-muted mb-0">Browse public datasets and manage your private ones.</p>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Owner</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="datasets.length === 0">
              <td colspan="4">
                <div class="table-empty">
                  <i class="fa fa-database table-empty__icon"></i>
                  <div class="table-empty__title">No datasets available yet</div>
                  <div class="table-empty__text">Datasets will appear here when created or shared with you.</div>
                </div>
              </td>
            </tr>
            <tr v-for="dataset in datasets" :key="dataset.id">
              <td>{{ dataset.name }}</td>
              <td>
                {{ dataset.owner }}
                <span v-if="dataset.isYou" class="badge badge-primary ml-1">You</span>
                <span v-else-if="dataset.isAdmin" class="badge badge-secondary ml-1">Admin</span>
              </td>
              <td>{{ dataset.created }}</td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "datasets-list-container",
  data() {
    return {
      datasets: [],
    };
  },
};
</script>
