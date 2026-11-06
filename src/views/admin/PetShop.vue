<template>
  <div class="app-page-shell space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <div class="flex flex-wrap items-center gap-3">
          <h1 class="text-lg font-semibold text-gray-900">宠物商城配置</h1>
          <button
            type="button"
            class="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
            @click="openCreateModal"
          >
            新增商品
          </button>
        </div>
        <p v-if="pointsConfig" class="text-xs text-gray-500 mt-1">
          积分上线时间：{{ formatTime(pointsConfig.points_launched_at) }} · 首 AC +{{
            pointsConfig.points_per_first_ac
          }}
          分
        </p>
      </div>
    </div>

    <ListQueryToolbar
      v-model:keyword="keyword"
      v-model:sort-value="sortValue"
      :sort-options="sortOptions"
      placeholder="模糊搜索 SKU / 名称 / 类型…"
      :filter-active="Boolean(categoryFilter)"
      filter-aria-label="筛选商品"
      @toggle-filter="toggleFilter"
    >
      <template #filter>
        <AdminPetShopFilterPopover
          :open="filterOpen"
          :category="draftCategory"
          @update:category="draftCategory = $event"
          @apply="onFilterApply"
          @reset="onFilterReset"
        />
      </template>
    </ListQueryToolbar>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>
    <div v-else-if="displayedItems.length === 0" class="text-center py-12 text-gray-500">
      {{ hasListQuery ? '没有匹配的商品' : '暂无商品' }}
    </div>
    <div v-else class="bg-white border border-gray-100 rounded-xl overflow-x-auto">
      <table class="w-full text-sm min-w-[820px]">
        <thead class="bg-gray-50 text-left text-gray-600">
          <tr>
            <th class="px-4 py-3">图片</th>
            <th class="px-4 py-3">SKU</th>
            <th class="px-4 py-3">名称</th>
            <th class="px-4 py-3">类型</th>
            <th class="px-4 py-3">价格</th>
            <th class="px-4 py-3">上架</th>
            <th class="px-4 py-3">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in displayedItems" :key="row.sku" class="border-t border-gray-50 align-top">
            <td class="px-4 py-3">
              <div class="flex flex-col items-start gap-2">
                <div
                  class="w-14 h-14 rounded-lg border border-gray-200 bg-gray-50 flex items-center justify-center overflow-hidden"
                >
                  <img
                    v-if="row.preview_asset_url"
                    :src="row.preview_asset_url"
                    :alt="row.name"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="text-xs text-gray-400">无图</span>
                </div>
                <label class="text-xs text-indigo-600 cursor-pointer hover:underline">
                  {{ uploading === row.sku ? '上传中…' : '上传图片' }}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    class="hidden"
                    :disabled="uploading === row.sku"
                    @change="onPickImage(row, $event)"
                  />
                </label>
                <button
                  v-if="row.preview_asset_url"
                  type="button"
                  class="text-xs text-red-500 hover:underline"
                  @click="clearImage(row)"
                >
                  清除
                </button>
              </div>
            </td>
            <td class="px-4 py-3 font-mono text-xs">{{ row.sku }}</td>
            <td class="px-4 py-3">
              <input
                v-model="row.name"
                class="pet-shop-field border border-gray-200 rounded px-2 py-1 w-full max-w-[140px]"
              />
            </td>
            <td class="px-4 py-3 text-gray-900">{{ shopCategoryLabel(row.category) }}</td>
            <td class="px-4 py-3">
              <input
                v-model.number="row.price"
                type="number"
                min="1"
                class="pet-shop-field border border-gray-200 rounded px-2 py-1 w-20"
              />
            </td>
            <td class="px-4 py-3">
              <input v-model="row.is_active" type="checkbox" />
            </td>
            <td class="px-4 py-3 space-x-2 whitespace-nowrap">
              <button
                type="button"
                class="text-indigo-600 hover:underline disabled:opacity-50"
                :disabled="saving === row.sku"
                @click="saveRow(row)"
              >
                {{ saving === row.sku ? '保存中' : '保存' }}
              </button>
              <button
                type="button"
                class="text-red-600 hover:underline disabled:opacity-50"
                :disabled="deleting === row.sku"
                @click="removeRow(row)"
              >
                {{ deleting === row.sku ? '删除中' : '删除' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showCreate" class="modal-mask">
      <div class="modal-box" style="width: 440px;">
        <h3 class="modal-title">新增商品</h3>
        <p class="modal-sub">SKU 创建后不可修改；已有学生持有的商品无法删除</p>
        <div class="modal-field">
          <label class="modal-label">SKU（小写英文，如 food_snack）</label>
          <input v-model="createForm.sku" class="modal-input input-light-bg" placeholder="food_snack" />
        </div>
        <div class="modal-field">
          <label class="modal-label">类型</label>
          <select v-model="createForm.category" class="modal-input input-light-bg">
            <option value="pet">宠物</option>
            <option value="food">食物</option>
            <option value="drink">饮料</option>
          </select>
        </div>
        <div class="modal-field">
          <label class="modal-label">名称</label>
          <input v-model="createForm.name" class="modal-input input-light-bg" />
        </div>
        <div class="modal-field">
          <label class="modal-label">描述</label>
          <input v-model="createForm.description" class="modal-input input-light-bg" />
        </div>
        <div class="modal-field">
          <label class="modal-label">价格（积分）</label>
          <input v-model.number="createForm.price" type="number" min="1" class="modal-input input-light-bg" />
        </div>
        <div class="modal-field">
          <label class="modal-label">资源 key（宠物 SVG 用，如 cat_blue）</label>
          <input v-model="createForm.asset_key" class="modal-input input-light-bg" />
        </div>
        <div v-if="createForm.category === 'pet'" class="modal-field">
          <label class="modal-label">稀有度</label>
          <select v-model="createForm.rarity" class="modal-input input-light-bg">
            <option value="common">普通</option>
            <option value="rare">稀有</option>
          </select>
        </div>
        <div v-if="createForm.category === 'food'" class="grid grid-cols-2 gap-2">
          <div class="modal-field">
            <label class="modal-label">经验</label>
            <input v-model.number="createForm.effect_exp" type="number" min="0" class="modal-input input-light-bg" />
          </div>
          <div class="modal-field">
            <label class="modal-label">饱食</label>
            <input v-model.number="createForm.effect_satiety" type="number" min="0" class="modal-input input-light-bg" />
          </div>
        </div>
        <div v-if="createForm.category === 'drink'" class="modal-field">
          <label class="modal-label">心情</label>
          <input v-model.number="createForm.effect_mood" type="number" min="0" class="modal-input input-light-bg" />
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button type="button" class="modal-btn-cancel" @click="showCreate = false">取消</button>
          <button type="button" class="modal-btn-confirm" :disabled="creating" @click="submitCreate">
            {{ creating ? '提交中…' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { adminPetApi, type AdminShopItem, type AdminPetPointsConfig } from '@/api/admin-pet'
import AdminPetShopFilterPopover from '@/components/admin/AdminPetShopFilterPopover.vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import type { ShopItemCategory } from '@/types/pet'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useListFilterPanel } from '@/composables/useListFilterPanel'
import { shopCategoryLabel } from '@/utils/pet-shop-category'
import { toast } from '@/utils/toast'

const loading = ref(true)
const saving = ref<string | null>(null)
const deleting = ref<string | null>(null)
const uploading = ref<string | null>(null)
const showCreate = ref(false)
const creating = ref(false)
const createForm = reactive({
  sku: '',
  category: 'food' as ShopItemCategory,
  name: '',
  description: '',
  price: 10,
  asset_key: '',
  rarity: 'common' as 'common' | 'rare',
  effect_exp: 15,
  effect_satiety: 20,
  effect_mood: 25,
})
const allItems = ref<AdminShopItem[]>([])
const pointsConfig = ref<AdminPetPointsConfig | null>(null)
const keyword = ref('')
const categoryFilter = ref('')
const draftCategory = ref('')
const sortValue = ref('price:asc')
const sortOptions = [
  { value: 'price:asc', label: '价格 ↑' },
  { value: 'price:desc', label: '价格 ↓' },
]
const { filterOpen, toggleFilter, closeFilter } = useListFilterPanel()

const hasListQuery = computed(
  () => Boolean(keyword.value.trim() || categoryFilter.value || sortValue.value !== 'price:asc'),
)

const displayedItems = computed(() => {
  let rows = [...allItems.value]
  if (categoryFilter.value) {
    rows = rows.filter((row) => row.category === categoryFilter.value)
  }
  const desc = sortValue.value === 'price:desc'
  rows.sort((a, b) => (desc ? b.price - a.price : a.price - b.price))
  return rows
})

const onFilterApply = () => {
  categoryFilter.value = draftCategory.value
  closeFilter()
}

const onFilterReset = () => {
  draftCategory.value = ''
  categoryFilter.value = ''
  closeFilter()
}

function formatTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN')
}

async function loadItems() {
  loading.value = true
  try {
    allItems.value = await adminPetApi.listItems(keyword.value.trim() || undefined)
  } catch {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const [list, cfg] = await Promise.all([
      adminPetApi.listItems(),
      adminPetApi.getPointsConfig(),
    ])
    allItems.value = list
    pointsConfig.value = cfg
  } catch {
    toast.error('加载失败')
  } finally {
    loading.value = false
  }
}

useDebouncedWatch(keyword, () => {
  void loadItems()
})

async function saveRow(row: AdminShopItem) {
  saving.value = row.sku
  try {
    const updated = await adminPetApi.patchItem(row.sku, {
      name: row.name,
      price: row.price,
      is_active: row.is_active,
      preview_asset_url: row.preview_asset_url,
    })
    Object.assign(row, updated)
    toast.success('已保存')
  } catch {
    toast.error('保存失败')
  } finally {
    saving.value = null
  }
}

async function onPickImage(row: AdminShopItem, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploading.value = row.sku
  try {
    const updated = await adminPetApi.uploadPreviewImage(row.sku, file)
    Object.assign(row, updated)
    toast.success('图片已更新')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '上传失败'
    toast.error(msg)
  } finally {
    uploading.value = null
  }
}

async function clearImage(row: AdminShopItem) {
  row.preview_asset_url = ''
  await saveRow(row)
}

function openCreateModal() {
  createForm.sku = ''
  createForm.category = 'food'
  createForm.name = ''
  createForm.description = ''
  createForm.price = 10
  createForm.asset_key = ''
  createForm.rarity = 'common'
  createForm.effect_exp = 15
  createForm.effect_satiety = 20
  createForm.effect_mood = 25
  showCreate.value = true
}

async function submitCreate() {
  const sku = createForm.sku.trim()
  const assetKey = createForm.asset_key.trim() || sku.replace(/^pet_|^food_|^drink_/, '') || sku
  if (!sku || !createForm.name.trim()) {
    toast.error('请填写 SKU 和名称')
    return
  }
  creating.value = true
  try {
    await adminPetApi.createItem({
      sku,
      category: createForm.category,
      name: createForm.name.trim(),
      description: createForm.description.trim(),
      price: createForm.price,
      asset_key: assetKey,
      rarity: createForm.category === 'pet' ? createForm.rarity : null,
      effect_exp: createForm.category === 'food' ? createForm.effect_exp : undefined,
      effect_satiety: createForm.category === 'food' ? createForm.effect_satiety : undefined,
      effect_mood: createForm.category === 'drink' ? createForm.effect_mood : undefined,
      is_active: true,
    })
    toast.success('商品已创建')
    showCreate.value = false
    await load()
  } catch (e: unknown) {
    toast.error(e instanceof Error ? e.message : '创建失败')
  } finally {
    creating.value = false
  }
}

async function removeRow(row: AdminShopItem) {
  if (!confirm(`确定删除商品「${row.name}」（${row.sku}）？`)) return
  deleting.value = row.sku
  try {
    await adminPetApi.deleteItem(row.sku)
    toast.success('已删除')
    allItems.value = allItems.value.filter((item) => item.sku !== row.sku)
  } catch (e: unknown) {
    toast.error(e instanceof Error ? e.message : '删除失败')
  } finally {
    deleting.value = null
  }
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.pet-shop-field {
  background-color: #ffffff;
  color: #111827;
}

.pet-shop-field::placeholder {
  color: #9ca3af;
}
</style>
