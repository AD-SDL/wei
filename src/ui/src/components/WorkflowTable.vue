<template>
  <v-container>
    <WorkflowModal :modal_title="modal_title" :modal_text="modal_text" v-model="modal" />
    <!-- eslint-disable vue/no-parsing-error-->
    <v-data-table :headers="arg_headers" hover
      :items="Object.values(wc_state.workflows).filter((key: any) => (wfs).includes(key.run_id))"
      no-data-text="No Workflows" density="compact" :sort-by="sortBy" :hide-default-footer="wfs.length <= 10">
      <template v-slot:item="{ item }: { item: any }">
        <tr @click="set_modal(wc_state.workflows[item.run_id].name, wc_state.workflows[item.run_id])">
          <td>{{ item.name }}</td>
          <td><v-sheet class="pa-2 rounded-lg text-md-center text-white" :class="'wf_status_' + item.status"> {{
      item.status }}
            </v-sheet>
          </td>
          <td>{{ item.start_time }}</td>
          <td>Step {{ item.step_index }}: {{ item.steps[item.step_index].name }}</td>
          <td>{{ item.end_time }}</td>
        </tr>
      </template>
    </v-data-table>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { VDataTable } from 'vuetify/components';

const props = defineProps(['wfs', 'wc_state', 'title'])
const modal = ref(false)
const modal_text = ref()
const modal_title = ref()
const sortBy: VDataTable['sortBy'] = [{ key: 'start_time', order: 'desc' }];
const arg_headers = [
  { title: 'Name', key: 'name' },
  { title: 'Status', key: 'status' },
  { title: 'Start Time', key: 'start_time' },
  { title: 'Latest Step', key: 'latest_step' },
  { title: 'End Time', key: 'end_time' }
]
const set_modal = (title: string, value: Object) => {
  modal_title.value = title
  modal_text.value = value
  modal.value = true
}
</script>

<style>
.status_button {
  border-radius: 5px;
  color: white;
    padding: 2px;
  }
</style>
