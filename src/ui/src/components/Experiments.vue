<template>
  <v-card>
    <v-card-title class="text-center">
      <h2>Experiments</h2>
    </v-card-title>
    <v-card-text>
      <v-data-table :headers="arg_headers" :items="experiment_objects" item-value="experiment_id" :sort-by="sortBy"
        @click:row="openExperimentDetails" density="compact">
        <template v-slot:item.campaign_id="{ value }">
          <td>{{ (value != null && campaigns !== undefined && value in campaigns) ? campaigns[value].campaign_name : "-"
            }}</td>
        </template>
      </v-data-table>
      <v-dialog v-model="dialogVisible">
        <v-card v-if="selectedExperiment">
          <v-card-title>
            <div>
              <h2 class="title">Experiment: {{ selectedExperiment.experiment_name }}</h2>
            </div>
            {{ selectedExperiment.experiment_id }}
          </v-card-title>
          <v-card-text>
              <h3 class="title">Recent Events:</h3>
                <EventTable :items="experimentEvents" :maxEntries="5"/>
              <h3>Details:</h3>
              <vue-json-pretty v-if="selectedExperiment" :data="selectedExperiment" :deep="1"></vue-json-pretty>
            <div>
              <h3>Workflows:</h3>
              <v-data-table :headers="workflowHeaders" :items="experimentWorkflows" density="compact">
                <template v-slot:item.status="{ value }">
                  <td>{{ value }}</td>
                </template>
              </v-data-table>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="blue-darken-1" variant="text" @click="dialogVisible = false">Close</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import {
  computed,
  ref,
  watch,
} from 'vue';

import VueJsonPretty from 'vue-json-pretty';
import { VDataTable } from 'vuetify/lib/components/index.mjs';

/// <reference path="../store.d.ts" />
import {
  campaigns,
  events,
  experiment_objects,
  workcell_state,
} from '@/store';

import EventTable from './EventTable.vue';

const sortBy: VDataTable['sortBy'] = [{ key: 'experiment_id', order: 'desc' }];

const arg_headers = [
  { title: 'Name', key: 'experiment_name' },
  { title: 'ID', key: 'experiment_id' },
  { title: 'Campaign', key: 'campaign_id' },
  { title: 'Last Check-in', key: 'check_in_timestamp' }
];

const workflowHeaders = [
{ title: 'Workflow Name', key: 'name' },
  { title: 'Workflow ID', key: 'run_id' },
  { title: 'Status', key: 'status' },
  { title: 'Start Time', key: 'start_time' },
  { title: 'End Time', key: 'end_time' }
];

const dialogVisible = ref(false);
const selectedExperiment = ref<any>(null);

const openExperimentDetails = (event: Event, { item }: { item: any }) => {
  selectedExperiment.value = item;
  dialogVisible.value = true;
};

const experimentWorkflows = computed<any[]>(() => {
  return Object.values(workcell_state.value?.workflows || {}).filter((workflow: any) => {
    return workflow.experiment_id === selectedExperiment.value?.experiment_id;
  });
});

const experimentEvents = computed(() => {
  return events.value.filter((event: any) => {
    const matchExperiment = selectedExperiment.value?.experiment_id
      ? event.experiment_id === selectedExperiment.value?.experiment_id
      : true;
    return matchExperiment;
  });
});

watch(experiment_objects, (newVal: any, oldVal: any) => {
  console.log('Experiment Data Test:', newVal);
});
</script>
