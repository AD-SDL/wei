<template>
  <v-container>
    <v-tabs v-model="tab" align-tabs="center" color="deep-purple-accent-4">
      <v-tab :value="1">
        Workcells
      </v-tab>
      <v-tab :value="2">
        Workflows
      </v-tab>
      <v-tab :value="3">
        Experiments
      </v-tab>
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
                <div class="d-flex justify-center">
                  <PauseResumeButton :main_url="main_url" class="ml-2"/>
                  <CancelButton :main_url="main_url" class="ml-2" />
                  <ResetButton :main_url="main_url" class="ml-2" />
                  <LockUnlockButton :main_url="main_url" class="ml-2"/>
                  <ShutdownButton :main_url="main_url" class="ml-2" />
                  <SafetyStopButton :main_url="main_url" class="ml-2"/>
                </div>
              </v-card-title>
            <v-card-text>
              <v-container class="pa-1">
                <v-row dense wrap justify-content="space-evenly">
                  <v-col cols="3" md="3" lg="3">
                    <ModulesPanel :modules="wc_state.modules" :main_url="main_url" :wc_state="wc_state" />
                  </v-col>
                  <v-col cols="9" md="9" lg="9">
                    <LocationsPanel :locations="wc_state.locations" />

                    <WorkflowsPanel :wc_state="wc_state" :wfs="wfs" @view-workflows="tab = 2" />
                  </v-col>
                </v-row>
              </v-container>
            </v-card-text>

            <v-card-actions>
              <v-spacer />
              <v-dialog max-width="800">
                <template #activator="{ props: activatorProps }">
                  <v-btn color="blue" dark v-bind="activatorProps">
                    Workcell Info
                  </v-btn>
                </template>
                <template #default="{ isActive }">
                  <v-card>
                    <v-card-title>
                      <h3>Workcell Info</h3>
                    </v-card-title>
                    <v-card-text>
                      <vue-json-pretty :data="wc_info" />
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer />
                      <v-btn text="Close Dialog" @click="isActive.value = false" />
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
        <WorkflowTable title="All Workflows" :wc_state="wc_state" :wfs="wfs" />
      </v-window-item>
      <v-window-item :key="3" :value="3">
        <v-row class="pa-1 ma-1 justify-center">
          <Experiments :experiment_objects="experiment_objects" :wc_state="wc_state" />
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
import CancelButton from './AdminButtons/CancelButton.vue';
import LockUnlockButton from './AdminButtons/LockUnlockButton.vue';
import PauseResumeButton from './AdminButtons/PauseResumeButton.vue';
import ResetButton from './AdminButtons/ResetButton.vue';
import SafetyStopButton from './AdminButtons/SafetyStopButton.vue';
import ShutdownButton from './AdminButtons/ShutdownButton.vue';
const main_url = ref()
const state_url = ref()
const workcell_info_url = ref()
const has_url = ref(false)
const tab = ref(1)
const wfs = ref([''])
const experiments = ref()
const experiments_url = ref()
const wc_state = ref()
const wc_info = ref()
const experiment_keys = ref()
const experiment_objects: any = ref([])
main_url.value = "http://".concat(window.location.host) //.concat("/server")
class ExperimentInfo {
  experiment_id?: string;
  experiment_workflows: any;
  experiment_name?: string;
  num_wfs?: any;
  num_events?: any;
  events?: any
}
async function get_events(experiment_id: string) {
  return Object.values(await ((await fetch(main_url.value.concat("/experiments/".concat(experiment_id).concat("/events"))))).json());
}
watchEffect(async () => {
  has_url.value = true;
  state_url.value = main_url.value.concat("/wc/state")

  experiments_url.value = main_url.value.concat("/experiments/all")
  workcell_info_url.value = main_url.value.concat("/wc/")

  watchEffect(async () => wc_state.value = await (await fetch(state_url.value)).json())
  watchEffect(async () => wc_info.value = await (await fetch(workcell_info_url.value)).json())

  var new_experiment_keys = [];
  experiment_keys.value = [];
  setInterval(updateDashboard, 1000)

  async function updateDashboard() {
    wc_state.value = await (await fetch(state_url.value)).json();
    wfs.value = Object.keys(wc_state.value.workflows).sort().reverse();
    experiments.value = await ((await fetch(experiments_url.value)).json());
    new_experiment_keys = Object.keys(experiments.value).sort();
    let difference = new_experiment_keys.filter(x => !experiment_keys.value.includes(x));
    difference.forEach(async function (value: any) {
      var experiment: ExperimentInfo = new ExperimentInfo();
      experiment.experiment_id = value;
      var events = await get_events(value);

      experiment.experiment_name = experiments.value[value].experiment_name;
      experiment.experiment_workflows = wfs.value.filter((key: any) => wc_state.value.workflows[key].experiment_id === value);
      experiment.events = events;
      experiment.num_wfs = experiment.experiment_workflows.length;
      experiment.num_events = experiment.events.length;
      experiment_objects.value.splice(0, 0, experiment);
    });
    experiment_keys.value = Object.keys(experiments.value).sort();
  }
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

.wf_status_completed,
.module_status_IDLE,
.module_status_READY {
  background-color: green;
}

.wf_status_running,
.module_status_BUSY {
  background-color: blue;
}

.wf_status_failed,
.module_status_ERROR {
  background-color: red;
}

.wf_status_unknown,
.module_status_UNKNOWN {
  background-color: darkslategray;
}

.wf_status_new,
.module_status_INIT {
  background-color: aquamarine;
  color: black;
}

.wf_status_queued,
.wf_status_paused,
.wf_status_in_progress,
.module_status_PAUSED {
  background-color: gold;
  color: black;
}

.wf_status_in_progress {
  background-color: darkblue;
  color: black;
}

.module_status_LOCKED {
  background-color: darkgoldenrod;
  color: white;
}

.wf_status_cancelled,
.module_status_CANCELLED {
  background-color: darkorange;
  color: black;
}

.wf_indicator {
  width: 10px;
  height: 10px;
  border-radius: 5px;
  margin-left: 10px;
}
</style>
