
<template>

  <v-data-table
    v-model:expanded="expanded"
    :headers="arg_headers"
    :items="experiment_objects"
    item-value="experiment_id"
    show-expand
    :sort-by="sortBy"
  >
    <template v-slot:top>
      <v-toolbar flat>
        <v-toolbar-title>Experiments </v-toolbar-title>
      </v-toolbar>
    </template>
    <template v-slot:expanded-row="{ columns, item}: {columns: any, item: any}">
      <tr>
        <td :colspan="columns.length">
          <v-expansion-panels v-if="item.events.length > 0">
              <v-expansion-panel v-for="event in item.events" :key="event.event_id">
                <v-expansion-panel-title>
                  {{ event.event_type }} {{ event.event_name }}
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <Event :event="event" :wc_state="wc_state" />
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
            <p v-else class="text-caption">No events</p>
        </td>
      </tr>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">


import { ref } from 'vue';
import { VDataTable } from 'vuetify/lib/components/index.mjs';
const props = defineProps(["experiment_objects", "wc_state"])
const my_wfs = ref()
const panel = ref()
const sortBy: VDataTable['sortBy'] = [{ key: 'experiment_id', order:'desc'}];

//const item: any = ref()
const arg_headers = [
  { title: 'Name', key: 'experiment_name' },
  { title: 'ID', key: 'experiment_id' },
  { title: 'num_wfs', key: 'num_wfs' },
  { title: 'num_events', key: 'num_events' },
  { title: '', key: 'data-table-expand' },
 
]
const expanded =  ref([])

</script>
