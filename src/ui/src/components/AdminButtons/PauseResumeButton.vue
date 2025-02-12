<template>
    <div>
      <v-tooltip location="bottom">
        <template v-slot:activator="{ props }">
            <div v-bind="props">
            <v-btn
                @click="togglePauseResume"
                :color="isPaused ? 'green-darken-3' : 'orange-darken-1'"
                dark
                elevation="5"
                :disabled="!allowButton" >
                <v-icon>
                    {{ isPaused ? 'mdi-play' : 'mdi-pause' }}
                </v-icon>
            </v-btn>
            </div>
        </template>
         <span>
            {{ allowButton ? (isPaused ? 'Resume ' + hoverText : 'Pause ' + hoverText)
                       : (isPaused ? 'Resume ' + hoverText + ' (unavailable)' : 'Pause ' + hoverText + ' (unavailable)') }}
        </span>
      </v-tooltip>
    </div>
  </template>

<script lang="ts" setup>
import {
  ref,
  watchEffect,
} from 'vue';

import {
  main_url,
  workcell_state,
} from '@/store';

const props = defineProps<{
    module?: string;
    module_status?: any;
    wf_run_id?: string;
    wf_status?: string;
}>();

const pause_url = ref('')
const resume_url = ref('')
const isPaused = ref(false);
const allowButton = ref(false)
const hoverText = ref('')

// Format pause and resume urls
watchEffect(() => {
    if (props.module) {
        pause_url.value = main_url.value.concat('/admin/pause/'.concat(props.module))
        resume_url.value = main_url.value.concat('/admin/resume/'.concat(props.module))
        hoverText.value = "Module"
    }
    else if (props.wf_run_id) {
        pause_url.value = main_url.value.concat('/admin/pause_wf/'.concat(props.wf_run_id))
        resume_url.value = main_url.value.concat('/admin/resume_wf/'.concat(props.wf_run_id))
        hoverText.value = "Workflow"
    }
    else {
        pause_url.value = main_url.value.concat('/admin/pause')
        resume_url.value = main_url.value.concat('/admin/resume')
        hoverText.value = "Workcell"
    }
})

watchEffect(() => {
    if (props.module) {
        // Determine if pressing pause/resume button should be allowed
        if (props.module_status["BUSY"] == true || props.module_status["PAUSED"] == true) {
            allowButton.value = true
        } else {
            allowButton.value = false
        }

        // Determine if the module is already paused
        if (props.module_status["PAUSED"] == true) {
            isPaused.value = true
        } else {
            isPaused.value = false
        }
    }
    else if (props.wf_run_id) {
        if (props.wf_status == "running" || props.wf_status == "in_progress" || props.wf_status == "paused") {
            allowButton.value = true
        } else {
            allowButton.value = false
        }
                
        if (props.wf_status == "paused") {
            isPaused.value = true
        } else {
            isPaused.value = false
        }
    }
    else {
        if (workcell_state.value) {
            isPaused.value = workcell_state.value.paused
        } else {
            isPaused.value = false
        }
        allowButton.value = true
    }
})

// Function to toggle pause/resume
const togglePauseResume = async () => {
    if (isPaused.value) {
        await sendResumeCommand();
    } else {
        await sendPauseCommand();
    }
    isPaused.value = !isPaused.value;
};

// Function to send pause command
const sendPauseCommand = async () => {
    try {
        const response = await fetch(pause_url.value, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        console.log('Paused');

    } catch (error) {
        console.error('Error pausing:', error);
    }
};

// Function to send resume command
const sendResumeCommand = async () => {
    try {
        const response = await fetch(resume_url.value, {
            method: 'POST',
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        console.log('Resumed');

    } catch (error) {
        console.error('Error resuming:', error);
    }
};
</script>
