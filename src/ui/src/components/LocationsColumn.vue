<template>
  <v-card class="pa-1" col="3" title="Locations">
    <v-card-text>
      <v-list title="Locations">
        <v-list-item v-if=locations v-for="(value, key) in locations" :key="key" :title="key" :subtitle="value.state"></v-list-item>
        <p v-else>No Locations Yet</p>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">

const props = defineProps(['locations'])

</script>
