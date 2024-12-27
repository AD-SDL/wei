<template>
    <v-dialog :model-value="modalValue" @update:model-value="updateModalValue">
        <v-card>
            <v-card-title>
                <div v-if="modal_event?.event_type === 'WORKCELL'">
                    <h2 class="title">Workcell: {{ (modal_event?.workcell.name).toLowerCase() }}</h2>
                </div>
                <div v-if="modal_event?.event_type === 'WORKFLOW'">
                        <h2 class="title">Workflow: {{ (modal_event?.workflow_name).toLowerCase() }}</h2>
                </div> 
                <div v-if="modal_event?.event_type === 'EXPERIMENT'">
                    <h2 class="title">Experiment</h2>
                </div>                                   
                    {{modal_event.event_id}}
                    <v-sheet class="pa-2 rounded-lg text-md-center text-white"
                        :class="'event_name_' + (modal_event?.event_name).toLowerCase()">
                        {{ (modal_event?.event_name).toLowerCase() }}
                    </v-sheet>
            </v-card-title>
            <v-card-text>
                <Event :event="modal_event" />
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn @click="closeDialog" class="primary--text">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import Event from './Event.vue';

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
