const avatarStorageKey = 'finance_avatar'
const legacyAvatarStorageKey = 'finance_mobile_avatar'

export function loadAvatarPreference() {
  try {
    return JSON.parse(localStorage.getItem(avatarStorageKey) || localStorage.getItem(legacyAvatarStorageKey) || '{}')
  } catch {
    return {}
  }
}

export function saveAvatarPreference(value) {
  localStorage.setItem(avatarStorageKey, JSON.stringify(value || {}))
}
