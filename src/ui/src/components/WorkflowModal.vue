<template>
  <v-dialog class="pa-3" v-slot:default="{ isActive }">
    <v-card>
      <v-card-title>
        <div class="d-flex align-center w-100">
          <h2 class="title py-3 my-3">Workflow: {{ modal_title }}</h2>
          <PauseResumeButton
            :wf_run_id="modal_text.run_id"
            :wf_status="modal_text.status"
            class="ml-2">
          </PauseResumeButton>
          <CancelButton
            :wf_run_id="modal_text.run_id"
            :wf_status="modal_text.status"
            :can_Cancel="canCancel"
            class="ml-2">
          </CancelButton>
          <ResetButton
            :wf_run_id="modal_text.run_id"
            :wf_status="modal_text.status"
            :can_Pause="canPause"
            class="ml-2">
          </ResetButton>
        </div>
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
  watchEffect,
} from 'vue';

import {
  events,
  workcell_state,
} from '@/store';

import CancelButton from './AdminButtons/CancelButton.vue';
import PauseResumeButton from './AdminButtons/PauseResumeButton.vue';
import ResetButton from './AdminButtons/ResetButton.vue';
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

const stepIndex = computed(() => props.modal_text?.step_index ?? -1);

const currentStep = computed(() => props.modal_text?.steps?.[stepIndex.value] ?? null);

const moduleName = computed(() => currentStep.value?.module);

const currentModule = computed(() => {
  const modules = workcell_state.value?.modules;
  if (!modules || !moduleName.value) return null;
  
  return Object.values(modules).find((module: any) => module.name === moduleName.value) || null;
});

const canCancel = computed(() => {
  const module = currentModule.value as { about?: { admin_commands?: string[] } };
  return module?.about?.admin_commands?.includes("cancel") ?? false;
});

const canPause = computed(() => {
  const module = currentModule.value as { about?: { admin_commands?: string[] } };
  return module?.about?.admin_commands?.includes("pause") ?? false;
});

// watchEffect(() => {
//   console.log('Step Index:', stepIndex.value);
//   console.log('Current Step:', currentStep.value);
//   console.log('Module Name:', moduleName.value);
//   console.log('Current Module:', currentModule.value);
//   console.log("Can Cancel:", canCancel.value);
// });
</script>
