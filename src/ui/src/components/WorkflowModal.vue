<template>
  <v-dialog v-slot:default="{ isActive }" max-width="800">
    <v-btn slot="activator" primary dark></v-btn>
    <v-card>
      <v-card-text>
        <h2 class="title">{{ modal_title }}</h2>
        <v-list>
          <v-list-item><b>Run ID:</b> {{ modal_text.run_id }}<br></v-list-item>
          <v-list-item v-if="modal_text.start_time">
            <b>Start Time</b> {{ modal_text.start_time }}
          </v-list-item>
          <v-list-item v-if="modal_text.end_time">
            <b>End Time</b> {{ modal_text.end_time }}
          </v-list-item>
          <v-list-item v-if="modal_text.duration">
            <b>Duration</b> {{ modal_text.duration }}
          </v-list-item>
        </v-list>
        <div>
          <v-switch label="Toggle Payload Values" v-model="flowdef"></v-switch>
          <div v-if="flowdef">
            <Workflow :steps="modal_text.flowdef" />
          </div>
          <div v-else>
            <Workflow :steps="modal_text.steps" />
          </div>
        </div>
      </v-card-text>
      <v-card-row actions>
        <v-spacer></v-spacer>
        <v-btn flat @click="isActive.value = false" class="primary--text">close</v-btn>
      </v-card-row>
    </v-card>
  </v-dialog>
</template>


<script setup lang="ts">
import { ref } from 'vue';
const props = defineProps(['modal_title', 'modal_text'])
const flowdef = ref(false)

</script>
