<template>
  <section class="settings-page">
    <el-card class="profile-card">
      <div class="settings-profile-row">
        <div class="settings-avatar">
          <img v-if="avatarImage" :src="avatarImage" alt="用户头像" />
          <span v-else>{{ avatarText }}</span>
        </div>
        <div class="settings-profile-main">
          <strong>{{ displayName }}</strong>
          <span>{{ accountLabel }}</span>
        </div>
      </div>
    </el-card>

    <el-card>
      <template #header>账号设置</template>
      <div class="settings-list">
        <button type="button" class="settings-cell settings-row" @click="profileDialogVisible = true">
          <span>用户名</span>
          <span>{{ displayName }}</span>
        </button>
        <button type="button" class="settings-cell settings-row" @click="openOpeningDialog">
          <span>期初账</span>
          <span>{{ openingBalanceLabel }}</span>
        </button>
        <button type="button" class="settings-cell settings-row" @click="openRecurringDialog">
          <span>固定支出</span>
          <span>{{ recurringSummary }}</span>
        </button>
        <button type="button" class="settings-cell settings-row" @click="openAvatarDialog">
          <span>头像</span>
          <span>{{ avatarSummary }}</span>
        </button>
        <button type="button" class="settings-cell settings-row danger-row" @click="logout">
          <span>退出登录</span>
        </button>
      </div>
    </el-card>

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
      v-model="openingDialogVisible"
      title="期初账"
      width="min(460px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="期初日期">
          <el-date-picker
            v-model="openingForm.opening_balance_date"
            type="date"
            value-format="YYYY-MM-DD"
            :editable="false"
            placeholder="选择开始统计的日期"
            class="full-width"
          />
        </el-form-item>
        <el-form-item label="期初金额">
          <el-input-number
            v-model="openingForm.opening_balance_amount"
            :precision="2"
            :step="100"
            controls-position="right"
            class="full-width"
          />
        </el-form-item>
      </el-form>
      <p class="settings-dialog-tip">保存后，概览和分析只统计期初日期之后的数据；明细记录仍会保留。</p>
      <template #footer>
        <el-button @click="clearOpeningBalance">清除期初账</el-button>
        <el-button @click="openingDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveOpeningBalance">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="recurringDialogVisible"
      title="固定支出"
      width="min(520px, calc(100vw - 24px))"
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
          <div class="recurring-period-row">
            <el-select v-model="recurringForm.frequency" class="full-width">
              <el-option label="每月" value="monthly" />
              <el-option label="每年" value="yearly" />
            </el-select>
            <el-select v-if="recurringForm.frequency === 'yearly'" v-model="recurringForm.month_of_year" class="full-width">
              <el-option v-for="month in 12" :key="month" :label="`${month}月`" :value="month" />
            </el-select>
            <el-select v-model="recurringForm.day_of_month" class="full-width">
              <el-option v-for="day in 31" :key="day" :label="`${day}日`" :value="day" />
            </el-select>
          </div>
          <label class="recurring-enabled">
            <span>开启项目</span>
            <el-switch v-model="recurringForm.enabled" />
          </label>
          <div class="recurring-form-actions">
            <el-button type="primary" :loading="recurringSaving" @click="saveRecurring">
              {{ editingRecurringId ? '保存固定支出' : '添加固定支出' }}
            </el-button>
            <el-button v-if="editingRecurringId" @click="resetRecurringForm">取消编辑</el-button>
          </div>
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
      v-model="avatarDialogVisible"
      title="头像设置"
      width="min(460px, calc(100vw - 24px))"
      class="finance-dialog"
      destroy-on-close
    >
      <div class="avatar-editor">
        <div class="avatar-preview">
          <img v-if="previewAvatarImage" :src="previewAvatarImage" alt="头像预览" />
          <span v-else>{{ previewAvatarText }}</span>
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
          <button
            type="button"
            class="avatar-choice text-avatar-choice"
            :class="{ active: avatarForm.mode === 'text' }"
            @click="useTextAvatar"
          >
            <b>{{ previewAvatarText }}</b>
            <span>文字头像</span>
          </button>
        </div>
        <el-input v-if="avatarForm.mode === 'text'" v-model.trim="avatarForm.text" maxlength="2" placeholder="头像文字，例如：账" />
        <div class="avatar-actions">
          <el-button @click="chooseAvatarFile">上传图片</el-button>
          <el-button @click="useTextAvatar">使用文字</el-button>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { expenseCategories } from '../constants/categories'
import { useAuthStore } from '../stores/auth'
import { notifyFinanceDataChanged } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'
import { loadAvatarPreference, saveAvatarPreference } from '../utils/userPreferences'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const profileDialogVisible = ref(false)
const openingDialogVisible = ref(false)
const recurringDialogVisible = ref(false)
const avatarDialogVisible = ref(false)
const avatarFileInput = ref(null)
const avatarPreference = ref(loadAvatarPreference())
const profileForm = reactive({
  username: ''
})
const openingForm = reactive({
  opening_balance_date: '',
  opening_balance_amount: 0
})
const avatarForm = reactive({
  mode: 'preset',
  preset: 'default-cat',
  text: '',
  image: ''
})
const recurringExpenses = ref([])
const recurringSaving = ref(false)
const editingRecurringId = ref(null)
const recurringForm = reactive({
  name: '',
  amount: null,
  category: '其他',
  frequency: 'monthly',
  day_of_month: 1,
  month_of_year: 1,
  enabled: true
})
const defaultAvatarOptions = [
  { value: 'default-cat', label: '默认头像', image: publicAsset('default-cat-avatar.jpg') }
]

const defaultDisplayName = computed(() => {
  const userNumber = (((Number(authStore.user?.id) || 1) - 1) % 199) + 1
  return `用户${userNumber}`
})
const displayName = computed(() => authStore.user?.username || defaultDisplayName.value)
const accountLabel = computed(() => authStore.user?.email || '')
const openingBalanceLabel = computed(() => {
  if (!authStore.user?.opening_balance_date) return '未设置'
  return `${authStore.user.opening_balance_date} · ${currency(authStore.user.opening_balance_amount || 0)}`
})
const avatarMode = computed(() => avatarPreference.value.mode || (avatarPreference.value.image ? 'custom' : 'preset'))
const selectedDefaultAvatar = computed(() => {
  return defaultAvatarOptions.find((item) => item.value === avatarPreference.value.preset) || defaultAvatarOptions[0]
})
const avatarImage = computed(() => {
  if (avatarMode.value === 'custom') return avatarPreference.value.image || ''
  if (avatarMode.value === 'preset') return selectedDefaultAvatar.value.image
  return ''
})
const avatarSummary = computed(() => {
  if (avatarMode.value === 'custom') return '已上传'
  if (avatarMode.value === 'text') return '文字头像'
  return selectedDefaultAvatar.value.label
})
const avatarText = computed(() => String(displayName.value || '账').slice(0, 2).toUpperCase())
const previewAvatarText = computed(() => String(avatarForm.text || displayName.value || '账').slice(0, 2).toUpperCase())
const previewDefaultAvatar = computed(() => {
  return defaultAvatarOptions.find((item) => item.value === avatarForm.preset) || defaultAvatarOptions[0]
})
const previewAvatarImage = computed(() => {
  if (avatarForm.mode === 'custom') return avatarForm.image
  if (avatarForm.mode === 'preset') return previewDefaultAvatar.value.image
  return ''
})
const allManagedCategories = computed(() => expenseCategories)
const recurringSummary = computed(() => {
  const enabledCount = recurringExpenses.value.filter((item) => item.enabled).length
  return enabledCount ? `${enabledCount} 个已开启` : '未设置'
})

watch(
  () => authStore.user?.username,
  (value) => {
    profileForm.username = value || ''
  },
  { immediate: true }
)

watch(
  () => [authStore.user?.opening_balance_date, authStore.user?.opening_balance_amount],
  ([dateValue, amountValue]) => {
    openingForm.opening_balance_date = dateValue || ''
    openingForm.opening_balance_amount = Number(amountValue || 0)
  },
  { immediate: true }
)

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

function openOpeningDialog() {
  openingForm.opening_balance_date = authStore.user?.opening_balance_date || new Date().toISOString().slice(0, 10)
  openingForm.opening_balance_amount = Number(authStore.user?.opening_balance_amount || 0)
  openingDialogVisible.value = true
}

async function saveOpeningBalance() {
  if (!openingForm.opening_balance_date) {
    ElMessage.error('请选择期初日期')
    return
  }

  saving.value = true
  try {
    await authStore.updateProfile({
      opening_balance_date: openingForm.opening_balance_date,
      opening_balance_amount: Number(openingForm.opening_balance_amount || 0)
    })
    openingDialogVisible.value = false
    notifyFinanceDataChanged()
    ElMessage.success('期初账已保存')
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
    openingDialogVisible.value = false
    notifyFinanceDataChanged()
    ElMessage.success('期初账已清除')
  } finally {
    saving.value = false
  }
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
  recurringForm.frequency = 'monthly'
  recurringForm.day_of_month = 1
  recurringForm.month_of_year = 1
  recurringForm.enabled = true
}

function recurringPayload() {
  return {
    name: recurringForm.name.trim(),
    amount: Number(recurringForm.amount || 0),
    category: recurringForm.category,
    frequency: recurringForm.frequency,
    day_of_month: Number(recurringForm.day_of_month || 1),
    month_of_year: recurringForm.frequency === 'yearly' ? Number(recurringForm.month_of_year || 1) : null,
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
  recurringForm.frequency = item.frequency
  recurringForm.day_of_month = item.day_of_month
  recurringForm.month_of_year = item.month_of_year || 1
  recurringForm.enabled = item.enabled
}

async function toggleRecurring(item) {
  await http.put(`/recurring-expenses/${item.id}`, { enabled: !item.enabled })
  await loadRecurringExpenses()
  notifyFinanceDataChanged()
}

async function deleteRecurring(item) {
  await http.delete(`/recurring-expenses/${item.id}`)
  ElMessage.success('固定支出已删除')
  await loadRecurringExpenses()
  notifyFinanceDataChanged()
}

function recurringScheduleLabel(item) {
  if (item.frequency === 'yearly') {
    return `每年 ${item.month_of_year}月${item.day_of_month}日`
  }
  return `每月 ${item.day_of_month}日`
}

function publicAsset(path) {
  return `${import.meta.env.BASE_URL || '/'}${path}`.replace(/\/{2,}/g, '/')
}

function openAvatarDialog() {
  avatarForm.mode = avatarMode.value
  avatarForm.preset = avatarPreference.value.preset || defaultAvatarOptions[0].value
  avatarForm.text = avatarPreference.value.text || ''
  avatarForm.image = avatarPreference.value.image || ''
  avatarDialogVisible.value = true
}

function selectDefaultAvatar(value) {
  avatarForm.mode = 'preset'
  avatarForm.preset = value
  avatarForm.image = ''
}

function useTextAvatar() {
  avatarForm.mode = 'text'
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
    text: avatarForm.text.trim(),
    image: avatarForm.mode === 'custom' ? avatarForm.image : ''
  }
  saveAvatarPreference(avatarPreference.value)
  avatarDialogVisible.value = false
  ElMessage.success('头像已保存')
}

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}

onMounted(loadRecurringExpenses)
</script>
