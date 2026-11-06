<template>
  <RouterView />
  <ToastContainer />
</template>

<script setup lang="ts">
import ToastContainer from '@/components/ToastContainer.vue'
</script>

<style>
#app { width: 100%; height: 100vh; }
</style>
