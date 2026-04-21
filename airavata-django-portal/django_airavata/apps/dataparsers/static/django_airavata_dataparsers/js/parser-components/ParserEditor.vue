<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">{{ title }}</h1>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <div
              v-if="showDismissibleAlert.dismissable"
              :class="['alert', 'alert-' + showDismissibleAlert.variant]"
            >
              {{ showDismissibleAlert.message }}
            </div>

            <form>
              <form-group
                id="group1"
                label="Parser Name:"
                label-for="parser_name"
                description="Name should only contain Alpha Characters"
              >
                <input
                  id="parser_name"
                  v-model="localParser.id"
                  class="form-control"
                  type="text"
                  required
                  placeholder="Enter parser name"
                />
              </form-group>

              <form-group id="group2" label="Docker Image:" label-for="docker-image">
                <input
                  id="docker-image"
                  v-model="localParser.imageName"
                  class="form-control"
                  type="text"
                  required
                  placeholder="Enter the Docker Image name"
                />
              </form-group>

              <form-group id="group3" label="Input Data Directory:" label-for="input-path">
                <input
                  id="input-path"
                  v-model="localParser.inputDirPath"
                  class="form-control"
                  type="text"
                  required
                  placeholder="Enter input directory of the container"
                />
              </form-group>

              <form-group id="group4" label="Output Data Directory:" label-for="output-path">
                <input
                  id="output-path"
                  v-model="localParser.outputDirPath"
                  class="form-control"
                  type="text"
                  required
                  placeholder="Enter output directory of the container"
                />
              </form-group>
            </form>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <list-layout
              :items="localParser.inputFiles"
              title="Inputs"
              new-item-button-text="New Input"
              @add-new-item="createInput"
            >
              <template #item-list="slotProps">
                <!-- TODO: migrate to native HTML table -->
                <table
                  class="table"
                  hover
                  :fields="parserInputFields"
                  :items="slotProps.items"
                ></table>
              </template>
            </list-layout>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <list-layout
              :items="localParser.outputFiles"
              title="Outputs"
              new-item-button-text="New Output"
              @add-new-item="createOutput"
            >
              <template #item-list="slotProps">
                <!-- TODO: migrate to native HTML table -->
                <table
                  class="table"
                  hover
                  :fields="parserOutputFields"
                  :items="slotProps.items"
                ></table>
              </template>
            </list-layout>
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col d-flex justify-content-end">
        <button class="btn btn-primary" @click="saveParser">Save</button>
        <button v-if="parser" class="btn btn-danger ms-2" @click="removeParser">Delete</button>
        <button class="btn btn-secondary ms-2" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
import { models, services } from "django-airavata-api";
import { layouts } from "django-airavata-common-ui";

export default {
  components: {
    "list-layout": layouts.ListLayout,
  },
  props: {
    parser: {
      type: models.Parser,
      required: true,
    },
  },
  data() {
    return {
      localParser: this.parser.clone(),
      service: services.ServiceFactory.service("Parsers"),
      showDismissibleAlert: {
        variant: "success",
        message: "no data",
        dismissable: false,
      },
      parserInputFields: [
        {
          label: "Name",
          key: "name",
        },
        {
          label: "Required",
          key: "requiredInput",
        },
        {
          label: "Type",
          key: "type",
          formatter: (value) => value.name,
        },
      ],
      parserOutputFields: [
        {
          label: "Name",
          key: "name",
        },
        {
          label: "Required",
          key: "requiredOutput",
        },
        {
          label: "Type",
          key: "type",
          formatter: (value) => value.name,
        },
      ],
    };
  },
  computed: {
    title: function () {
      return this.parser ? this.parser.id : "New Parser";
    },
  },
  methods: {
    submitForm() {},
    createInput: function () {},
    createOutput: function () {},
    saveParser: function () {
      var persist = null;
      if (this.parser) {
        persist = this.service.update({
          data: this.localParser,
          lookup: this.parser.id,
        });
      } else {
        //persist = this.service.create({ data: this.localParser }).then(data => {
        // Merge sharing settings with default sharing settings created when
        // Group Resource Profile was created
        //const savedPArserId = data.id;
        // });
      }
      persist.then(() => {
        this.$emit("saved");
      });
    },
    removeParser: function () {},
    cancel: function () {
      this.$emit("cancelled");
    },
  },
};
</script>
