<template>
    <v-app>
      <v-container>
        <v-row justify="center">
          <!-- <v-btn @click="sendPauseCommand">{{ buttonText }}</v-btn> -->
           <PauseResumeButton />
        </v-row>
      </v-container>
    </v-app>
</template>

<script setup lang="ts">
    import { defineProps, ref, defineComponent } from 'vue';
    import PauseResumeButton from './PauseResumeButton.vue';

    // export default defineComponent({
    //     components: {PauseResumeButton}
    // });

    // const isPressed = ref(false);
    // const buttonText = ref('Pause Action');

    // const sendPauseCommand = async () => {

    //     isPressed.value = !isPressed.value;
    //     buttonText.value = isPressed.value ? 'Action Paused' : 'Pause Action';

    //     try {
    //         const response = await fetch('http://localhost:8000/admin/pause/measure', {method: 'POST',});
    //         console.log("RESPONSE FROM PAUSE POST")
    //         console.log(response)

    //     if (!response.ok) {
    //         throw new Error(`HTTP error! status: ${response.status}`);
    //     }

    //     // const data = await response.json();
    //     // console.log('Module paused:', data);
    //   } catch (error) {
    //         console.error('Error pausing module:', error);
    //   }
    // }

    // async pauseAction() {

    //     try {
    //         

    //     } catch (error) {
    //         console.error('Error pausing module:', error);
    //     }



       
    // }

    // async sendPauseCommand() {
    //   try {
    //     const response = await fetch('http://localhost:8000/admin/pause', {
    //       method: 'POST',
    //     });

    //     if (!response.ok) {
    //       throw new Error(`HTTP error! status: ${response.status}`);
    //     }

    //     const data = await response.json();
    //     console.log('Module paused:', data);
    //   } catch (error) {
    //     console.error('Error pausing module:', error);
    //   }
    // }





    // async function pause_action()
</script>
  
<style scoped>
  h1 {
    color: #42b983;
    text-align: center;
  }
</style>



