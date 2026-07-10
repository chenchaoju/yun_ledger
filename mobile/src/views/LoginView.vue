<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div class="auth-brand">
        <el-icon><Wallet /></el-icon>
        <h1>云记账</h1>
      </div>

      <el-tabs v-model="mode" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @keyup.enter="submit">
        <el-form-item label="账号" prop="email">
          <el-input v-model.trim="form.email" :prefix-icon="User" placeholder="手机号或邮箱" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" :prefix-icon="Lock" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <div class="auth-options">
          <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
          <el-checkbox v-model="autoLogin">自动登录</el-checkbox>
        </div>
        <el-button type="primary" class="full-width" :loading="loading" @click="submit">
          {{ mode === 'login' ? '登录' : '注册' }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User, Wallet } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { clearAutoLoginSkip, loadAuthPreferences, saveAuthPreferences, shouldSkipAutoLogin } from '../utils/authPreferences'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)
const loading = ref(false)
const mode = ref('login')
const rememberPassword = ref(false)
const autoLogin = ref(false)

const form = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入手机号或邮箱', trigger: 'blur' },
    { min: 3, message: '账号至少 3 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' }
  ]
}

watch(rememberPassword, (value) => {
  if (!value) {
    autoLogin.value = false
  }
})

watch(autoLogin, (value) => {
  if (value) {
    rememberPassword.value = true
  }
})

onMounted(() => {
  const preferences = loadAuthPreferences()
  rememberPassword.value = Boolean(preferences.rememberPassword)
  autoLogin.value = Boolean(preferences.autoLogin)

  if (rememberPassword.value) {
    form.email = preferences.email || ''
    form.password = preferences.password || ''
  }

  if (autoLogin.value && form.email && form.password && !shouldSkipAutoLogin()) {
    submit({ silent: true }).catch(() => {
      autoLogin.value = false
    })
  }
})

function persistAuthPreferences() {
  saveAuthPreferences({
    email: form.email,
    password: form.password,
    rememberPassword: rememberPassword.value,
    autoLogin: autoLogin.value && mode.value === 'login'
  })
}

async function submit(options = {}) {
  await formRef.value.validate()
  loading.value = true

  try {
    if (mode.value === 'login') {
      await authStore.login(form)
      persistAuthPreferences()
      clearAutoLoginSkip()
      if (!options.silent) {
        ElMessage.success('登录成功')
      }
    } else {
      await authStore.register(form)
      persistAuthPreferences()
      clearAutoLoginSkip()
      ElMessage.success('注册成功')
    }

    router.push(route.query.redirect || { name: 'dashboard' })
  } finally {
    loading.value = false
  }
}
</script>
