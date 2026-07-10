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
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { loadAvatarPreference, saveAvatarPreference } from '../utils/userPreferences'

const router = useRouter()
const authStore = useAuthStore()
const saving = ref(false)
const profileDialogVisible = ref(false)
const avatarDialogVisible = ref(false)
const avatarFileInput = ref(null)
const avatarPreference = ref(loadAvatarPreference())
const profileForm = reactive({
  username: ''
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

watch(
  () => authStore.user?.username,
  (value) => {
    profileForm.username = value || ''
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
</script>
