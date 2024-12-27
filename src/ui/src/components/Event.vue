<template>
    <div>
        <div v-if="event.event_name === 'STEP'">
            <h3 class="title">Step:</h3>
            <v-expansion-panels title="Step">
                <v-expansion-panel>
                    <v-expansion-panel-title>
                        <h4>{{ event.workflow_name }}</h4>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                        <vue-json-pretty :data="event.step"/>
                    </v-expansion-panel-text>
                </v-expansion-panel>
            </v-expansion-panels>
        </div>
        <h3>Details</h3>
        <vue-json-pretty v-if="event" :data="event" :deep="1"></vue-json-pretty>
    </div>
</template>

<script setup lang="ts">
import VueJsonPretty from 'vue-json-pretty';

const props = defineProps(['event'])

</script>

<style scoped>
.workcell-details {
    margin-top: 20px;
}
</style>