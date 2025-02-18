<script setup>
// Unused!
</script>

<script>
export default {
  name: 'ImageEditor',
  props: {
    imageBlob: {
      type: Blob,
      required: true,
    },
  },
  computed: {
    imageSrc() {
      return URL.createObjectURL(this.imageBlob);
    },
  },
};
</script>


<template>
  <v-img :src="imageBlob"></v-img>
</template>

<style scoped>
</style>