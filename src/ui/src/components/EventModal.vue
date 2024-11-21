<template>
    <v-dialog :model-value="modalValue" @update:model-value="updateModalValue">
        <v-card>
            <v-card-title>
                <h2 class="title">Event: {{ modal_event?.event_name || 'N/A' }}</h2>
                <!-- {{modal_event.event_id}} -->
            </v-card-title>
            <v-card-text>
                <v-sheet class="pa-2 rounded-lg text-md-center text-white"
                :class="'event_name_' + (modal_event?.event_name || '').toLowerCase()">
                {{ modal_event?.event_id || 'N/A' }}
            </v-sheet>
            <test :event="modal_event" />
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click="closeDialog" class="primary--text">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import test from './test.vue';

const props = defineProps({
    modal_event: {
        type: Object,
        required: true,
    },
    modalValue: {
        type: Boolean,
        required: true,
    },
});

const emit = defineEmits(['update:modalValue']);

const closeDialog = () => {
    emit('update:modalValue', false);
};

const updateModalValue = (value: Boolean) => {
    emit('update:modalValue', value);
};

</script>