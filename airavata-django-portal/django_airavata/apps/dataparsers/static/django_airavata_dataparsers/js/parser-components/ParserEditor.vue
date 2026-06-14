<template>
  <div class="space-y-6">
    <Card>
      <CardContent>
        <Alert
          v-if="showDismissibleAlert.dismissable"
          :variant="
            showDismissibleAlert.variant === 'destructive'
              ? 'destructive'
              : 'default'
          "
          class="mb-4"
        >
          <AlertDescription class="flex w-full items-start gap-2">
            <span>{{ showDismissibleAlert.message }}</span>
            <Button
              variant="ghost"
              size="icon"
              class="ml-auto shrink-0"
              @click="showDismissibleAlert.dismissable = false"
            >
              <X class="size-4" />
            </Button>
          </AlertDescription>
        </Alert>

        <form class="space-y-4">
          <div class="space-y-1.5">
            <Label for="parser_name">Parser Name</Label>
            <Input
              id="parser_name"
              type="text"
              v-model="localParser.id"
              required
              placeholder="Enter parser name"
            />
            <p class="text-sm text-muted-foreground">
              Name should only contain alpha characters.
            </p>
          </div>

          <div class="space-y-1.5">
            <Label for="docker-image">Docker Image</Label>
            <Input
              id="docker-image"
              type="text"
              v-model="localParser.image_name"
              required
              placeholder="Enter the Docker image name"
            />
          </div>

          <div class="space-y-1.5">
            <Label for="input-path">Input Data Directory</Label>
            <Input
              id="input-path"
              type="text"
              v-model="localParser.input_dir_path"
              required
              placeholder="Enter input directory of the container"
            />
          </div>

          <div class="space-y-1.5">
            <Label for="output-path">Output Data Directory</Label>
            <Input
              id="output-path"
              type="text"
              v-model="localParser.output_dir_path"
              required
              placeholder="Enter output directory of the container"
            />
          </div>
        </form>
      </CardContent>
    </Card>

    <Card>
      <CardContent>
        <list-layout
          :items="localParser.input_files"
          title="Inputs"
          new-item-button-text="New Input"
          @add-new-item="createInput"
        >
          <template #item-list="slotProps">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead v-for="field in parserInputFields" :key="field.key">
                    {{ field.label }}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="(item, index) in slotProps.items"
                  :key="index"
                >
                  <TableCell
                    v-for="field in parserInputFields"
                    :key="field.key"
                  >
                    {{ formatCell(field, item) }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </template>
        </list-layout>
      </CardContent>
    </Card>

    <Card>
      <CardContent>
        <list-layout
          :items="localParser.output_files"
          title="Outputs"
          new-item-button-text="New Output"
          @add-new-item="createOutput"
        >
          <template #item-list="slotProps">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    v-for="field in parserOutputFields"
                    :key="field.key"
                  >
                    {{ field.label }}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="(item, index) in slotProps.items"
                  :key="index"
                >
                  <TableCell
                    v-for="field in parserOutputFields"
                    :key="field.key"
                  >
                    {{ formatCell(field, item) }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </template>
        </list-layout>
      </CardContent>
    </Card>
    <div class="flex justify-end gap-2">
      <Button variant="secondary" @click="cancel">Cancel</Button>
      <Button v-if="parser" variant="destructive" @click="removeParser"
        >Delete</Button
      >
      <Button variant="default" @click="saveParser">Save</Button>
    </div>
  </div>
</template>

<script>
import { X } from "@lucide/vue";
import { models, services } from "django-airavata-api";
// Deep import (not the `index.js` barrel) so this bundle does not also pull in
// the shared `Uppy` component, whose `@uppy/status-bar/dist/style.min.css` import
// is not resolvable under that package's `exports` field. See the
// TODO(vue3-migration) note in the migration report.
import ListLayout from "django-airavata-common-ui/js/layouts/ListLayout.vue";

export default {
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
          key: "required_input",
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
          key: "required_output",
        },
        {
          label: "Type",
          key: "type",
          formatter: (value) => value.name,
        },
      ],
    };
  },
  components: {
    X,
    "list-layout": ListLayout,
  },
  methods: {
    formatCell: function (field, item) {
      const value = item[field.key];
      return field.formatter ? field.formatter(value) : value;
    },
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
