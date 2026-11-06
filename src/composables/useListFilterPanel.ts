import { onBeforeUnmount, ref } from 'vue'

/** 点击外部关闭筛选浮层 */
export function useListFilterPanel() {
  const filterOpen = ref(false)

  const onDocumentClick = (event: MouseEvent) => {
    if (!filterOpen.value) return
    const target = event.target as HTMLElement
    if (target.closest('.practice-filter-popover')) return
    if (target.closest('.list-query-toolbar-filter-btn')) return
    filterOpen.value = false
  }

  const bindFilterListeners = () => {
    document.addEventListener('mousedown', onDocumentClick)
  }

  const unbindFilterListeners = () => {
    document.removeEventListener('mousedown', onDocumentClick)
  }

  const toggleFilter = () => {
    filterOpen.value = !filterOpen.value
    if (filterOpen.value) {
      bindFilterListeners()
    } else {
      unbindFilterListeners()
    }
  }

  const closeFilter = () => {
    filterOpen.value = false
    unbindFilterListeners()
  }

  onBeforeUnmount(unbindFilterListeners)

  return { filterOpen, toggleFilter, closeFilter }
}
