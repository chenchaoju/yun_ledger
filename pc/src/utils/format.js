export function currency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(Number(value || 0))
}

export function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

