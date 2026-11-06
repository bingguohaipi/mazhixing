<template>
  <div class="app-page-shell space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-lg font-semibold text-gray-900">宠物商城</h1>
        <p class="text-sm text-gray-500">答对题目赚积分，领养桌面小伙伴</p>
      </div>
      <div class="flex items-center gap-4 text-sm">
        <span class="font-semibold text-indigo-600">🪙 {{ balance }} 积分</span>
        <RouterLink to="/student/points" class="text-indigo-600 hover:underline">积分明细</RouterLink>
      </div>
    </div>

    <div class="flex gap-2 border-b border-gray-200">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        class="px-4 py-2 text-sm -mb-px border-b-2 transition"
        :class="activeTab === tab.key ? 'border-indigo-600 text-indigo-600 font-medium' : 'border-transparent text-gray-500'"
        @click="activeTab = tab.key; load()"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-500">加载中...</div>

    <div v-else-if="activeTab === 'inventory'" class="space-y-3">
      <div v-if="inventory.length === 0" class="text-center py-10 text-gray-500">背包空空，去买点粮食吧</div>
      <div
        v-for="item in inventory"
        :key="item.sku"
        class="flex items-center justify-between border border-gray-200 rounded-xl p-4"
      >
        <div>
          <div class="font-medium">{{ item.name }}</div>
          <div class="text-xs text-gray-500">数量 {{ item.quantity }}</div>
        </div>
        <button
          type="button"
          class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg disabled:opacity-50"
          :disabled="using === item.sku"
          @click="useItem(item.sku)"
        >
          使用
        </button>
      </div>
    </div>

    <div v-else-if="activeTab === 'pets'" class="space-y-4">
      <div v-if="myPets.length" class="border border-gray-200 rounded-xl p-4">
        <h2 class="text-sm font-semibold mb-3">我的宠物</h2>
        <div class="flex flex-wrap gap-3">
          <div
            v-for="p in myPets"
            :key="p.id"
            class="border rounded-xl p-3 w-40 text-center bg-transparent"
            :class="p.is_active ? 'border-indigo-500' : 'border-gray-200'"
          >
            <PetAvatar :asset-key="p.asset_key" :size="72" :level="p.level" show-stage-label />
            <div class="text-sm font-medium mt-1">{{ p.name }}</div>
            <div class="text-xs text-gray-500">Lv.{{ p.level }}</div>
            <button
              v-if="!p.is_active"
              type="button"
              class="mt-2 text-xs text-indigo-600"
              @click="setActive(p.id)"
            >
              设为桌面伙伴
            </button>
            <span v-else class="mt-2 inline-block text-xs text-indigo-600">当前出战</span>
          </div>
        </div>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
        <CatalogCard
          v-for="item in catalogItems"
          :key="item.sku"
          :item="item"
          :buying="buying === item.sku"
          @buy="buy(item)"
        />
      </div>
    </div>

    <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
      <CatalogCard
        v-for="item in catalogItems"
        :key="item.sku"
        :item="item"
        :buying="buying === item.sku"
        @buy="buy(item)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { petApi } from '@/api/pet'
import { usePetStore } from '@/stores/pet'
import { toast } from '@/utils/toast'
import type { PetShopCatalogItem, StudentPetListItem } from '@/types/pet'
import { petEmojiForAssetKey } from '@/types/pet'
import PetAvatar from '@/components/PetAvatar.vue'

const petStore = usePetStore()
const loading = ref(true)
const buying = ref<string | null>(null)
const using = ref<string | null>(null)
const catalogItems = ref<PetShopCatalogItem[]>([])
const inventory = ref<Awaited<ReturnType<typeof petApi.getInventory>>>([])
const myPets = ref<StudentPetListItem[]>([])
const balance = ref(0)

const tabs = [
  { key: 'pets', label: '宠物' },
  { key: 'food', label: '食物' },
  { key: 'drink', label: '饮料' },
  { key: 'inventory', label: '我的背包' },
] as const

type TabKey = (typeof tabs)[number]['key']
const activeTab = ref<TabKey>('pets')

const CatalogCard = defineComponent({
  props: {
    item: { type: Object as () => PetShopCatalogItem, required: true },
    buying: Boolean,
  },
  emits: ['buy'],
  setup(props, { emit }) {
    const assetKey = props.item.lottie_url?.match(/\/lottie\/(.+)\.json$/)?.[1] ?? props.item.sku
    const previewUrl = props.item.preview_asset_url?.trim()
    return () =>
      h('div', { class: 'border border-gray-200 rounded-xl p-4 flex flex-col bg-transparent' }, [
        previewUrl
          ? h('div', { class: 'flex justify-center py-1' }, [
              h('img', {
                src: previewUrl,
                alt: props.item.name,
                class: 'w-[88px] h-[88px] object-contain rounded-lg',
              }),
            ])
          : props.item.category === 'pet'
            ? h('div', { class: 'flex flex-col items-center py-1' }, [
                h(PetAvatar, { assetKey, size: 88, level: 1 }),
                h('span', { class: 'text-[10px] text-gray-400 mt-1' }, '购买后为幼体'),
              ])
            : h('div', { class: 'text-4xl text-center' }, petEmojiForAssetKey(props.item.sku)),
        h('div', { class: 'font-medium text-center mt-2' }, props.item.name),
        h('div', { class: 'text-xs text-gray-500 text-center mt-1 min-h-[2rem]' }, props.item.effect_summary || props.item.description),
        h('div', { class: 'text-center text-sm font-semibold text-indigo-600 mt-2' }, `${props.item.price} 🪙`),
        h(
          'button',
          {
            type: 'button',
            class:
              'mt-3 w-full py-2 text-sm rounded-lg ' +
              (props.item.owned
                ? 'bg-gray-100 text-gray-500 cursor-default'
                : props.item.can_afford
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-100 text-gray-400'),
            disabled: props.item.owned || !props.item.can_afford || props.buying,
            onClick: () => emit('buy'),
          },
          props.item.owned ? '已拥有' : props.buying ? '购买中...' : props.item.can_afford ? '购买' : '积分不足',
        ),
      ])
  },
})

const categoryParam = computed(() => {
  if (activeTab.value === 'food' || activeTab.value === 'drink') return activeTab.value
  if (activeTab.value === 'pets') return 'pet'
  return undefined
})

async function load() {
  loading.value = true
  try {
    if (activeTab.value === 'inventory') {
      inventory.value = await petApi.getInventory()
      await petStore.refreshPoints()
      balance.value = petStore.points?.balance ?? 0
    } else if (activeTab.value === 'pets') {
      const [catalog, pets] = await Promise.all([petApi.getCatalog('pet'), petApi.listPets()])
      catalogItems.value = catalog.items
      balance.value = catalog.balance
      myPets.value = pets
    } else {
      const catalog = await petApi.getCatalog(categoryParam.value)
      catalogItems.value = catalog.items
      balance.value = catalog.balance
    }
  } catch {
    toast.error('网络连接异常，请检查网络后重试')
  } finally {
    loading.value = false
  }
}

async function buy(item: PetShopCatalogItem) {
  if (item.owned || !item.can_afford) return
  if (item.category === 'pet' && !window.confirm(`确定领养「${item.name}」？将消耗 ${item.price} 积分`)) {
    return
  }
  buying.value = item.sku
  try {
    const res = await petApi.purchase(item.sku, 1)
    balance.value = res.balance
    await petStore.refreshPoints()
    await petStore.refreshActivePet()
    toast.success('购买成功')
    await load()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '购买失败'
    toast.error(msg)
  } finally {
    buying.value = null
  }
}

async function useItem(sku: string) {
  using.value = sku
  try {
    await petApi.useItem(sku, 1)
    toast.success('已喂养小伙伴')
    await petStore.refreshActivePet()
    await load()
  } catch {
    toast.error('使用失败，请确认已设置出战宠物')
  } finally {
    using.value = null
  }
}

async function setActive(petId: number) {
  await petApi.activatePet(petId)
  await petStore.refreshActivePet()
  await load()
  toast.success('已切换桌面伙伴')
}

onMounted(() => {
  void load()
})
</script>
