<template>
  <section class="settings-page">
    <div class="settings-cell profile-cell">
      <div class="settings-avatar">
        <img v-if="avatarImage" :src="avatarImage" alt="用户头像" />
        <span v-else>{{ avatarText }}</span>
      </div>
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
      <button type="button" class="settings-cell settings-row" @click="salaryDialogVisible = true">
        <span>预设工资</span>
        <span>{{ defaultSalaryLabel }}</span>
      </button>
      <button type="button" class="settings-cell settings-row" @click="openAvatarDialog">
        <span>头像</span>
        <span>{{ avatarSummary }}</span>
      </button>
      <button type="button" class="settings-cell settings-row" @click="categoryDialogVisible = true">
        <span>分类管理</span>
        <span>{{ categorySummary }}</span>
      </button>
      <DataTransferButton @imported="handleImported" />
      <button type="button" class="settings-cell settings-row danger-row" @click="logout">
        <span>退出登录</span>
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
      v-model="salaryDialogVisible"
      title="预设工资"
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
      </el-form>
      <template #footer>
        <el-button @click="salaryDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveDefaultSalary">保存</el-button>
      </template>
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
          <div v-for="item in allManagedCategories" :key="item.value" class="category-toggle-row">
            <span class="category-toggle-name">
              <i :style="{ color: item.color }">
                <el-icon><component :is="categoryIconComponent(item.icon)" /></el-icon>
              </i>
              <span>{{ item.label }}</span>
              <em v-if="item.custom">自定义</em>
            </span>
            <span class="category-toggle-actions">
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
        <el-input v-if="avatarForm.mode === 'text'" v-model.trim="avatarForm.text" maxlength="2" placeholder="头像文字，例如：财" />
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
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import DataTransferButton from '../components/DataTransferButton.vue'
import {
  buildCustomCategory,
  expenseCategories,
  loadCustomCategories,
  loadHiddenCategoryValues,
  saveCustomCategories,
  saveHiddenCategoryValues
} from '../constants/categories'
import { categoryIconComponent, categoryIconOptions } from '../constants/categoryIcons'
import { useAuthStore } from '../stores/auth'
import { currency } from '../utils/format'
import { loadAvatarPreference, saveAvatarPreference } from '../utils/userPreferences'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const profileDialogVisible = ref(false)
const salaryDialogVisible = ref(false)
const categoryDialogVisible = ref(false)
const avatarDialogVisible = ref(false)
const avatarFileInput = ref(null)
const newCategoryName = ref('')
const newCategoryIcon = ref('MoreFilled')
const customCategories = ref(loadCustomCategories())
const hiddenCategoryValues = ref(loadHiddenCategoryValues())
const avatarPreference = ref(loadAvatarPreference())
const profileForm = reactive({
  username: ''
})
const salaryForm = reactive({
  default_salary_income: 0
})
const avatarForm = reactive({
  mode: 'preset',
  preset: 'cat-window',
  text: '',
  image: ''
})
const defaultAvatarOptions = [
  { value: 'cat-window', label: '默认头像 1', image: publicAsset('avatar-cat-window.jpg') },
  { value: 'cat-closeup', label: '默认头像 2', image: publicAsset('avatar-cat-closeup.jpg') }
]

const defaultDisplayName = computed(() => {
  const userNumber = (((Number(authStore.user?.id) || 1) - 1) % 199) + 1
  return `用户${userNumber}`
})
const displayName = computed(() => authStore.user?.username || defaultDisplayName.value)
const accountLabel = computed(() => authStore.user?.email || '')
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
const avatarText = computed(() => String(avatarPreference.value.text || displayName.value || '财').slice(0, 2).toUpperCase())
const previewAvatarText = computed(() => String(avatarForm.text || displayName.value || '财').slice(0, 2).toUpperCase())
const previewDefaultAvatar = computed(() => {
  return defaultAvatarOptions.find((item) => item.value === avatarForm.preset) || defaultAvatarOptions[0]
})
const previewAvatarImage = computed(() => {
  if (avatarForm.mode === 'custom') return avatarForm.image
  if (avatarForm.mode === 'preset') return previewDefaultAvatar.value.image
  return ''
})
const defaultSalary = computed(() => Number(authStore.user?.default_salary_income || 0))
const defaultSalaryLabel = computed(() => (defaultSalary.value > 0 ? currency(defaultSalary.value) : '未设置'))
const allManagedCategories = computed(() => [...expenseCategories, ...customCategories.value])
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

function handleImported() {
  ElMessage.success('数据已更新')
}

function addCategory() {
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
  customCategories.value = [...customCategories.value, buildCustomCategory(name, customCategories.value.length, newCategoryIcon.value)]
  saveCustomCategories(customCategories.value)
  newCategoryName.value = ''
  newCategoryIcon.value = 'MoreFilled'
  ElMessage.success('分类已添加')
}

function removeCategory(value) {
  customCategories.value = customCategories.value.filter((item) => item.value !== value)
  saveCustomCategories(customCategories.value)
  hiddenCategoryValues.value = hiddenCategoryValues.value.filter((item) => item !== value)
  saveHiddenCategoryValues(hiddenCategoryValues.value)
}

function isCategoryHidden(value) {
  return hiddenCategoryValues.value.includes(value)
}

function toggleCategory(value) {
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
}

function openAvatarDialog() {
  avatarForm.mode = avatarMode.value
  avatarForm.preset = avatarPreference.value.preset || defaultAvatarOptions[0].value
  avatarForm.text = avatarPreference.value.text || ''
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

async function saveDefaultSalary() {
  const amount = Number(salaryForm.default_salary_income || 0)
  if (amount < 0) {
    ElMessage.error('预设工资不能小于 0')
    return
  }

  saving.value = true
  try {
    await authStore.updateProfile({ default_salary_income: amount })
    salaryDialogVisible.value = false
    ElMessage.success('预设工资已保存')
  } finally {
    saving.value = false
  }
}

function logout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>
