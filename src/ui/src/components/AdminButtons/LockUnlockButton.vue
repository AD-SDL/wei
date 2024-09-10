<template>
    <div>
      <v-tooltip location="bottom">
        <template v-slot:activator="{ props }">
            <div v-bind="props">
            <v-btn
                @click="toggleLockUnlock"
                :color="isLocked ? 'grey-darken-3' : 'grey-lighten-1'"
                dark
                elevation="5" >
                <v-icon>
                    {{ isLocked ? 'mdi-lock-open' : 'mdi-lock' }}
                </v-icon>
            </v-btn>
            </div>
        </template>
         <span>
            {{ isLocked ? "Unlock " + hoverText : "Lock " + hoverText}}
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

    const lock_url = ref()
    const unlock_url = ref()
    const isLocked = ref(false);
    const hoverText = ref()

    // Format pause and resume urls
    if (props.module) {
        // TODO: Module lock and unlock urls
        hoverText.value = "Module"
    }
    else {
        // TODO: Workcell lock and unlock urls
        hoverText.value = "Workcell"
    }

    if (props.module) {
        watchEffect(() => {
        // Determine if the module is already locked
        // TODO: Implement 'LOCKED' status
        if (props.module_status == 'LOCKED') {
            isLocked.value = true
        } else {
            isLocked.value = false
        }
    })
    }

    // Function to toggle lock/unlock
    const toggleLockUnlock = async () => {
        // if (isLocked.value) {
        //     await sendUnlockCommand();
        // } else {
        //     await sendLockCommand();
        // }
        isLocked.value = !isLocked.value;
    };

    // // Function to send lock command
    // const sendLockCommand = async () => {
    //     try {
    //         const response = await fetch(lock_url.value, {
    //             method: 'POST',
    //         });
    //         if (!response.ok) {
    //             throw new Error(`HTTP error! status: ${response.status}`);
    //         }
    //         console.log('Locked');

    //     } catch (error) {
    //         console.error('Error locking:', error);
    //     }
    // };

    // // Function to send unlock command
    // const sendUnlockCommand = async () => {
    //     try {
    //         const response = await fetch(unlock_url.value, {
    //             method: 'POST',
    //         });

    //         if (!response.ok) {
    //             throw new Error(`HTTP error! status: ${response.status}`);
    //         }

    //         console.log('Unlocked');

    //     } catch (error) {
    //     console.error('Error unlocking:', error);
    //     }
    // };
</script>
