<template>
  <v-card class="pa-1" col="3" title="Locations">
    <v-card-text>
      <v-list v-if=locations>
        <v-list-item v-for="(value, key) in locations" :key="key" :title="key" :subtitle="value.state"></v-list-item>
      </v-list>
      <p v-else>No Locations Yet</p>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
const props = defineProps(['locations'])
</script>
