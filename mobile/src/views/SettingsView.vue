<template>
  <section class="settings-page">
    <div class="settings-cell profile-cell">
      <button type="button" class="settings-avatar" aria-label="切换头像" @click="openAvatarDialog">
        <img :src="avatarImage" alt="用户头像" />
      </button>
      <div class="settings-profile-main">
        <strong>{{ displayName }}</strong>
        <span>{{ accountLabel }}</span>
      </div>
    </div>

    <div class="settings-list">
      <button type="button" class="settings-cell settings-row" @click="profileDialogVisible = true">
        <span>用户名</span>
        <span>{{ displayName }}</span>
      </button>
      <button type="button" class="settings-cell settings-row" @click="openPresetDialog">
        <span>预设管理</span>
        <span>{{ presetSummaryLabel }}</span>
      </button>
      <button type="button" class="settings-cell settings-row" @click="openRecurringDialog">
        <span>固定支出</span>
        <span>{{ recurringSummary }}</span>
      </button>
      <button type="button" class="settings-cell settings-row" @click="categoryDialogVisible = true">
        <span>分类管理</span>
        <span>{{ categorySummary }}</span>
      </button>
      <DataTransferButton @imported="handleImported" />
      <button type="button" class="settings-cell settings-row danger-row" @click="logout">
        <span>退出登录</span>
      </button>
      <button type="button" class="settings-cell settings-row danger-row" @click="deleteAccount">
        <span>注销用户</span>
      </button>
    </div>

    <el-dialog
      v-model="profileDialogVisible"
      title="修改用户名"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model.trim="profileForm.username" maxlength="80" placeholder="请输入用户名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="presetDialogVisible"
      title="预设管理"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="每月工资金额">
          <el-input-number
            v-model="salaryForm.default_salary_income"
            :min="0"
            :precision="2"
            :step="500"
            controls-position="right"
            class="full-width"
          />
        </el-form-item>
        <el-form-item label="初始总余额">
          <el-input-number
            v-model="openingForm.opening_balance_amount"
            :precision="2"
            :step="100"
            controls-position="right"
            class="full-width"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="clearOpeningBalance">清除初始余额</el-button>
        <el-button @click="presetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="savePresetSettings">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="recurringDialogVisible"
      title="固定支出"
      width="min(460px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <div class="recurring-manager">
        <div class="recurring-form">
          <el-input v-model.trim="recurringForm.name" maxlength="80" placeholder="名称，例如：视频会员、房贷" />
          <el-input-number
            v-model="recurringForm.amount"
            :min="0"
            :precision="2"
            :step="50"
            controls-position="right"
            class="full-width"
          />
          <el-select v-model="recurringForm.category" placeholder="分类" class="full-width">
            <el-option v-for="item in allManagedCategories" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-date-picker
            v-model="recurringForm.start_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="扣费日期"
            :editable="false"
            class="full-width"
          />
          <div class="recurring-enabled">
            <span>按年扣费</span>
            <button
              type="button"
              class="smooth-switch"
              :class="{ active: recurringForm.yearly }"
              role="switch"
              :aria-checked="recurringForm.yearly"
              @click="recurringForm.yearly = !recurringForm.yearly"
            >
              <i></i>
            </button>
          </div>
          <div class="recurring-enabled">
            <span>开启项目</span>
            <button
              type="button"
              class="smooth-switch"
              :class="{ active: recurringForm.enabled }"
              role="switch"
              :aria-checked="recurringForm.enabled"
              @click="recurringForm.enabled = !recurringForm.enabled"
            >
              <i></i>
            </button>
          </div>
          <el-button type="primary" class="full-width" :loading="recurringSaving" @click="saveRecurring">
            {{ editingRecurringId ? '保存固定支出' : '添加固定支出' }}
          </el-button>
          <el-button v-if="editingRecurringId" class="full-width" @click="resetRecurringForm">取消编辑</el-button>
        </div>

        <div class="recurring-list">
          <div v-for="item in recurringExpenses" :key="item.id" class="recurring-row">
            <div>
              <strong>{{ item.name }}</strong>
              <span>{{ recurringScheduleLabel(item) }} · {{ item.category }} · {{ currency(item.amount) }}</span>
            </div>
            <div class="recurring-actions">
              <el-switch :model-value="item.enabled" @change="toggleRecurring(item)" />
              <el-button size="small" @click="editRecurring(item)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteRecurring(item)">删除</el-button>
            </div>
          </div>
          <el-empty v-if="!recurringExpenses.length" description="暂无固定支出" :image-size="80" />
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="categoryDialogVisible"
      title="分类管理"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <div class="category-manager">
        <div class="category-add-row">
          <el-input v-model.trim="newCategoryName" maxlength="12" placeholder="例如：宠物、停车、咖啡" />
          <el-button type="primary" @click="addCategory">添加</el-button>
        </div>
        <div class="category-color-palette" aria-label="分类颜色">
          <button
            v-for="color in categoryColorOptions"
            :key="color"
            type="button"
            class="category-color-dot"
            :class="{ active: newCategoryColor === color }"
            :style="{ '--category-create-color': color }"
            :aria-label="`选择颜色 ${color}`"
            @click="newCategoryColor = color"
          />
        </div>
        <div class="icon-picker">
          <button
            v-for="item in categoryIconOptions"
            :key="item.value"
            type="button"
            class="icon-picker-button"
            :class="{ active: newCategoryIcon === item.value }"
            :title="item.label"
            @click="newCategoryIcon = item.value"
          >
            <el-icon><component :is="item.component" /></el-icon>
          </button>
        </div>

        <div class="category-toggle-list">
          <div
            v-for="item in allManagedCategories"
            :key="item.value"
            class="category-toggle-row"
            :class="{ dragging: draggedCategoryValue === item.value }"
            :data-category-value="item.value"
          >
            <span class="category-toggle-name">
              <i :style="{ color: item.color }">
                <el-icon><component :is="categoryIconComponent(item.icon)" /></el-icon>
              </i>
              <span>{{ item.label }}</span>
              <em v-if="item.custom">自定义</em>
            </span>
            <span class="category-toggle-actions">
              <button
                type="button"
                class="category-drag-handle"
                aria-label="拖动调整顺序"
                @pointerdown="startCategoryDrag(item.value, $event)"
              >
                <el-icon><Sort /></el-icon>
              </button>
              <el-switch :model-value="!isCategoryHidden(item.value)" @change="toggleCategory(item.value)" />
              <button
                v-if="item.custom"
                type="button"
                class="category-remove-button"
                aria-label="删除分类"
                @click="removeCategory(item.value)"
              >
                ×
              </button>
            </span>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="avatarDialogVisible"
      title="头像设置"
      width="min(420px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <div class="avatar-editor">
        <div class="avatar-preview">
          <img :src="previewAvatarImage" alt="头像预览" />
        </div>
        <div class="avatar-choice-grid">
          <button
            v-for="item in defaultAvatarOptions"
            :key="item.value"
            type="button"
            class="avatar-choice"
            :class="{ active: avatarForm.mode === 'preset' && avatarForm.preset === item.value }"
            @click="selectDefaultAvatar(item.value)"
          >
            <img :src="item.image" :alt="item.label" />
            <span>{{ item.label }}</span>
          </button>
        </div>
        <div class="avatar-actions">
          <el-button @click="chooseAvatarFile">上传图片</el-button>
          <el-button @click="selectDefaultAvatar(defaultAvatarOptions[0].value)">使用默认</el-button>
        </div>
        <input ref="avatarFileInput" type="file" accept="image/*" class="avatar-file-input" @change="handleAvatarFile" />
      </div>
      <template #footer>
        <el-button @click="avatarDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAvatar">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, h, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Sort } from '@element-plus/icons-vue'
import DataTransferButton from '../components/DataTransferButton.vue'
import {
  allExpenseCategories,
  buildCustomCategory,
  expenseCategories,
  loadCategoryOrder,
  loadCategoryColors,
  loadCategoryPreferenceFromServer,
  loadCustomCategories,
  loadHiddenCategoryValues,
  saveCategoryOrder,
  saveCategoryColors,
  saveCategoryPreferenceToServer,
  saveCustomCategories,
  saveHiddenCategoryValues
} from '../constants/categories'
import { categoryIconComponent, categoryIconOptions } from '../constants/categoryIcons'
import { useAuthStore } from '../stores/auth'
import { notifyFinanceDataChanged } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'
import { loadAvatarPreference, saveAvatarPreference } from '../utils/userPreferences'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const profileDialogVisible = ref(false)
const presetDialogVisible = ref(false)
const categoryDialogVisible = ref(false)
const avatarDialogVisible = ref(false)
const recurringDialogVisible = ref(false)
const avatarFileInput = ref(null)
const newCategoryName = ref('')
const newCategoryIcon = ref('MoreFilled')
const newCategoryColor = ref('#0ea5e9')
const customCategories = ref(loadCustomCategories())
const hiddenCategoryValues = ref(loadHiddenCategoryValues())
const categoryOrder = ref(loadCategoryOrder())
const categoryColors = ref(loadCategoryColors())
const draggedCategoryValue = ref('')
const avatarPreference = ref(loadAvatarPreference())
const profileForm = reactive({
  username: ''
})
const salaryForm = reactive({
  default_salary_income: 0
})
const openingForm = reactive({
  opening_balance_amount: 0
})
const presetOriginalOpeningBalance = ref(0)
const avatarForm = reactive({
  mode: 'preset',
  preset: 'default-cat',
  image: ''
})
const recurringExpenses = ref([])
const recurringSaving = ref(false)
const editingRecurringId = ref(null)
const recurringForm = reactive({
  name: '',
  amount: null,
  category: '其他',
  start_date: dayjs().format('YYYY-MM-DD'),
  yearly: false,
  enabled: true
})
const defaultAvatarOptions = [
  { value: 'default-cat', label: '蓝眼猫', image: publicAsset('default-avatar-cat.jpg') },
  { value: 'default-dog', label: '白狗狗', image: publicAsset('default-avatar-dog.jpg') },
  { value: 'black-cat', label: '黑猫', image: publicAsset('default-avatar-black-cat.jpg') }
]
const categoryColorOptions = [
  '#0ea5e9',
  '#22c55e',
  '#f97316',
  '#db2777',
  '#9333ea',
  '#14b8a6',
  '#e11d48',
  '#dc2626',
  '#0891b2',
  '#64748b'
]
const displayName = computed(() => authStore.user?.username || authStore.user?.email || '未命名用户')
const accountLabel = computed(() => authStore.user?.email || '')
const avatarMode = computed(() => (avatarPreference.value.mode === 'custom' && avatarPreference.value.image ? 'custom' : 'preset'))
const selectedDefaultAvatar = computed(() => {
  return defaultAvatarOptions.find((item) => item.value === avatarPreference.value.preset) || defaultAvatarOptions[0]
})
const avatarImage = computed(() => {
  if (avatarMode.value === 'custom') return avatarPreference.value.image || ''
  return selectedDefaultAvatar.value.image
})
const previewDefaultAvatar = computed(() => {
  return defaultAvatarOptions.find((item) => item.value === avatarForm.preset) || defaultAvatarOptions[0]
})
const previewAvatarImage = computed(() => {
  if (avatarForm.mode === 'custom') return avatarForm.image
  return previewDefaultAvatar.value.image
})
const defaultSalary = computed(() => Number(authStore.user?.default_salary_income || 0))
const defaultSalaryLabel = computed(() => (defaultSalary.value > 0 ? currency(defaultSalary.value) : '未设置'))
const openingBalanceLabel = computed(() => {
  const amount = Number(authStore.user?.opening_balance_amount || 0)
  return amount ? currency(amount) : '未设置'
})
const presetSummaryLabel = computed(() => {
  return `工资 ${defaultSalaryLabel.value} · 余额 ${openingBalanceLabel.value}`
})
const allManagedCategories = computed(() => {
  categoryOrder.value
  customCategories.value
  hiddenCategoryValues.value
  categoryColors.value
  return allExpenseCategories({ includeHidden: true })
})
const recurringSummary = computed(() => {
  const enabledCount = recurringExpenses.value.filter((item) => item.enabled).length
  return enabledCount ? `${enabledCount} 个已开启` : '未设置'
})
const categorySummary = computed(() => {
  const hiddenCount = hiddenCategoryValues.value.length
  const customCount = customCategories.value.length
  return hiddenCount ? `${customCount} 个自定义，隐藏 ${hiddenCount} 个` : `${customCount} 个自定义`
})

watch(
  () => authStore.user?.username,
  (value) => {
    profileForm.username = value || ''
  },
  { immediate: true }
)

watch(
  () => authStore.user?.default_salary_income,
  (value) => {
    salaryForm.default_salary_income = Number(value || 0)
  },
  { immediate: true }
)

watch(
  () => authStore.user?.opening_balance_amount,
  (amountValue) => {
    openingForm.opening_balance_amount = Number(amountValue || 0)
  },
  { immediate: true }
)

function handleImported() {
  ElMessage.success('数据已更新')
}

function openPresetDialog() {
  salaryForm.default_salary_income = Number(authStore.user?.default_salary_income || 0)
  openingForm.opening_balance_amount = Number(authStore.user?.opening_balance_amount || 0)
  presetOriginalOpeningBalance.value = Number(authStore.user?.opening_balance_amount || 0)
  presetDialogVisible.value = true
}

async function openRecurringDialog() {
  await loadRecurringExpenses()
  resetRecurringForm()
  recurringDialogVisible.value = true
}

async function loadRecurringExpenses() {
  const { data } = await http.get('/recurring-expenses')
  recurringExpenses.value = data
}

function resetRecurringForm() {
  editingRecurringId.value = null
  recurringForm.name = ''
  recurringForm.amount = null
  recurringForm.category = allManagedCategories.value[0]?.value || '其他'
  recurringForm.start_date = dayjs().format('YYYY-MM-DD')
  recurringForm.yearly = false
  recurringForm.enabled = true
}

function recurringPayload() {
  const chargeDate = dayjs(recurringForm.start_date || dayjs().format('YYYY-MM-DD'))
  const isYearly = Boolean(recurringForm.yearly)
  return {
    name: recurringForm.name.trim(),
    amount: Number(recurringForm.amount || 0),
    category: recurringForm.category,
    frequency: isYearly ? 'yearly' : 'monthly',
    day_of_month: chargeDate.date(),
    month_of_year: isYearly ? chargeDate.month() + 1 : null,
    start_date: chargeDate.format('YYYY-MM-DD'),
    enabled: recurringForm.enabled
  }
}

async function saveRecurring() {
  const payload = recurringPayload()
  if (!payload.name) {
    ElMessage.error('请输入固定支出名称')
    return
  }
  if (payload.amount <= 0) {
    ElMessage.error('请输入固定支出金额')
    return
  }

  recurringSaving.value = true
  try {
    if (editingRecurringId.value) {
      await http.put(`/recurring-expenses/${editingRecurringId.value}`, payload)
      ElMessage.success('固定支出已保存')
    } else {
      await http.post('/recurring-expenses', payload)
      ElMessage.success('固定支出已添加')
    }
    await loadRecurringExpenses()
    notifyFinanceDataChanged()
    resetRecurringForm()
  } finally {
    recurringSaving.value = false
  }
}

function editRecurring(item) {
  editingRecurringId.value = item.id
  recurringForm.name = item.name
  recurringForm.amount = Number(item.amount || 0)
  recurringForm.category = item.category
  recurringForm.start_date = normalizedRecurringDate(item)
  recurringForm.yearly = item.frequency === 'yearly'
  recurringForm.enabled = item.enabled
}

async function toggleRecurring(item) {
  await http.put(`/recurring-expenses/${item.id}`, { enabled: !item.enabled })
  await loadRecurringExpenses()
  notifyFinanceDataChanged()
}

async function deleteRecurring(item) {
  const confirmed = await ElMessageBox.confirm(
    `确定删除“${item.name}”吗？删除后不会再自动统计。`,
    '删除固定支出',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    }
  ).catch(() => false)
  if (!confirmed) return
  await http.delete(`/recurring-expenses/${item.id}`)
  ElMessage.success('固定支出已删除')
  await loadRecurringExpenses()
  notifyFinanceDataChanged()
}

function recurringScheduleLabel(item) {
  const date = normalizedRecurringDate(item)
  if (item.frequency === 'yearly') {
    return `每年 ${dayjs(date).format('M月D日')} 扣费`
  }
  return `每月 ${dayjs(date).date()}日扣费 · 自 ${date} 起`
}

function normalizedRecurringDate(item) {
  const baseDate = dayjs(item.start_date || dayjs().format('YYYY-MM-DD'))
  if (!baseDate.isValid()) return dayjs().format('YYYY-MM-DD')
  const month = item.frequency === 'yearly' ? Number(item.month_of_year || baseDate.month() + 1) : baseDate.month() + 1
  const day = Number(item.day_of_month || baseDate.date())
  return baseDate.month(month - 1).date(Math.min(day, baseDate.month(month - 1).daysInMonth())).format('YYYY-MM-DD')
}

function refreshCategoryState() {
  customCategories.value = loadCustomCategories()
  hiddenCategoryValues.value = loadHiddenCategoryValues()
  categoryOrder.value = loadCategoryOrder()
  categoryColors.value = loadCategoryColors()
}

async function persistCategoryPreference() {
  try {
    await saveCategoryPreferenceToServer()
    refreshCategoryState()
  } catch {
    refreshCategoryState()
  }
}

async function addCategory() {
  const name = newCategoryName.value.trim()
  if (!name) {
    ElMessage.error('请输入分类名称')
    return
  }
  const exists = [...expenseCategories, ...customCategories.value].some((item) => item.value === name)
  if (exists) {
    ElMessage.error('分类已存在')
    return
  }
  customCategories.value = [
    ...customCategories.value,
    buildCustomCategory(name, customCategories.value.length, newCategoryIcon.value, newCategoryColor.value)
  ]
  saveCustomCategories(customCategories.value)
  categoryOrder.value = [...allManagedCategories.value.map((item) => item.value), name]
  saveCategoryOrder(categoryOrder.value)
  newCategoryName.value = ''
  newCategoryIcon.value = 'MoreFilled'
  newCategoryColor.value = '#0ea5e9'
  await persistCategoryPreference()
  ElMessage.success('分类已添加')
}

async function removeCategory(value) {
  const confirmed = await ElMessageBox.confirm(
    '确定删除这个分类吗？已有明细不会一起删除。',
    '删除分类',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    }
  ).catch(() => false)
  if (!confirmed) return
  customCategories.value = customCategories.value.filter((item) => item.value !== value)
  saveCustomCategories(customCategories.value)
  categoryOrder.value = categoryOrder.value.filter((item) => item !== value)
  saveCategoryOrder(categoryOrder.value)
  hiddenCategoryValues.value = hiddenCategoryValues.value.filter((item) => item !== value)
  saveHiddenCategoryValues(hiddenCategoryValues.value)
  const nextColors = { ...categoryColors.value }
  delete nextColors[value]
  categoryColors.value = nextColors
  saveCategoryColors(nextColors)
  await persistCategoryPreference()
}

function reorderCategories(fromValue, toValue) {
  const values = allManagedCategories.value.map((item) => item.value)
  const index = values.indexOf(fromValue)
  const targetIndex = values.indexOf(toValue)
  if (index < 0 || targetIndex < 0 || index === targetIndex) return
  const next = [...values]
  const [item] = next.splice(index, 1)
  next.splice(targetIndex, 0, item)
  categoryOrder.value = next
  saveCategoryOrder(next)
}

function startCategoryDrag(value, event) {
  if (event.target?.closest?.('.category-toggle-actions') && !event.target?.closest?.('.category-drag-handle')) return
  draggedCategoryValue.value = value
  event.preventDefault()
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  window.addEventListener('pointermove', moveCategoryDrag)
  window.addEventListener('pointerup', stopCategoryDrag, { once: true })
  window.addEventListener('pointercancel', stopCategoryDrag, { once: true })
}

function moveCategoryDrag(event) {
  if (!draggedCategoryValue.value) return
  event.preventDefault()
  const target = document.elementFromPoint(event.clientX, event.clientY)?.closest?.('[data-category-value]')
  const targetValue = target?.dataset?.categoryValue
  if (!targetValue || targetValue === draggedCategoryValue.value) return
  reorderCategories(draggedCategoryValue.value, targetValue)
}

async function stopCategoryDrag() {
  window.removeEventListener('pointermove', moveCategoryDrag)
  if (draggedCategoryValue.value) {
    await persistCategoryPreference()
  }
  draggedCategoryValue.value = ''
}

function isCategoryHidden(value) {
  return hiddenCategoryValues.value.includes(value)
}

async function toggleCategory(value) {
  if (isCategoryHidden(value)) {
    hiddenCategoryValues.value = hiddenCategoryValues.value.filter((item) => item !== value)
  } else {
    const visibleCount = allManagedCategories.value.filter((item) => !isCategoryHidden(item.value)).length
    if (visibleCount <= 1) {
      ElMessage.error('至少保留一个可用分类')
      return
    }
    hiddenCategoryValues.value = [...hiddenCategoryValues.value, value]
  }
  saveHiddenCategoryValues(hiddenCategoryValues.value)
  await persistCategoryPreference()
}

function openAvatarDialog() {
  avatarForm.mode = avatarMode.value
  avatarForm.preset = avatarPreference.value.preset || defaultAvatarOptions[0].value
  avatarForm.image = avatarPreference.value.image || ''
  avatarDialogVisible.value = true
}

function publicAsset(path) {
  return `${import.meta.env.BASE_URL || '/'}${path}`.replace(/\/{2,}/g, '/')
}

function selectDefaultAvatar(value) {
  avatarForm.mode = 'preset'
  avatarForm.preset = value
  avatarForm.image = ''
}

function chooseAvatarFile() {
  avatarFileInput.value?.click()
}

function handleAvatarFile(event) {
  const [file] = event.target.files || []
  if (!file) return
  if (file.size > 1024 * 1024) {
    ElMessage.error('头像图片不要超过 1MB')
    event.target.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    avatarForm.mode = 'custom'
    avatarForm.image = String(reader.result || '')
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function saveAvatar() {
  avatarPreference.value = {
    mode: avatarForm.mode,
    preset: avatarForm.preset,
    image: avatarForm.mode === 'custom' ? avatarForm.image : ''
  }
  saveAvatarPreference(avatarPreference.value)
  avatarDialogVisible.value = false
  ElMessage.success('头像已保存')
}

async function saveProfile() {
  const username = profileForm.username.trim()
  if (!username) {
    ElMessage.error('请输入用户名')
    return
  }

  saving.value = true
  try {
    await authStore.updateProfile({ username })
    profileDialogVisible.value = false
    ElMessage.success('用户名已保存')
  } finally {
    saving.value = false
  }
}

async function savePresetSettings() {
  const salaryAmount = Number(salaryForm.default_salary_income || 0)
  const balanceAmount = Number(openingForm.opening_balance_amount || 0)
  if (salaryAmount < 0) {
    ElMessage.error('预设工资不能小于 0')
    return
  }

  saving.value = true
  try {
    const payload = {
      default_salary_income: salaryAmount,
      opening_balance_date: null,
      opening_balance_amount: balanceAmount
    }
    await authStore.updateProfile(payload)
    presetOriginalOpeningBalance.value = balanceAmount
    presetDialogVisible.value = false
    notifyFinanceDataChanged()
    ElMessage.success('预设管理已保存')
  } finally {
    saving.value = false
  }
}

async function clearOpeningBalance() {
  saving.value = true
  try {
    await authStore.updateProfile({
      opening_balance_date: null,
      opening_balance_amount: 0
    })
    openingForm.opening_balance_amount = 0
    presetOriginalOpeningBalance.value = 0
    presetDialogVisible.value = false
    notifyFinanceDataChanged()
    ElMessage.success('初始总余额已清除')
  } finally {
    saving.value = false
  }
}

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}

async function deleteAccount() {
  await ElMessageBox.confirm(
    h('div', { class: 'delete-account-warning' }, [
      h('p', '注销用户会永久删除当前账号，请确认你已经了解以下风险：'),
      h('ul', [
        h('li', '该账号下的收入、支出、固定支出、额外收入等账本数据会被删除。'),
        h('li', '概览、记录、分析图表中的历史统计会同步清空。'),
        h('li', '本机保存的登录用户信息会移除，注销后无法恢复。')
      ]),
      h('p', '这个操作不可撤销。')
    ]),
    '注销用户',
    {
      type: 'warning',
      confirmButtonText: '我已了解，注销用户',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    }
  )
  const deletedEmail = authStore.user?.email
  await http.delete('/auth/me')
  ElMessage.success('用户已注销')
  if (deletedEmail) {
    const userListKey = 'finance_mobile_saved_users'
    try {
      const users = JSON.parse(localStorage.getItem(userListKey) || '[]')
      localStorage.setItem(
        userListKey,
        JSON.stringify((Array.isArray(users) ? users : []).filter((item) => item?.email !== deletedEmail))
      )
    } catch {
      localStorage.removeItem(userListKey)
    }
  }
  authStore.logout()
  router.push({ name: 'login' })
}

onMounted(async () => {
  await Promise.all([
    loadRecurringExpenses(),
    loadCategoryPreferenceFromServer()
      .then(refreshCategoryState)
      .catch(() => {
        refreshCategoryState()
      })
  ])
})

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', moveCategoryDrag)
  window.removeEventListener('pointerup', stopCategoryDrag)
  window.removeEventListener('pointercancel', stopCategoryDrag)
})
</script>
