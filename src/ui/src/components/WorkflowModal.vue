<template>
  <v-dialog class="pa-3" v-slot:default="{ isActive }" max-width="1000">
    <v-card>
      <v-card-title>
        <h2 class="title">Workflow: {{ modal_title }}</h2>
        {{modal_text.run_id}}
        <v-sheet class="pa-2 rounded-lg text-md-center text-white" :class="'wf_status_' + modal_text.status">{{ modal_text.status }}</v-sheet>
      </v-card-title>
      <v-card-text>
        <h3>Details</h3>
        <vue-json-pretty :data="modal_text" :deep="1"></vue-json-pretty>
        <Workflow :steps="modal_text.steps" />
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
const props = defineProps(['modal_title', 'modal_text'])
const flowdef = ref(false)
</script>
