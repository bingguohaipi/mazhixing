<template>
  <div class="password-input-wrap">
    <input
      :type="visible ? 'text' : 'password'"
      :class="[inputClass, { error: hasError }]"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      @input="onInput"
      @blur="emit('blur')"
    />
    <button
      type="button"
      class="password-toggle"
      :aria-label="visible ? '隐藏密码' : '显示密码'"
      :aria-pressed="visible"
      tabindex="-1"
      @click="visible = !visible"
    >
      <svg
        v-if="visible"
        class="password-toggle-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.75"
        aria-hidden="true"
      >
        <path
          d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <circle cx="12" cy="12" r="3" />
      </svg>
      <svg
        v-else
        class="password-toggle-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.75"
        aria-hidden="true"
      >
        <path
          d="M3 3l18 18M10.5 10.7a3 3 0 0 0 4.2 4.2M9.9 5.1A10.8 10.8 0 0 1 12 5c6.5 0 10 7 10 7a18.2 18.2 0 0 1-2.1 3.1M6.1 6.1A18.5 18.5 0 0 0 2 12s3.5 7 10 7a10.3 10.3 0 0 0 5-1.3"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    inputClass?: 'form-input' | 'modal-input'
    hasError?: boolean
    autocomplete?: string
  }>(),
  {
    placeholder: '',
    inputClass: 'form-input',
    hasError: false,
    autocomplete: 'current-password',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const visible = ref(false)

const onInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>
