<template>
  <div>
    <ModuleModal :modal_title="modal_title" :modal_text="modal_text" :main_url="main_url" :wc_state="wc_state" v-model="modal" />
    <v-card class="pa-1" title="Modules">
      <v-card-text>
        <v-container v-if="modules" fluid class="pa-1">
          <v-row no-gutter wrap justify-content class="pa-1">
            <v-col class="pa-1" cols=12 xl=6 v-for="(value, module_name) in modules" :key="module_name">
              <v-card class="pa-1 module_indicator" @click="set_modal(String(module_name), value.about)"
                :class="value.state.status">
                <v-card-text>
                  <h4 >{{ module_name }}</h4>
                 
                  <p class="text-caption">
                   status: {{ value.state.status }} 
                  </p>
                  <div  v-for="(value2, key2) in value.state" >
                  <p v-if="(key2.toString() != 'status') && (value2 != null)" class="text-caption">
                    {{ key2 }} : {{ value2 }}
                  </p>
                </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
        <p v-else> No Modules Yet</p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">

import { ref } from 'vue';
const props = defineProps(['modules', 'wc_state', 'main_url'])
const modal_title = ref()
const modal = ref(false)
const modal_text = ref()
const set_modal = (title: string, value: Object) => {
  modal_title.value = title
  modal_text.value = value
  modal.value = true
}
</script>
