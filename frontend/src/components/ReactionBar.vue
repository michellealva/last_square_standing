<template>
  <div class="mt-3 flex justify-center gap-1.5">
    <button
      v-for="e in emojis"
      :key="e"
      type="button"
      class="rounded-full bg-white/5 px-2.5 py-1.5 text-lg ring-1 ring-white/10 transition hover:bg-white/10 active:scale-90"
      @click="$emit('react', e)"
    >
      {{ e }}
    </button>
  </div>
</template>

<script setup>
defineProps({ emojis: { type: Array, default: () => [] } })
defineEmits(['react'])
</script>
