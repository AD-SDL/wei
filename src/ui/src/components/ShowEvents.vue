<template>
    <div>
        <h3 class="title">Recent Events:</h3>
        <v-expansion-panels>
            <v-expansion-panel>
                <v-expansion-panel-title>
                    <h4>event table</h4>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                    <EventTable :items="filteredEvents" :maxEntries="25"/>
                </v-expansion-panel-text>
            </v-expansion-panel>
            <v-expansion-panel>
                <v-expansion-panel-title>
                    <h4>event list</h4>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                    <v-list dense>
                        <v-list-item v-for="event in filteredEvents.slice(0, 10)" :key="event.event_id">
                            <v-list-item-content>
                              <v-list-item-title>{{ event.event_name.toLowerCase() }}</v-list-item-title>
                              <v-list-item-subtitle>Type: {{ event.event_type.toLowerCase() }}</v-list-item-subtitle>
                            </v-list-item-content>
                        </v-list-item>
                    </v-list>
                </v-expansion-panel-text>
            </v-expansion-panel>
        </v-expansion-panels>
    </div>
</template>

<script setup lang="ts">
import {
  computed,
  PropType,
  ref,
} from 'vue';

/// <reference path="../store.d.ts" />
import { events } from '@/store';

import EventTable from './EventTable.vue';

const props = defineProps({
  filteredEvents: {
    type: Array as PropType<Array<any>>,
    required: true,
  },
});
</script>