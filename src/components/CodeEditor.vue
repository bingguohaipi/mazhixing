<template>
  <div ref="containerRef" class="code-editor-container"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import loader from '@monaco-editor/loader'
import type * as Monaco from 'monaco-editor'

const props = defineProps<{
  modelValue: string
  language: 'Python' | 'C++'
  readOnly?: boolean
  highlightLineNumbers?: number[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLDivElement | null>(null)
let editor: Monaco.editor.IStandaloneCodeEditor | null = null
let monacoInstance: typeof Monaco | null = null
let decorationIds: string[] = []

const monacoLanguage = (lang: 'Python' | 'C++'): string => (lang === 'Python' ? 'python' : 'cpp')

onMounted(async () => {
  if (!containerRef.value) return

  const monaco = await loader.init()
  monacoInstance = monaco
  const createdEditor = monaco.editor.create(containerRef.value, {
    value: props.modelValue,
    language: monacoLanguage(props.language),
    theme: 'vs-dark',
    fontSize: 14,
    lineNumbers: 'on',
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 4,
    readOnly: props.readOnly ?? false,
    quickSuggestions: true,
    suggestOnTriggerCharacters: true,
    wordBasedSuggestions: 'currentDocument',
    parameterHints: { enabled: true },
  })
  editor = createdEditor

  createdEditor.onDidChangeModelContent(() => {
    emit('update:modelValue', createdEditor.getValue())
  })
  applyHighlightLines(props.highlightLineNumbers ?? [])
})

watch(
  () => props.language,
  (lang) => {
    if (!editor || !monacoInstance) return
    const model = editor.getModel()
    if (model) {
      monacoInstance.editor.setModelLanguage(model, monacoLanguage(lang))
    }
  },
)

watch(
  () => props.modelValue,
  (value) => {
    if (editor && editor.getValue() !== value) {
      editor.setValue(value)
    }
  },
)

watch(
  () => props.readOnly,
  (readOnly) => {
    editor?.updateOptions({ readOnly: readOnly ?? false })
  },
)

const applyHighlightLines = (lines: number[]) => {
  if (!editor || !monacoInstance) return
  const model = editor.getModel()
  if (!model) return
  const decorations = lines
    .filter((line) => line >= 1 && line <= model.getLineCount())
    .map((line) => ({
      range: new monacoInstance!.Range(line, 1, line, 1),
      options: {
        isWholeLine: true,
        className: 'ai-error-line-highlight',
        glyphMarginClassName: 'ai-error-line-glyph',
      },
    }))
  decorationIds = editor.deltaDecorations(decorationIds, decorations)
}

watch(
  () => props.highlightLineNumbers,
  (lines) => {
    applyHighlightLines(lines ?? [])
  },
  { deep: true },
)

onBeforeUnmount(() => {
  editor?.dispose()
})

defineExpose({
  getValue: () => editor?.getValue() ?? '',
  revealLine: (line: number) => {
    if (!editor) return
    editor.revealLineInCenter(line)
    editor.setPosition({ lineNumber: line, column: 1 })
  },
})
</script>

<style scoped>
.code-editor-container {
  width: 100%;
  height: 100%;
  min-height: 300px;
}

:deep(.ai-error-line-highlight) {
  background: rgba(255, 77, 79, 0.18);
}

:deep(.ai-error-line-glyph) {
  background: #ff4d4f;
  margin-left: 4px;
  width: 4px !important;
}
</style>
