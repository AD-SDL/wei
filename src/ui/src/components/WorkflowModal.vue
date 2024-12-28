<template>
  <v-dialog class="pa-3" v-slot:default="{ isActive }">
    <v-card>
      <v-card-title>
        <h2 class="title">Workflow: {{ modal_title }}</h2>
        {{modal_text.run_id}}
        <v-sheet class="pa-2 rounded-lg text-md-center text-white" :class="'wf_status_' + modal_text.status">{{ modal_text.status }}</v-sheet>
      </v-card-title>
      <v-card-text>
        <ShowEvents :filteredEvents="workflowEvents"/>
        <Workflow :steps="modal_text.steps" :wf="modal_text" />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn flat @click="isActive.value = false" class="primary--text">close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import {
  computed,
  ref,
} from 'vue';

import { events } from '@/store';

import ShowEvents from './ShowEvents.vue';

const props = defineProps(['modal_title', 'modal_text'])
const flowdef = ref(false)

const workflowEvents = computed(() => {
  return events.value.filter((event: any) => {
    const eventType = event.event_type
      ? event.event_type === "WORKFLOW"
      : true;
    const matchWorkflow = props.modal_text?.run_id
      ? event.run_id === props.modal_text?.run_id
      : true;
    return eventType && matchWorkflow;
  });
});
</script>
