export const FINANCE_DATA_CHANGED = 'finance-data-changed'

export function notifyFinanceDataChanged() {
  window.dispatchEvent(new CustomEvent(FINANCE_DATA_CHANGED))
}
