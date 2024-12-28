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
            <div>
              <h3 class="title">Workflows:</h3>
              <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <h4>workflow table</h4>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <WorkflowTable :workflows="experimentWorkflows" :workcell_state="workcell_state"/>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <h4>workflow list</h4>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                        <v-list dense>
                          <v-list-item v-for="workflow in experimentWorkflows" :key="workflow.run_id">
                            <v-list-item-content>
                              <v-list-item-title>{{ workflow.name }}</v-list-item-title>
                              <v-list-item-subtitle>Status: {{ workflow.status }}</v-list-item-subtitle>
                            </v-list-item-content>
                          </v-list-item>
                        </v-list>
                      </v-expansion-panel-text>
                  </v-expansion-panel>
              </v-expansion-panels>
            </div>
            <div>
              <h3>Details:</h3>
              <vue-json-pretty v-if="selectedExperiment" :data="selectedExperiment" :deep="1"></vue-json-pretty>
            </div>
            <!-- <div>
              <h3 class="title">Details:</h3>
              <v-list>
                <v-list-item>
                  <v-list-item-title>Name:</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedExperiment.experiment_name }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>ID:</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedExperiment.experiment_id }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Campaign:</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ selectedExperiment.campaign_id ? campaigns[selectedExperiment.campaign_id]?.campaign_name : '-' }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Description:</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedExperiment.experiment_description || '-' }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Last Check-in:</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedExperiment.check_in_timestamp || '-' }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Email Addresses:</v-list-item-title>
                  <v-list-item-subtitle>{{ selectedExperiment.email_addresses.join(', ') || '-' }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div> -->
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
  experiment_objects,
  workcell_state,
} from '@/store';

import WorkflowTable from './WorkflowTable.vue';

const sortBy: VDataTable['sortBy'] = [{ key: 'experiment_id', order: 'desc' }];

const arg_headers = [
  { title: 'Name', key: 'experiment_name' },
  { title: 'ID', key: 'experiment_id' },
  { title: 'Campaign', key: 'campaign_id' },
  { title: 'Last Check-in', key: 'check_in_timestamp' }
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

watch(experiment_objects, (newVal: any, oldVal: any) => {
  console.log('Experiment Data Test:', newVal);
});
</script>
