export const expenseCategories = [
  { label: '餐饮', value: '餐饮', color: '#f97316' },
  { label: '交通', value: '交通', color: '#2563eb' },
  { label: '购物', value: '购物', color: '#db2777' },
  { label: '网购', value: '网购', color: '#9333ea' },
  { label: '服务', value: '服务', color: '#14b8a6' },
  { label: '居住', value: '居住', color: '#0f766e' },
  { label: '送礼', value: '送礼', color: '#e11d48' },
  { label: '娱乐', value: '娱乐', color: '#7c3aed' },
  { label: '医疗', value: '医疗', color: '#dc2626' },
  { label: '教育', value: '教育', color: '#0891b2' },
  { label: '其他', value: '其他', color: '#64748b' }
]

export const categoryColorMap = expenseCategories.reduce((map, item) => {
  map[item.value] = item.color
  return map
}, {})
