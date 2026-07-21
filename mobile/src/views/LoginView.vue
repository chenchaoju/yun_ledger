<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div class="auth-brand">
        <el-icon><Wallet /></el-icon>
        <h1>财务管理</h1>
      </div>

      <el-tabs v-model="mode" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="submit">
        <div v-if="mode === 'login'" class="auth-user-switch">
          <button type="button" @click="userManagerVisible = true">
            <el-icon><User /></el-icon>
            <span>{{ selectedSavedUserLabel }}</span>
          </button>
        </div>
        <el-form-item v-if="mode === 'register'" label="用户名" prop="username">
          <el-input v-model.trim="form.username" :prefix-icon="User" autocomplete="nickname" />
        </el-form-item>
        <el-form-item label="账号" prop="email">
          <el-input v-model.trim="form.email" :prefix-icon="User" placeholder="手机号或邮箱" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" :prefix-icon="Lock" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <div v-if="mode === 'login'" class="auth-options">
          <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
          <el-checkbox v-model="autoLogin">自动登录</el-checkbox>
        </div>
        <el-button type="primary" class="full-width" :loading="loading" @click="submit">
          {{ mode === 'login' ? '登录' : '注册' }}
        </el-button>
      </el-form>

      <el-dialog
        v-model="userManagerVisible"
        title="用户管理"
        width="min(400px, calc(100vw - 24px))"
        class="finance-dialog"
      >
        <div class="saved-user-list">
          <button
            v-for="item in savedUsers"
            :key="item.email"
            type="button"
            class="saved-user-row"
            :class="{ active: normalizeAccount(form.email) === normalizeAccount(item.email) }"
            @click="selectSavedUser(item)"
          >
            <span>
              <strong>{{ item.label || item.email }}</strong>
              <em>{{ item.email }}</em>
            </span>
            <i>{{ item.password ? '已记住密码' : '仅账号' }}</i>
          </button>
          <el-empty v-if="!savedUsers.length" description="暂无登录用户" :image-size="80" />
        </div>
        <template #footer>
          <el-button v-if="form.email" @click="removeCurrentSavedUser">删除当前用户</el-button>
          <el-button type="primary" @click="userManagerVisible = false">完成</el-button>
        </template>
      </el-dialog>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock, User, Wallet } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const mode = ref('login')
const rememberPassword = ref(false)
const autoLogin = ref(false)
const credentialKey = 'finance_mobile_saved_login'
const userListKey = 'finance_mobile_saved_users'
const skipAutoLoginKey = 'skip_auto_login_once'
const autoLoginPausedKey = 'finance_mobile_auto_login_paused'
const userManagerVisible = ref(false)
const savedUsers = ref([])

const form = reactive({
  username: '',
  email: '',
  password: ''
})

const rules = {
  username: [
    {
      validator: (_rule, value, callback) => {
        if (mode.value === 'register' && !String(value || '').trim()) {
          callback(new Error('请输入用户名'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入手机号或邮箱', trigger: 'blur' },
    { min: 3, message: '账号至少 3 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' }
  ]
}

const selectedSavedUserLabel = computed(() => {
  const current = savedUsers.value.find((item) => normalizeAccount(item.email) === normalizeAccount(form.email))
  return current ? `当前用户：${current.label || current.email}` : '用户管理'
})

function normalizeAccount(value) {
  return String(value || '').trim().toLowerCase()
}

function readSavedUsers() {
  try {
    const users = JSON.parse(localStorage.getItem(userListKey) || '[]')
    return Array.isArray(users) ? users.filter((item) => item?.email) : []
  } catch {
    localStorage.removeItem(userListKey)
    return []
  }
}

function writeSavedUsers(users) {
  localStorage.setItem(userListKey, JSON.stringify(users))
  savedUsers.value = users
}

function upsertSavedUser(user) {
  const account = normalizeAccount(user.email)
  if (!account) return
  const users = readSavedUsers().filter((item) => normalizeAccount(item.email) !== account)
  users.unshift({
    email: user.email,
    label: user.label || user.email,
    password: user.password || '',
    rememberPassword: Boolean(user.rememberPassword),
    autoLogin: Boolean(user.autoLogin),
    updatedAt: new Date().toISOString()
  })
  writeSavedUsers(users.slice(0, 8))
}

function selectSavedUser(item) {
  form.email = item.email || ''
  form.password = item.password || ''
  rememberPassword.value = Boolean(item.password || item.rememberPassword)
  autoLogin.value = Boolean(item.autoLogin && item.password)
  userManagerVisible.value = false
}

async function removeCurrentSavedUser() {
  const confirmed = await ElMessageBox.confirm(
    '确定删除这个登录用户吗？只会删除本机保存的账号，不会注销账号。',
    '删除登录用户',
    {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger'
    }
  ).catch(() => false)
  if (!confirmed) return
  const account = normalizeAccount(form.email)
  writeSavedUsers(readSavedUsers().filter((item) => normalizeAccount(item.email) !== account))
  localStorage.removeItem(credentialKey)
  rememberPassword.value = false
  autoLogin.value = false
  form.password = ''
  ElMessage.success('已删除当前登录用户')
}

function loadLoginPreference() {
  savedUsers.value = readSavedUsers()
  try {
    const saved = JSON.parse(localStorage.getItem(credentialKey) || 'null')
    if (saved?.email) {
      upsertSavedUser({
        email: saved.email,
        label: saved.email,
        password: saved.password || '',
        rememberPassword: saved.rememberPassword,
        autoLogin: saved.autoLogin
      })
      localStorage.removeItem(credentialKey)
    }
  } catch {
    localStorage.removeItem(credentialKey)
  }

  const autoUser = savedUsers.value.find((item) => item.autoLogin && item.password)
  const firstUser = autoUser || savedUsers.value[0]
  if (firstUser) {
    selectSavedUser(firstUser)
  }
}

function saveLoginPreference(user) {
  upsertSavedUser({
    email: form.email,
    label: user?.username || user?.email || form.email,
    password: rememberPassword.value ? form.password : '',
    rememberPassword: rememberPassword.value,
    autoLogin: autoLogin.value && rememberPassword.value
  })
}

async function submit() {
  await formRef.value.validate()
  loading.value = true

  try {
    if (mode.value === 'login') {
      await authStore.login(form)
      sessionStorage.removeItem(autoLoginPausedKey)
      saveLoginPreference(authStore.user)
      ElMessage.success('登录成功')
    } else {
      await authStore.register(form)
      sessionStorage.removeItem(autoLoginPausedKey)
      upsertSavedUser({
        email: form.email,
        label: authStore.user?.username || form.username || form.email,
        password: '',
        rememberPassword: false,
        autoLogin: false
      })
      ElMessage.success('注册成功')
    }

    router.push(route.query.redirect || { name: 'dashboard' })
  } finally {
    loading.value = false
  }
}

watch(autoLogin, (value) => {
  if (value) rememberPassword.value = true
})

watch(rememberPassword, (value) => {
  if (!value) autoLogin.value = false
})

onMounted(async () => {
  loadLoginPreference()
  const skipAutoLogin = sessionStorage.getItem(skipAutoLoginKey) === '1'
  const autoLoginPaused = sessionStorage.getItem(autoLoginPausedKey) === '1'
  if (skipAutoLogin) {
    sessionStorage.removeItem(skipAutoLoginKey)
  }
  if (skipAutoLogin || autoLoginPaused) {
    return
  }
  if (mode.value === 'login' && autoLogin.value && form.email && form.password && !authStore.isAuthenticated) {
    await submit()
  }
})
</script>
