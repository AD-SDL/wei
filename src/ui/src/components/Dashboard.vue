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
        <v-container v-if="workcell_state">
          <v-card class="pa-1">
              <v-card-title class="text-center">
                <h2>{{ workcell_info.name }}</h2>
                <div class="d-flex justify-center">
                  <PauseResumeButton :main_url="main_url" :wc_state=workcell_state class="ml-2"/>
                  <CancelButton :main_url="main_url" :wc_state=workcell_state class="ml-2" />
                  <ResetButton :main_url="main_url" :wc_state=workcell_state class="ml-2" />
                  <LockUnlockButton :main_url="main_url" :wc_state=workcell_state class="ml-2"/>
                  <ShutdownButton :main_url="main_url" :wc_state=workcell_state class="ml-2" />
                  <SafetyStopButton :main_url="main_url" :wc_state=workcell_state class="ml-2"/>
                </div>
              </v-card-title>
            <v-card-text>
              <v-container class="pa-1">
                <v-row dense wrap justify-content="space-evenly">
                  <v-col cols="3" md="3" lg="3">
                    <ModulesPanel :modules="workcell_state.modules" :main_url="main_url" :wc_state="workcell_state" />
                  </v-col>
                  <v-col cols="9" md="9" lg="9">
                    <LocationsPanel :locations="workcell_state.locations" />

                    <WorkflowsPanel :wc_state="workcell_state" :wfs="workflows" @view-workflows="tab = 2" />
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
                      <vue-json-pretty :data="workcell_info" :deep="2" />
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
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
        </v-container>
      </v-window-item>
      <v-window-item :key="2" :value="2">
        <h2> All Workflows </h2>
        <WorkflowTable title="All Workflows" :wc_state="workcell_state" :wfs="workflows" />
      </v-window-item>
      <v-window-item :key="3" :value="3">
        <v-row class="pa-1 ma-1 justify-center">
          <Experiments/>
        </v-row>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
/// <reference path="../store.d.ts" />
import { main_url, workcell_info, workcell_state, workflows } from "@/store";
import { ref } from 'vue';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import CancelButton from './AdminButtons/CancelButton.vue';
import LockUnlockButton from './AdminButtons/LockUnlockButton.vue';
import PauseResumeButton from './AdminButtons/PauseResumeButton.vue';
import ResetButton from './AdminButtons/ResetButton.vue';
import SafetyStopButton from './AdminButtons/SafetyStopButton.vue';
import ShutdownButton from './AdminButtons/ShutdownButton.vue';
const tab = ref(1)
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
  background-color: darkslategray;
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
