<template>
  <div class="p-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold">用户管理</h1>
      <button class="px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm" @click="showCreate = true">新建用户</button>
    </div>
    <ListQueryToolbar
      v-model:keyword="keyword"
      placeholder="搜索账号 / 姓名"
      :filter-active="Boolean(roleFilter)"
      filter-aria-label="筛选用户"
      @toggle-filter="toggleFilter"
    >
      <template #filter>
        <AdminUsersFilterPopover
          :open="filterOpen"
          :role="draftRole"
          @update:role="draftRole = $event"
          @apply="onFilterApply"
          @reset="onFilterReset"
        />
      </template>
    </ListQueryToolbar>
    <div class="bg-white border rounded-xl overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-500">
          <tr>
            <th class="px-4 py-2 text-left">ID</th>
            <th class="px-4 py-2 text-left">账号</th>
            <th class="px-4 py-2 text-left">角色</th>
            <th class="px-4 py-2 text-left">真实姓名</th>
            <th class="px-4 py-2 text-left">昵称</th>
            <th class="px-4 py-2 text-left">班级</th>
            <th class="px-4 py-2 text-left">关联</th>
            <th class="px-4 py-2 text-left">状态</th>
            <th class="px-4 py-2 text-left">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-t">
            <td class="px-4 py-2">{{ u.id }}</td>
            <td class="px-4 py-2">{{ u.account }}</td>
            <td class="px-4 py-2">{{ userRoleLabel(u.role) }}</td>
            <td class="px-4 py-2">{{ u.real_name || u.display_name || '-' }}</td>
            <td class="px-4 py-2 text-gray-600">{{ u.nickname || '-' }}</td>
            <td class="px-4 py-2 text-gray-600 max-w-[10rem]">
              <span v-if="u.class_names?.length">{{ u.class_names.join('、') }}</span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-2 text-gray-600 max-w-xs">
              <template v-if="u.relation_summary?.length">
                <div v-for="(line, idx) in u.relation_summary" :key="idx" class="leading-snug">{{ line }}</div>
              </template>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-2">{{ u.is_active ? '正常' : '禁用' }}</td>
            <td class="px-4 py-2">
              <button class="text-indigo-600 mr-2" @click="openEdit(u)">编辑</button>
              <button
                v-if="u.role === 'student' || u.role === 'parent' || u.role === 'teacher'"
                class="text-indigo-600 mr-2"
                @click="openRelations(u)"
              >
                {{ u.role === 'teacher' ? '查看关联' : '绑定关系' }}
              </button>
              <button class="text-indigo-600 mr-2" @click="toggleActive(u)">{{ u.is_active ? '禁用' : '启用' }}</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editUser" class="modal-mask">
      <div class="modal-box" style="width: 440px;">
        <h3 class="modal-title">编辑用户 · {{ userRoleLabel(editUser.role) }}</h3>
        <p class="modal-sub">ID {{ editUser.id }}</p>
        <div v-if="editUser.role === 'parent'" class="modal-field">
          <label class="modal-label">手机号（登录账号）</label>
          <input v-model="editForm.phone" class="modal-input" placeholder="11 位手机号">
        </div>
        <template v-else>
          <div class="modal-field">
            <label class="modal-label">账号</label>
            <input v-model="editForm.account" class="modal-input">
          </div>
          <div v-if="editUser.role === 'teacher'" class="modal-field">
            <label class="modal-label">手机号</label>
            <input v-model="editForm.phone" class="modal-input" placeholder="可选">
          </div>
        </template>
        <div class="modal-field">
          <label class="modal-label">真实姓名</label>
          <input v-model="editForm.display_name" class="modal-input">
        </div>
        <div class="modal-field">
          <label class="modal-label">昵称</label>
          <input v-model="editForm.nickname" class="modal-input" placeholder="用户也可自行修改，留空表示无">
        </div>
        <div v-if="editUser.role === 'student'" class="modal-field">
          <label class="modal-label">学号</label>
          <input v-model="editForm.student_no" class="modal-input" placeholder="可选">
        </div>
        <div v-if="editUser.role === 'student'" class="modal-field">
          <label class="modal-label">负责教师 ID</label>
          <input
            v-model="editForm.created_by_teacher_id"
            type="number"
            class="modal-input"
            placeholder="留空表示无"
          >
        </div>
        <div class="modal-field">
          <label class="modal-label">新密码</label>
          <input v-model="editForm.password" type="password" class="modal-input" placeholder="不修改请留空">
        </div>
        <div class="modal-field flex items-center gap-2">
          <input id="edit-active" v-model="editForm.is_active" type="checkbox">
          <label for="edit-active" class="modal-label mb-0">账号正常（启用）</label>
        </div>
        <div v-if="editError" class="modal-error show" style="margin-bottom: 12px;">{{ editError }}</div>
        <div class="modal-actions">
          <button class="modal-btn-cancel" @click="closeEdit">取消</button>
          <button class="modal-btn-confirm" :disabled="editSubmitting" @click="saveEdit">
            {{ editSubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="modal-mask">
      <div class="modal-box" style="width: 420px;">
        <h3 class="modal-title">新建用户</h3>
        <div class="modal-field"><label class="modal-label">角色</label>
          <select v-model="createForm.role" class="modal-input"><option value="teacher">教师</option><option value="student">学生</option><option value="parent">家长</option></select>
        </div>
        <template v-if="createForm.role === 'student'">
          <p class="text-xs text-gray-500 mb-3">
            仅需填写真实姓名，系统将自动生成登录账号，默认密码为 123456。
          </p>
          <div class="modal-field">
            <label class="modal-label">真实姓名 <span class="text-red-500">*</span></label>
            <input
              v-model="createForm.display_name"
              class="modal-input"
              placeholder="请输入学生真实姓名"
            >
          </div>
        </template>
        <template v-else-if="createForm.role === 'parent'">
          <div class="modal-field">
            <label class="modal-label">手机号（登录账号）</label>
            <input v-model="createForm.phone" class="modal-input" placeholder="11 位手机号">
          </div>
          <div class="modal-field">
            <label class="modal-label">密码</label>
            <input v-model="createForm.password" class="modal-input" type="password">
          </div>
          <div class="modal-field">
            <label class="modal-label">姓名</label>
            <input v-model="createForm.display_name" class="modal-input">
          </div>
        </template>
        <template v-else>
          <div class="modal-field">
            <label class="modal-label">账号</label>
            <input v-model="createForm.account" class="modal-input">
          </div>
          <div class="modal-field">
            <label class="modal-label">密码</label>
            <input v-model="createForm.password" class="modal-input" type="password">
          </div>
          <div class="modal-field">
            <label class="modal-label">姓名</label>
            <input v-model="createForm.display_name" class="modal-input">
          </div>
        </template>
        <div class="modal-actions">
          <button class="modal-btn-cancel" @click="showCreate = false">取消</button>
          <button class="modal-btn-confirm" @click="createUser">创建</button>
        </div>
      </div>
    </div>

    <div v-if="relationsUser" class="modal-mask">
      <div class="modal-box" style="width: 520px; max-height: 90vh; overflow-y: auto;">
        <h3 class="modal-title">绑定关系 · {{ relationsUser.display_name || relationsUser.account }}</h3>

        <template v-if="relations">
          <div v-if="relations.role === 'student'" class="space-y-4 text-sm">
            <section v-if="relations.student_teacher_lines?.length">
              <h4 class="font-medium text-gray-800 mb-2">教师与班级</h4>
              <ul class="text-gray-600 space-y-1 mb-2">
                <li v-for="(line, idx) in relations.student_teacher_lines" :key="idx">{{ line }}</li>
              </ul>
            </section>
            <section>
              <h4 class="font-medium text-gray-800 mb-2">负责教师（名册）</h4>
              <p v-if="relations.teacher" class="text-gray-600 mb-2">
                {{ relations.teacher.display_name || relations.teacher.account }}（ID {{ relations.teacher.id }}）
              </p>
              <p v-else class="text-gray-400 mb-2">未绑定教师</p>
              <div class="flex gap-2 items-center">
                <input
                  v-model.number="teacherIdInput"
                  type="number"
                  class="modal-input flex-1"
                  placeholder="教师用户 ID"
                >
                <button class="px-3 py-1.5 border rounded-lg text-xs" @click="saveTeacher">换绑</button>
                <button class="px-3 py-1.5 border rounded-lg text-xs text-red-600" @click="clearTeacher">解绑</button>
              </div>
            </section>
            <section>
              <h4 class="font-medium text-gray-800 mb-2">已绑定家长</h4>
              <ul v-if="relations.parent_bindings.length" class="space-y-2 mb-3">
                <li
                  v-for="b in relations.parent_bindings"
                  :key="b.id"
                  class="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg"
                >
                  <span>{{ b.parent_name || b.parent_account }}（ID {{ b.parent_id }}）</span>
                  <span class="flex gap-2">
                    <button class="text-indigo-600 text-xs" @click="promptRebindParent(b)">换绑</button>
                    <button class="text-red-600 text-xs" @click="unbind(b.id)">解绑</button>
                  </span>
                </li>
              </ul>
              <p v-else class="text-gray-400 mb-2">暂无家长绑定</p>
            </section>
          </div>

          <div v-else-if="relations.role === 'teacher'" class="space-y-4 text-sm">
            <section>
              <h4 class="font-medium text-gray-800 mb-2">任教班级</h4>
              <ul v-if="relations.teaching_classes?.length" class="text-gray-600 space-y-1">
                <li v-for="(name, idx) in relations.teaching_classes" :key="idx">{{ name }}</li>
              </ul>
              <p v-else class="text-gray-400">暂无班级</p>
            </section>
          </div>

          <div v-else-if="relations.role === 'parent'" class="space-y-4 text-sm">
            <section>
              <h4 class="font-medium text-gray-800 mb-2">已绑定学生</h4>
              <ul v-if="relations.bound_children.length" class="space-y-2 mb-3">
                <li
                  v-for="b in relations.bound_children"
                  :key="b.id"
                  class="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg"
                >
                  <span>{{ b.student_name || b.student_id }}（ID {{ b.student_id }}）</span>
                  <span class="flex gap-2">
                    <button class="text-red-600 text-xs" @click="unbind(b.id)">解绑</button>
                  </span>
                </li>
              </ul>
              <p v-else class="text-gray-400 mb-2">暂无学生绑定</p>
            </section>
          </div>

          <section v-if="relations.role !== 'teacher'" class="border-t pt-4 mt-4">
            <h4 class="font-medium text-gray-800 mb-2">新建家长 ↔ 学生绑定</h4>
            <div class="flex gap-2">
              <input v-model.number="bindParentId" type="number" class="modal-input flex-1" placeholder="家长 ID">
              <input v-model.number="bindStudentId" type="number" class="modal-input flex-1" placeholder="学生 ID">
            </div>
            <button class="mt-2 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs" @click="createBinding">
              绑定
            </button>
          </section>
        </template>

        <div v-if="relationsLoading" class="text-gray-500 py-8 text-center">加载中...</div>
        <div class="modal-actions mt-4">
          <button class="modal-btn-cancel" @click="closeRelations">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { useListFilterPanel } from '@/composables/useListFilterPanel'
import { adminApi } from '@/api/admin'
import AdminUsersFilterPopover from '@/components/admin/AdminUsersFilterPopover.vue'
import ListQueryToolbar from '@/components/ListQueryToolbar.vue'
import type { AdminUserListItem, AdminUserRelationsResponse, AdminUserUpdatePayload } from '@/types/admin'
import { toast } from '@/utils/toast'
import { userRoleLabel } from '@/utils/user-role'

const users = ref<AdminUserListItem[]>([])
const roleFilter = ref('')
const draftRole = ref('')
const keyword = ref('')
const { filterOpen, toggleFilter, closeFilter } = useListFilterPanel()

const onFilterApply = () => {
  roleFilter.value = draftRole.value
  closeFilter()
  void load()
}

const onFilterReset = () => {
  draftRole.value = ''
  roleFilter.value = ''
  closeFilter()
  void load()
}
const showCreate = ref(false)
const createForm = reactive<{
  role: 'teacher' | 'student' | 'parent'
  account: string
  phone: string
  password: string
  display_name: string
}>({
  role: 'teacher',
  account: '',
  phone: '',
  password: '',
  display_name: '',
})

const relationsUser = ref<AdminUserListItem | null>(null)
const relations = ref<AdminUserRelationsResponse | null>(null)
const relationsLoading = ref(false)
const teacherIdInput = ref<number | null>(null)
const bindParentId = ref<number | null>(null)
const bindStudentId = ref<number | null>(null)

const editUser = ref<AdminUserListItem | null>(null)
const editSubmitting = ref(false)
const editError = ref('')
const editForm = reactive({
  account: '',
  display_name: '',
  nickname: '',
  phone: '',
  student_no: '',
  password: '',
  is_active: true,
  created_by_teacher_id: '' as string,
})

const load = async () => {
  const data = await adminApi.listUsers({ role: roleFilter.value || undefined, keyword: keyword.value || undefined, page: 1, page_size: 50 })
  users.value = data.items
}

const openEdit = async (user: AdminUserListItem) => {
  editUser.value = user
  editError.value = ''
  editForm.account = user.account
  editForm.display_name = user.real_name ?? user.display_name ?? ''
  editForm.nickname = user.nickname ?? ''
  editForm.phone = user.role === 'parent' ? (user.phone ?? user.account) : (user.phone ?? '')
  editForm.student_no = user.student_no ?? ''
  editForm.password = ''
  editForm.is_active = user.is_active
  editForm.created_by_teacher_id = ''
  if (user.role === 'student') {
    try {
      const rel = await adminApi.getUserRelations(user.id)
      editForm.created_by_teacher_id =
        rel.teacher?.id != null ? String(rel.teacher.id) : ''
    } catch {
      editForm.created_by_teacher_id = ''
    }
  }
}

const closeEdit = () => {
  editUser.value = null
  editError.value = ''
}

const saveEdit = async () => {
  if (!editUser.value) return
  editError.value = ''
  editSubmitting.value = true
  try {
    const payload: AdminUserUpdatePayload = {
      display_name: editForm.display_name.trim() || undefined,
      nickname: editForm.nickname.trim() || undefined,
      is_active: editForm.is_active,
    }
    if (editUser.value.role === 'parent') {
      const phone = editForm.phone.trim()
      if (!phone) {
        editError.value = '请输入手机号'
        editSubmitting.value = false
        return
      }
      payload.phone = phone
    } else {
      const account = editForm.account.trim()
      if (!account) {
        editError.value = '请输入账号'
        editSubmitting.value = false
        return
      }
      payload.account = account
      if (editUser.value.role === 'teacher') {
        payload.phone = editForm.phone.trim() || undefined
      }
    }
    if (editUser.value.role === 'student') {
      payload.student_no = editForm.student_no.trim() || undefined
      const rawTeacher = editForm.created_by_teacher_id.trim()
      payload.created_by_teacher_id = rawTeacher ? Number(rawTeacher) : null
    }
    if (editForm.password.trim()) {
      payload.password = editForm.password.trim()
    }
    await adminApi.updateUser(editUser.value.id, payload)
    toast.success('用户信息已更新')
    closeEdit()
    await load()
  } catch (err) {
    editError.value = err instanceof Error ? err.message : '保存失败'
  } finally {
    editSubmitting.value = false
  }
}

const toggleActive = async (user: AdminUserListItem) => {
  await adminApi.updateUser(user.id, { is_active: !user.is_active })
  toast.success('已更新')
  await load()
}

const createUser = async () => {
  const { role, account, phone, password, display_name } = createForm
  try {
    if (role === 'student') {
      const name = display_name.trim()
      if (!name) {
        toast.error('请输入学生真实姓名')
        return
      }
      const created = await adminApi.createUser({ role: 'student', display_name: name })
      toast.success(`创建成功：账号 ${created.account}，默认密码 123456`)
    } else if (role === 'parent') {
      if (!phone.trim()) {
        toast.error('请输入家长手机号')
        return
      }
      if (!password || password.length < 6) {
        toast.error('请填写至少 6 位密码')
        return
      }
      await adminApi.createUser({
        role,
        account: phone.trim(),
        phone: phone.trim(),
        password,
        display_name,
      })
      toast.success('创建成功')
    } else {
      if (!account.trim()) {
        toast.error('请输入账号')
        return
      }
      if (!password || password.length < 6) {
        toast.error('请填写至少 6 位密码')
        return
      }
      await adminApi.createUser({
        role,
        account: account.trim(),
        password,
        display_name: display_name.trim() || undefined,
      })
      toast.success('创建成功')
    }
    showCreate.value = false
    createForm.account = ''
    createForm.phone = ''
    createForm.password = ''
    createForm.display_name = ''
    await load()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '创建失败')
  }
}

const loadRelations = async (userId: number) => {
  relationsLoading.value = true
  try {
    relations.value = await adminApi.getUserRelations(userId)
    teacherIdInput.value = relations.value.teacher?.id ?? null
    if (relationsUser.value?.role === 'student') {
      bindStudentId.value = userId
    } else if (relationsUser.value?.role === 'parent') {
      bindParentId.value = userId
    }
  } catch (err) {
    toast.error(err instanceof Error ? err.message : '加载关系失败')
  } finally {
    relationsLoading.value = false
  }
}

const openRelations = async (user: AdminUserListItem) => {
  relationsUser.value = user
  relations.value = null
  bindParentId.value = user.role === 'parent' ? user.id : null
  bindStudentId.value = user.role === 'student' ? user.id : null
  await loadRelations(user.id)
}

const closeRelations = () => {
  relationsUser.value = null
  relations.value = null
}

const unbind = async (bindingId: number) => {
  if (!confirm('确定解绑该关系？')) return
  await adminApi.unbindParentStudent(bindingId)
  toast.success('已解绑')
  if (relationsUser.value) await loadRelations(relationsUser.value.id)
}

const promptRebindParent = async (binding: { id: number }) => {
  const raw = window.prompt('请输入新家长的用户 ID')
  if (!raw?.trim()) return
  const newParentId = Number(raw)
  if (Number.isNaN(newParentId)) {
    toast.error('ID 无效')
    return
  }
  await adminApi.rebindParentStudent(binding.id, newParentId)
  toast.success('换绑成功')
  if (relationsUser.value) await loadRelations(relationsUser.value.id)
}

const createBinding = async () => {
  if (!bindParentId.value || !bindStudentId.value) {
    toast.error('请填写家长 ID 与学生 ID')
    return
  }
  await adminApi.bindParentStudent(bindParentId.value, bindStudentId.value)
  toast.success('绑定成功')
  if (relationsUser.value) await loadRelations(relationsUser.value.id)
}

const saveTeacher = async () => {
  if (!relationsUser.value || relationsUser.value.role !== 'student') return
  if (!teacherIdInput.value) {
    toast.error('请输入教师 ID')
    return
  }
  await adminApi.setStudentTeacher(relationsUser.value.id, teacherIdInput.value)
  toast.success('负责教师已更新')
  await loadRelations(relationsUser.value.id)
}

const clearTeacher = async () => {
  if (!relationsUser.value || relationsUser.value.role !== 'student') return
  if (!confirm('确定解除该学生与教师的归属关系？')) return
  await adminApi.setStudentTeacher(relationsUser.value.id, null)
  toast.success('已解绑教师')
  await loadRelations(relationsUser.value.id)
}

useDebouncedWatch(keyword, () => {
  void load()
})

onMounted(load)
</script>
