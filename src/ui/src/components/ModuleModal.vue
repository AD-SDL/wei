<template>
  <v-dialog class="pa-3" v-slot:default="{ isActive }" max-width="1000">
    <v-card>
      <v-card-title>
        <h1 class="title py-3 my-3">Module: {{ modal_title }}</h1>
      </v-card-title>
      <v-card-text class="subheading grey--text">
        <div>
          <p>{{ modal_text.description }}</p>
          <br>
          <h2>Actions</h2>
          <v-expansion-panels>
            <v-expansion-panel v-for="action in modal_text.actions" :key="action.name">
              <v-expansion-panel-title @click="set_text(action)">
                <h3>{{ action.name }}</h3>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <h4>Description</h4>
                <p class="py-1 my-1">{{ action.description }}</p>
                <h4>Arguments</h4>
                <v-data-table :headers="arg_headers" :items="action.args" hover items-per-page="-1"
                  no-data-text="No Arguments" density="compact">
                  <!-- eslint-disable vue/no-parsing-error-->
                  <template v-slot:item="{ item }: { item: any }">
                    <tr>
                      <td>{{ item.name }}</td>
                      <td>{{ item.type }}</td>
                      <td>{{ item.required }}</td>
                      <td>{{ item.default }}</td>
                      <td>{{ item.description }}</td>
                      <td v-if="item.type == 'Location'"><v-select @update:menu="set_text(action)" v-model="item.value"
                          :items="Object.keys(wc_state.locations)"></v-select></td>
                      <td v-else><v-text-field @update:focused="set_text(action)" height="20px" v-model="item.value"
                          dense>
                        </v-text-field></td>
                    </tr>
                  </template>
                  <template #bottom></template>
                </v-data-table>
                <h4 v-if="action.files.length > 0">Files</h4>
                <v-data-table v-if="action.files.length > 0" :headers="file_headers" :items="action.files" hover
                  items-per-page="-1" no-data-text="No Files" density="compact">
                  <template v-slot:item="{ item }: { item: any }">
                    <tr>
                      <td>{{ item.name }}</td>
                      <td>{{ item.required }}</td>
                      <td>{{ item.description }}</td>
                      <td><v-file-input v-model="item.value" label="File input"></v-file-input></td>
                    </tr>
                  </template>
                </v-data-table>
                <h4 v-if="action.results.length > 0">Results</h4>
                <v-data-table v-if="action.results.length > 0" :headers="result_headers" :items="action.results" hover
                  items-per-page="-1" no-data-text="No Results" density="compact">
                  <template v-slot:item="{ item }: { item: any }">
                    <tr>
                      <td>{{ item.label }}</td>
                      <td>{{ item.type }}</td>
                      <td>{{ item.description }}</td>
                    </tr>
                  </template>
                </v-data-table>
                <v-btn @click="send_wf(action); isActive.value = false">Send Action</v-btn>
                <v-btn @click="copy = !copy; set_text(action)">
                  <p v-if="(copy == false) ">Show Copyable Workflow Step</p>
                  <p v-else>Hide copyable workflow step</p>
                </v-btn>
                <div v-if="copy">
                  <vue-json-pretty :data="json_text" />
                  Copy YAML Step to Clipboard: <v-icon hover @click=copyAction(text)>
                    mdi-clipboard-plus-outline
                  </v-icon>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn flat @click="isActive.value = false" class="primary--text">close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
const props = defineProps(['modal_title', 'modal_text', 'main_url', 'wc_state'])
const arg_headers = [
  { title: 'Name', key: 'name' },
  { title: 'Type', key: 'type' },
  { title: 'Required', key: 'required' },
  { title: 'Default', key: 'default' },
  { title: 'Description', key: 'description' },
]
const copy = ref(false)
const file_headers = [
  { title: 'Name', key: 'name' },
  { title: 'Required', key: 'required' },
  { title: 'Description', key: 'description' },
]

const result_headers = [
  { title: 'Label', key: 'name' },
  { title: 'Type', key: 'type' },
  { title: 'Description', key: 'description' },
]
const text = ref()
const json_text = ref()
function set_text(action: any) {
  text.value = "- name : ".concat(action.name).concat("\n\t").concat(
    "module : ").concat(props.modal_text.name).concat("\n\t").concat(
      "action : ").concat(action.name).concat("\n\t").concat(
        "args : \n\t\t").concat(cleanArgs(action.args)).concat("checks : null \n\tcomment: a comment! \n\t")
  var args: { [k: string]: any } = {};
  action.args.forEach(function (arg: any) {

    if (arg.value === undefined) {
      args[arg.name] = arg.default
    }
    else {
      args[arg.name] = arg.value
    }
  }
  )
  json_text.value = {
    "name": action.name,
    "module": props.modal_title,
    "action": action.name,
    "args": args,
    "checks": null,
    "comment": "Test"
  }
}
async function send_wf(action: any) {
  var wf: any = {}
  wf.name = action.name
  wf.metadata = {
    "author": "dashboard",
    "info": "testing module",
    "version": "0"

  }
  wf.modules = [props.modal_title]
  const formData = new FormData();
  var args: { [k: string]: any } = {};
  action.args.forEach(function (arg: any) {

    if (arg.value === undefined) {
      args[arg.name] = arg.default
    }
    else {
      args[arg.name] = arg.value
    }

  })
  var files: { [k: string]: any } = {};
  action.files.forEach(function (file: any) {
    console.log(file)
    if (file.value === undefined) {
      files[file.name] = ""
    }
    else {

      files[file.name] = file.value.name
    }
  })
  wf.flowdef = [{
    "name": action.name,
    "module": props.modal_title,
    "action": action.name,
    "args": args,
    "checks": null,
    "comment": "Test",
    "files": files
  }]
  formData.append("workflow", JSON.stringify(wf))
  var formData2 = new FormData();
  formData2.append("json", JSON.stringify({ "experiment_name": action.name }))
  var info: any = await (await fetch(props.main_url.concat('/experiments/'), {
    method: "POST",
    body: JSON.stringify({ "experiment_name": action.name }),
    headers: {
      'Content-Type': 'application/json'
    }
  }
  )).json()
  formData.append("experiment_id", info["experiment_id"])
  action.files.forEach(function (file: any) {
    if (file.value) {
      formData.append("files", file.value)
    }
  })
  fetch(props.main_url.concat('/runs/start'), {
    method: "POST",
    body: formData
  });

}
function cleanArgs(args: any) {
  var test: string = ""
  args.forEach((arg: any) => {
    var precursor = ""
    if (test !== "") {
      precursor = "\t"
    }

    if (arg.value) {
      test = test.concat((precursor.concat(arg.name.concat(" : ").concat(arg.value).concat("\n\t"))));
    } else {
      test = test.concat((precursor.concat(arg.name.concat(" : ").concat(arg.default).concat("\n\t"))));
    }
  }
  )
  return test
}
function copyAction(test: any) {
  navigator.clipboard.writeText(test)
  alert("Copied!")
}
</script>
