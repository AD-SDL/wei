<template>
  <v-container>
    <v-tabs v-model="tab" align-tabs="center" color="deep-purple-accent-4">
      <v-tab :value="1">Workcells</v-tab>
      <v-tab :value="2">Workflows</v-tab>
      <v-tab :value="3">Experiments</v-tab>
      <!-- <v-tab :value="4">Events</v-tab>
          <v-tab :value="5">Admin</v-tab>
          <v-tab :value="6">Resources</v-tab> -->
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item :key="1" :value="1">
        <v-container v-if="wc_state">
          <v-card class="pa-1">
            <v-card-title class="text-center">
              <h2>{{ wc_info.name }}</h2>
            </v-card-title>
            <v-card-text>
              <v-container class="pa-1">
                <v-row dense wrap justify-content="space-evenly">
                  <v-col cols=3 md=3 lg=3>
                    <ModuleColumn :modules=wc_state.modules :main_url=main_url :wc_state=wc_state />
                  </v-col>
                  <v-col cols=9 md=9 lg=9>
                    <LocationsColumn :locations=wc_state.locations />

                    <WorkflowsColumn :wc_state="wc_state" :wfs="wfs" @view-workflows="tab = 2" />
                  </v-col>
                </v-row>
              </v-container>

            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-dialog max-width="800">
                <template v-slot:activator="{ props: activatorProps }">
                  <v-btn color="blue" dark v-bind="activatorProps">Workcell Info</v-btn>
                </template>
                <template v-slot:default="{ isActive }">
                  <v-card>
                    <v-card-title>
                      <h3>Workcell Info</h3>
                    </v-card-title>
                    <v-card-text>
                      <vue-json-pretty :data="wc_info" />
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn text="Close Dialog" @click="isActive.value = false"></v-btn>
                    </v-card-actions>
                  </v-card>
                </template>
              </v-dialog>
            </v-card-actions>
          </v-card>
        </v-container>
        <v-container v-else>
          <p>No WC info yet</p>
        </v-container>
      </v-window-item>
      <v-window-item :key="2" :value="2">
        <h2> All Workflows </h2>
        <WorkflowTable title="All Workflows" :wc_state=wc_state :wfs="wfs" />
      </v-window-item>
      <v-window-item :key="3" :value="3">
        <v-row class="pa-1 ma-1 justify-center">

          <Experiments :experiment_objects="experiment_objects" :wc_state=wc_state />

        </v-row>
      </v-window-item>
      <!-- <v-window-item :key="4" :value="4">
              <p>test3</p>
            </v-window-item>
            <v-window-item :key="5" :value="5">
              <p>test3</p>
            </v-window-item>
            <v-window-item :key="6" :value="6">
              <p>test3</p>
            </v-window-item> -->
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
const main_url = ref()
const state_url = ref()
const workcell_info_url = ref()
const has_url = ref(false)
const tab = ref(1)
const wfs = ref([''])
const experiments = ref()
const experiments_url = ref()
const backend_server = ref()
const workcell_urls = ref()
const wc_state = ref()
const wc_info = ref()
const experiment_keys = ref()
const experiment_objects: any = ref([])
main_url.value = "http://".concat(window.location.host) //.concat("/server")
class Experimentval {
  experiment_id?: string;
  experiment_workflows: any;
  experiment_name?: string;
  num_wfs?: any;
  num_events? : any;
  events?: any



}
async function get_events(experiment_id: string) {
  var test = await ((await fetch(main_url.value.concat("/experiments/".concat(experiment_id).concat("/log"))))).json() ;
  console.log(test)
  return test

}
watchEffect(async () => {
  //workcell_urls.value = await (await fetch(backend_server.value)).json();
  //main_url.value = workcell_urls.value[0]

  has_url.value = true;
  state_url.value = main_url.value.concat("/wc/state")

  experiments_url.value = main_url.value.concat("/experiments/all")
  workcell_info_url.value = main_url.value.concat("/wc/")



  watchEffect(async () => wc_state.value = await (await fetch(state_url.value)).json())
  watchEffect(async () => wc_info.value = await (await fetch(workcell_info_url.value)).json())


  //wc_state.value = { modules: { "test": { state: "test" } } }
  var old_len: any = 0;
  var i = 0;
  setInterval(async () => {
    if(experiment_keys.value) {
      old_len =  experiment_keys.value.length

    }  else {
      old_len = 0;
    }
    wc_state.value = await (await fetch(state_url.value)).json()
    wfs.value = Object.keys(wc_state.value.workflows).sort().reverse()
    experiments.value = await ((await fetch(experiments_url.value)).json())
    experiment_keys.value = Object.keys(experiments.value).sort()
    i = 0;
    experiment_keys.value.forEach(async function (value: any) {
    i = i+1
    if (i > old_len) {
    var experiment: Experimentval = new Experimentval();
    experiment.experiment_id = value;
    var events = await get_events(value)

    experiment.experiment_name = experiments.value[value].experiment_name;
    experiment.experiment_workflows = wfs.value.filter((key: any) => wc_state.value.workflows[key].experiment_id === value);
    experiment.events = events;
    experiment.num_wfs = experiment.experiment_workflows.length;
    experiment.num_events = experiment.events.length;
    experiment_objects.value.splice(0, 0, experiment)
    }

});



  }, 500)
}
)

</script>

<script lang="ts">
export default {
  data: () => ({ drawer: false }),
}
</script>

<style>
.module_indicator {
  color: white;
    border-radius: 5px;
    padding: 3px;
  }

  .IDLE {
    background-color: green;
  }

  .BUSY {
    background-color: blue;
  }

  .ERROR {
    background-color: red;
  }

  .UNKNOWN {
    background-color: darkgrey;
  }


  .INIT {
    background-color: purple;
  }


  .wf_indicator {
    width: 10px;
    height: 10px;
    border-radius: 5px;
    margin-left: 10px;
  }

  .queued {
    background-color: yellow;
  }

  .new {
    background-color: yellow;
  }

  .running {
    background-color: blue;
  }

  .completed {
    background-color: green;
  }

  .failed {  background-color: red;
}
</style>
