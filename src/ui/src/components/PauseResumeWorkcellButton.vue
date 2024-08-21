<template>
    <div>
      <v-btn 
            @click="togglePauseResume" 
            :color="isPaused ? 'green darken-3' : 'red darken-3'" 
            dark 
            elevation="5">
            <v-icon>
                {{ isPaused ? 'mdi-play' : 'mdi-pause' }}
            </v-icon>
        </v-btn>
</div>
  </template>
  
  <script lang="ts" setup>
    // TODO: Currently this changes all modules to BUSY regardless of starting state on resume. 

    import {defineProps, ref, watchEffect} from 'vue';

    const props = defineProps(['main_url'])

    const pause_url = ref()
    const resume_url = ref()
    const isPaused = ref(false);

    // Format pause and resume urls
    pause_url.value = props.main_url.concat('/admin/pause')
    resume_url.value = props.main_url.concat('/admin/resume')

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
            console.log('Workcell Paused');

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

            console.log('Workcell Resumed');

        } catch (error) {
        console.error('Error resuming module:', error);
        }
    };
</script>
    
<style scoped>
    button {
        padding: 10px 20px;
        font-size: 16px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    
    button:hover {
        background-color: #0056b3;
    }
</style>