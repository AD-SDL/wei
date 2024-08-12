<template>
    <div>
    
        <!-- <p>PAUSE URL: {{ pause_url }}</p>
        <p v-if="module">MODULE: {{ module }}</p>
        <p v-else>No module provided</p> -->
        <!-- <p v-if="module">Module: {{ module }}</p> -->


        <!-- <p>Pause URL: {{ pause_url}}</p> -->
      <v-btn @click="togglePauseResume" 
      :color="isPaused ? 'green darken-3' : 'red darken-3'" 
      dark 
      elevation="5" >
        {{ isPaused ? 'RESUME MODULE' : 'PAUSE MODULE' }}
      </v-btn>
    </div>
  </template>
  
<script lang="ts" setup>
    import {defineProps, defineComponent, ref, computed} from 'vue';

    const props = defineProps(['main_url', 'module'])
    const pause_url = ref()
    const resume_url = ref()

    // Format pause and resume urls
    pause_url.value = props.main_url.concat('/admin/pause/'.concat(props.module))
    resume_url.value = props.main_url.concat('/admin/resume/'.concat(props.module))

    // Local reactive state TODO: Change this depending on the state of the module!!
    const isPaused = ref(false);

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