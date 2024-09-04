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
    import {defineProps, ref, watchEffect} from 'vue';

    const props = defineProps<{
        main_url: string;
        module?: string; 
        module_status?: string; 
    }>();
    
    const pause_url = ref()
    const resume_url = ref()
    const isPaused = ref(false);
    const allowButton = ref(false)
    const hoverText = ref()

    // Format pause and resume urls
    if (props.module) {
        pause_url.value = props.main_url.concat('/admin/pause/'.concat(props.module))
        resume_url.value = props.main_url.concat('/admin/resume/'.concat(props.module))
        hoverText.value = "Module"
    }
    else {
        pause_url.value = props.main_url.concat('/admin/pause')
        resume_url.value = props.main_url.concat('/admin/resume')
        hoverText.value = "Workcell"  
    }

    if (props.module) {
        watchEffect(() => {
        // Determine if pressing pause/resume button should be allowed
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
    }
    else {
        allowButton.value = true 
    }

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
  
