<template>
    <v-card class="pa-1 ma-1" title="Recent Events">
        <v-card-text v-if="evnts">
            <EventTable :maxEntries="5"/>
        </v-card-text>
        <v-card-text v-else>
            <p>No Events Yet</p>
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn class="ma-1" @click="$emit('viewEvents')" color="blue">View All Events</v-btn>
        </v-card-actions>
    </v-card>
</template>

<script setup lang="ts">
const props = defineProps(['evnts'])
const emits = defineEmits(['viewEvents'])
</script>