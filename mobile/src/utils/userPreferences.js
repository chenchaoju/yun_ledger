const avatarStorageKey = 'finance_mobile_avatar'

export function loadAvatarPreference() {
  try {
    return JSON.parse(localStorage.getItem(avatarStorageKey) || '{}')
  } catch {
    return {}
  }
}

export function saveAvatarPreference(value) {
  localStorage.setItem(avatarStorageKey, JSON.stringify(value || {}))
}
