const authPreferenceKey = 'finance_auth_preferences'
const skipAutoLoginKey = 'finance_skip_auto_login'

export function loadAuthPreferences() {
  try {
    return JSON.parse(localStorage.getItem(authPreferenceKey) || '{}')
  } catch {
    return {}
  }
}

export function saveAuthPreferences(value) {
  if (!value?.rememberPassword && !value?.autoLogin) {
    localStorage.removeItem(authPreferenceKey)
    return
  }

  localStorage.setItem(
    authPreferenceKey,
    JSON.stringify({
      email: value.email || '',
      password: value.password || '',
      rememberPassword: Boolean(value.rememberPassword || value.autoLogin),
      autoLogin: Boolean(value.autoLogin)
    })
  )
}

export function disableAutoLoginForSession() {
  sessionStorage.setItem(skipAutoLoginKey, '1')
}

export function clearAutoLoginSkip() {
  sessionStorage.removeItem(skipAutoLoginKey)
}

export function shouldSkipAutoLogin() {
  return sessionStorage.getItem(skipAutoLoginKey) === '1'
}
