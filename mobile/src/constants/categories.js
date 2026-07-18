export const expenseCategories = [
  { label: '餐饮', value: '餐饮', color: '#f97316', icon: 'Bowl' },
  { label: '交通', value: '交通', color: '#2563eb', icon: 'Van' },
  { label: '购物', value: '购物', color: '#db2777', icon: 'ShoppingBag' },
  { label: '网购', value: '网购', color: '#9333ea', icon: 'ShoppingCart' },
  { label: '服务', value: '服务', color: '#14b8a6', icon: 'Service' },
  { label: '居住', value: '居住', color: '#0f766e', icon: 'House' },
  { label: '送礼', value: '送礼', color: '#e11d48', icon: 'Present' },
  { label: '娱乐', value: '娱乐', color: '#7c3aed', icon: 'Trophy' },
  { label: '医疗', value: '医疗', color: '#dc2626', icon: 'FirstAidKit' },
  { label: '教育', value: '教育', color: '#0891b2', icon: 'Reading' },
  { label: '其他', value: '其他', color: '#64748b', icon: 'MoreFilled' }
]

const customCategoryStorageKey = 'finance_mobile_custom_categories'
const hiddenCategoryStorageKey = 'finance_mobile_hidden_categories'
const categoryOrderStorageKey = 'finance_mobile_category_order'
export const categoryChangedEvent = 'finance-mobile-categories-changed'
const customColors = ['#0ea5e9', '#22c55e', '#a855f7', '#f59e0b', '#ef4444', '#64748b']

export function loadCustomCategories() {
  try {
    const value = JSON.parse(localStorage.getItem(customCategoryStorageKey) || '[]')
    return Array.isArray(value) ? value.filter((item) => item?.label && item?.value) : []
  } catch {
    return []
  }
}

export function saveCustomCategories(categories) {
  localStorage.setItem(customCategoryStorageKey, JSON.stringify(categories))
  window.dispatchEvent(new CustomEvent(categoryChangedEvent))
}

export function loadHiddenCategoryValues() {
  try {
    const value = JSON.parse(localStorage.getItem(hiddenCategoryStorageKey) || '[]')
    return Array.isArray(value) ? value.filter(Boolean) : []
  } catch {
    return []
  }
}

export function saveHiddenCategoryValues(values) {
  localStorage.setItem(hiddenCategoryStorageKey, JSON.stringify([...new Set(values.filter(Boolean))]))
  window.dispatchEvent(new CustomEvent(categoryChangedEvent))
}

export function loadCategoryOrder() {
  try {
    const value = JSON.parse(localStorage.getItem(categoryOrderStorageKey) || '[]')
    return Array.isArray(value) ? value.filter(Boolean) : []
  } catch {
    return []
  }
}

export function saveCategoryOrder(values) {
  localStorage.setItem(categoryOrderStorageKey, JSON.stringify([...new Set(values.filter(Boolean))]))
  window.dispatchEvent(new CustomEvent(categoryChangedEvent))
}

export function buildCustomCategory(name, index = 0, icon = 'MoreFilled') {
  const label = String(name || '').trim()
  return {
    label,
    value: label,
    color: customColors[index % customColors.length],
    icon,
    custom: true
  }
}

function applyCategoryOrder(categories, order = loadCategoryOrder()) {
  if (!order.length) return categories
  const orderMap = new Map(order.map((value, index) => [value, index]))
  return [...categories].sort((left, right) => {
    const leftOrder = orderMap.has(left.value) ? orderMap.get(left.value) : Number.MAX_SAFE_INTEGER
    const rightOrder = orderMap.has(right.value) ? orderMap.get(right.value) : Number.MAX_SAFE_INTEGER
    if (leftOrder !== rightOrder) return leftOrder - rightOrder
    return categories.indexOf(left) - categories.indexOf(right)
  })
}

export function allExpenseCategories(options = {}) {
  const { includeHidden = false } = options
  const custom = loadCustomCategories()
  const defaultValues = new Set(expenseCategories.map((item) => item.value))
  const all = applyCategoryOrder([...expenseCategories, ...custom.filter((item) => !defaultValues.has(item.value))])
  if (includeHidden) return all
  const hiddenValues = new Set(loadHiddenCategoryValues())
  return all.filter((item) => !hiddenValues.has(item.value))
}

export function categoryColorMapFrom(categories = allExpenseCategories({ includeHidden: true })) {
  return categories.reduce((map, item) => {
    map[item.value] = item.color
    return map
  }, {})
}

export const categoryColorMap = expenseCategories.reduce((map, item) => {
  map[item.value] = item.color
  return map
}, {})
