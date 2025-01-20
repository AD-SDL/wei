<template>
    <div>
        <v-tooltip location="bottom">
            <template v-slot:activator="{ props }">
                <div v-bind="props">
                    <v-btn
                        @click="sendCancelCommand"
                        color="deep-orange darken-1"
                        dark
                        elevation="5"
                        :disabled="!canCancel">
                        <v-icon>mdi-cancel</v-icon>
                    </v-btn>
                </div>
            </template>
            <span>
                {{ canCancel ? hoverText : hoverText + " (unavailable)" }}
            </span>
        </v-tooltip>
    </div>

</template>

<script setup lang="ts">
import {
  ref,
  watchEffect,
} from 'vue';

import { main_url } from '@/store';

const props = defineProps<{
    module?: string;
    module_status?: string;
    wf_run_id?: string;
    wf_status?: string;
}>();

const cancel_url = ref('')
const canCancel = ref(false);
const hoverText = ref('')

// Format cancel url
watchEffect(() => {
    if (props.module) {
        cancel_url.value = main_url.value.concat('/admin/cancel/'.concat(props.module))
        hoverText.value = "Cancel Module Action"
        console.log(cancel_url.value)
    }
    else if (props.wf_run_id) {
        cancel_url.value = main_url.value.concat('/admin/cancel_wf/'.concat(props.wf_run_id))
        hoverText.value = "Cancel Workflow"
        console.log(cancel_url.value)
    }
    else {
        cancel_url.value = main_url.value.concat('/admin/cancel')
        hoverText.value = "Cancel Workcell"
        console.log(cancel_url.value)
    }
})

watchEffect(() => {
    // Determine if the module is cancelable (if actively running something)
    if (props.module) {
        if (props.module_status == 'BUSY' || props.module_status == 'PAUSED') {
            canCancel.value = true
        }
        else {
            canCancel.value = false
        }
    }
    else if (props.wf_run_id) {
        if (props.wf_status == "running" || (props.wf_status == "queued" || props.wf_status == "in_progress")) {
            canCancel.value = true
        }
        else {
            canCancel.value = false
        }
    }
    else {
        // TODO: Allow cancel if there's an actively running workflow
        canCancel.value = true
    }
})

// Function to send cancel command
const sendCancelCommand = async () => {
    try {
        const response = await fetch(cancel_url.value, {
            method: "POST",
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        console.log('Cancel successful');
    } catch (error) {
        console.error('Error in cancel:', error);
    }
};
</script>
