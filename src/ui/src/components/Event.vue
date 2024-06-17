<template>
    <vue-json-pretty :data="event" />
</template>

<script setup lang="ts">

import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
const props = defineProps(['event', "wc_state"])

</script>
