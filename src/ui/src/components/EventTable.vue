<template>
  <div>
    <div v-if="loading" class="d-flex justify-center">
      <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
    </div>
    <v-data-table v-else :headers="eventHeaders" hover
    :items="minEventsData" item-value="event_timestamp" :sort-by="sortBy" density="compact" :hide-default-footer="maxEntries <= 10">
    <template v-slot:body="{ items }">
        <tr v-for="item in items" :key="item.event_id" @click="openModal(item)">
            <td>{{ item.event_id }}</td>
            <td>
                <v-sheet class="pa-2 rounded-lg text-md-center text-white event-name-badge" :class="'event_name_' + item.event_name.toLowerCase()">
                    {{ (item.event_name).toLowerCase() }}
                </v-sheet>
            </td>
            <td>{{ (item.event_type).toLowerCase() }}</td>
            <td>{{ item.event_timestamp }}</td>
            <td>{{ item.workcell_id }}</td>
        </tr>
    </template>
    </v-data-table>
    <EventModal :modalValue="modal" @update:modalValue="modal = $event" :modal_event="modal_event" />
  </div>
</template>

<script setup lang="ts">
/// <reference path="../store.d.ts" />
import {
  computed,
  ref,
  watchEffect,
} from 'vue';

import { VDataTable } from 'vuetify/lib/components/index.mjs';

import { events } from '@/store';

import EventModal from './EventModal.vue';

const props = defineProps({
  maxEntries: {
    type: Number,
    default: Infinity
  },
  items: {
    type: Array,
    default: () => []
  }
});

const eventsData = computed(() => props.items.length ? props.items : events.value || []);
const sortBy: VDataTable['sortBy'] = [{ key: 'event_timestamp', order: 'desc'}];
const minEventsData = computed(() => {
  return eventsData.value
    .slice()
    .sort((a: { event_timestamp: string }, b: { event_timestamp: string }) => {
      return new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime();
    })
    .slice(0, props.maxEntries);
});

const loading = ref(true)

const modal = ref(false)
const modal_event = ref({})

const eventHeaders = [
  { title: 'ID', key: 'event_id' },
  { title: 'Name', key: 'event_name' },
  { title: 'Type', key: 'event_type'},
  { title: 'Timestamp', key: 'event_timestamp'},
  { title: 'Workcell ID', key: 'workcell_id'}
];

const openModal = (event: Object) => {
    modal_event.value = event;
    modal.value = true;
};

watchEffect(() => {
  if (eventsData.value.length > 0) {
    loading.value = false;
  }
});
</script>

<style scoped>
.event-name-badge {
  display: inline-block;
  width: 100%;
  text-align: center;
  min-width: 120px;
}
</style>
