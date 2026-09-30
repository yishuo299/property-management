<template>
  <div>
    <h2 class="page-title">{{ title }}</h2>
    <p v-if="desc" class="page-desc">{{ desc }}</p>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  desc: { type: String, default: '' }
})
</script>
