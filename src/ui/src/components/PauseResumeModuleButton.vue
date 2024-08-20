<template>
    <div>
      <v-tooltip location="bottom">
        <template v-slot:activator="{ props }">
            <div v-bind="props">
            <v-btn 
                @click="togglePauseResume" 
                :color="isPaused ? 'green darken-3' : 'red darken-3'" 
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
            {{ allowButton ? (isPaused ? 'Resume module' : 'Pause module') 
                       : (isPaused ? 'Resume module (unavailable)' : 'Pause module (unavailable)') }}
        </span>
      </v-tooltip>
    </div>
  </template>

<script lang="ts" setup>
    import {defineProps, ref, watchEffect} from 'vue';

    const props = defineProps(['main_url', 'module', 'module_status'])
    
    const pause_url = ref()
    const resume_url = ref()
    const isPaused = ref(false);
    const allowButton = ref(false)

    // Format pause and resume urls
    pause_url.value = props.main_url.concat('/admin/pause/'.concat(props.module))
    resume_url.value = props.main_url.concat('/admin/resume/'.concat(props.module))

    watchEffect(() => {
        // Determine if pause/resume button should appear
        if (props.module_status == "BUSY" || props.module_status == "PAUSED") {
            allowButton.value = true
        } else {
            allowButton.value = false
        }

        // Determine if the module is already paused 
        if (props.module_status == 'PAUSED') {
            isPaused.value = true
        } else {
            isPaused.value = false
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
            console.log('Module Paused');

        } catch (error) {
            console.error('Error pausing module:', error);
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

            console.log('Module Resumed');

        } catch (error) {
        console.error('Error resuming module:', error);
        }
    };
</script>
  
<style scoped>
    button {
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
    }
</style>