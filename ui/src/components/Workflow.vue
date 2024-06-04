<template>
  <div class="d-flex-column">
    <h4>Steps</h4>
    
    <v-expansion-panels title="Steps">
      
      <v-expansion-panel v-for="(value, key) in steps" :key="key">
        <v-expansion-panel-title>
          <h4>{{ value.name }}</h4>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          
          <b>Description</b>: {{ value.comment }} <br>
          <b> Module</b>: {{ value.module }} <br>
          <b>Module Action</b>: {{ value.action }} <br>
          <b>Args</b>: <v-list>
            <v-list-item v-for="(arg_value, arg_key) in value.args" :key="arg_key">
              <b>{{ arg_key }}</b>: {{ arg_value }}
            </v-list-item>
          </v-list>
          <div v-if="!(value.start_time == '') && !(value.start_time == null)"><b>Start Time</b>: {{ value.start_time }}
          </div>
          <div v-if="!(value.end_time == '') && !(value.end_time == null)"><b>End Time</b>: {{ value.end_time }}</div>
          <div v-if="!(value.result == '') && !(value.result == null)"><b>Action Response</b>: {{
        value.result.action_response }} <br>
           <div v-if="!(value.result.action_msg == '')"> <b>Action Message:</b> {{ value.result.action_msg }}<br></div>
           <div v-if="!(value.result.action_log == '')"><b>Action Log:</b> {{ value.result.action_log }}</div>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script setup lang="ts">
const props = defineProps(['steps'])
const arg_headers = [
  { title: 'Name', key: 'name' },
 
]
</script>
