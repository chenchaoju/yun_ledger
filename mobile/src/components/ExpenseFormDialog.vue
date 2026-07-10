<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="min(520px, calc(100vw - 24px))" class="finance-dialog" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item v-if="isAmountStep" prop="amount" class="amount-form-item">
        <div class="amount-keypad">
          <div class="amount-display">
            <span>金额</span>
            <strong>￥{{ amountText || '0' }}元</strong>
          </div>
          <div class="amount-keys">
            <button v-for="key in amountKeys" :key="key" type="button" @click="pressAmountKey(key)">
              {{ key }}
            </button>
            <button type="button" @click="pressAmountKey('.')">.</button>
            <button type="button" @click="pressAmountKey('0')">0</button>
            <button type="button" class="amount-delete" @click="deleteAmount">删除</button>
          </div>
        </div>
      </el-form-item>
      <template v-else>
        <div class="expense-step-summary">
          <span>本次金额</span>
          <strong>¥{{ amountText || '0' }}</strong>
          <el-button v-if="!props.expense?.id" link type="primary" @click="step = 'amount'">修改</el-button>
        </div>
        <el-form-item label="分类" prop="category">
          <div class="category-picker">
            <button
              v-for="item in visibleCategories"
              :key="item.value"
              type="button"
              class="category-choice"
              :class="{ active: form.category === item.value }"
              :style="{ '--category-color': item.color }"
              :title="item.label"
              @click="setCategory(item.value)"
            >
              <span class="category-choice-icon">
                <el-icon><component :is="categoryIconComponent(item.icon)" /></el-icon>
              </span>
              <span>{{ item.label }}</span>
            </button>
          </div>
        </el-form-item>
        <el-form-item label="日期" prop="spent_at">
          <el-date-picker v-model="form.spent_at" type="date" value-format="YYYY-MM-DD" class="full-width" />
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input v-model="form.note" maxlength="255" show-word-limit placeholder="可选，例如：午餐、停车费" />
        </el-form-item>
      </template>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button v-if="isAmountStep" type="primary" class="amount-next-button" @click="goNext">下一步</el-button>
      <el-button v-else type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { allExpenseCategories, categoryChangedEvent } from '../constants/categories'
import { categoryIconComponent } from '../constants/categoryIcons'
import { notifyFinanceDataChanged } from '../utils/events'
import http from '../utils/http'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  expense: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const formRef = ref(null)
const submitting = ref(false)
const step = ref('amount')
const form = reactive(emptyForm())
const amountText = ref('0')
const visibleCategories = ref(allExpenseCategories())
const amountKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9']

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => (props.expense?.id ? '编辑支出' : '新增支出'))
const isAmountStep = computed(() => step.value === 'amount')

const rules = {
  amount: [{ required: true, message: '请输入金额', trigger: 'change' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  spent_at: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

function emptyForm() {
  return {
    amount: 0,
    category: '餐饮',
    spent_at: dayjs().format('YYYY-MM-DD'),
    note: ''
  }
}

function fillForm() {
  Object.assign(form, emptyForm(), props.expense || {})
  step.value = props.expense?.id ? 'details' : 'amount'
  form.amount = Number(form.amount || 0)
  amountText.value = form.amount ? formatAmountText(form.amount) : '0'
  form.note = form.note || ''
  refreshCategories()
  if (!visibleCategories.value.some((item) => item.value === form.category)) {
    form.category = visibleCategories.value[0]?.value || '其他'
  }
}

function goNext() {
  syncAmountFromText()
  if (Number(form.amount || 0) <= 0) {
    ElMessage.error('请输入金额')
    return
  }
  step.value = 'details'
}

function setCategory(category) {
  form.category = category
}

function formatAmountText(value) {
  const number = Number(value || 0)
  if (!number) return '0'
  return Number(number.toFixed(2)).toString()
}

function syncAmountFromText() {
  form.amount = Number(amountText.value || 0)
}

function pressAmountKey(key) {
  if (key === '.') {
    if (!amountText.value.includes('.')) {
      amountText.value = `${amountText.value || '0'}.`
    }
    syncAmountFromText()
    return
  }

  if (amountText.value === '0') {
    amountText.value = key
  } else {
    const [, decimal = ''] = amountText.value.split('.')
    if (amountText.value.includes('.') && decimal.length >= 2) return
    amountText.value = `${amountText.value}${key}`
  }
  syncAmountFromText()
}

function deleteAmount() {
  amountText.value = amountText.value.length > 1 ? amountText.value.slice(0, -1) : '0'
  if (amountText.value === '0.' || amountText.value === '') amountText.value = '0'
  syncAmountFromText()
}

function refreshCategories() {
  const categories = allExpenseCategories()
  const currentCategory = form.category
  if (currentCategory && !categories.some((item) => item.value === currentCategory)) {
    const currentHidden = allExpenseCategories({ includeHidden: true }).find((item) => item.value === currentCategory)
    visibleCategories.value = currentHidden ? [currentHidden, ...categories] : categories
    return
  }
  visibleCategories.value = categories
}

async function submit() {
  await formRef.value.validate()
  if (Number(form.amount || 0) <= 0) {
    ElMessage.error('请输入金额')
    return
  }
  submitting.value = true

  try {
    const payload = {
      amount: Number(form.amount),
      category: form.category,
      spent_at: form.spent_at,
      note: form.note || null
    }

    if (props.expense?.id) {
      await http.put(`/expenses/${props.expense.id}`, payload)
    } else {
      await http.post('/expenses', payload)
    }

    ElMessage.success('已保存')
    notifyFinanceDataChanged()
    visible.value = false
    emit('saved')
  } finally {
    submitting.value = false
  }
}

watch(() => props.modelValue, (value) => {
  if (value) fillForm()
})

window.addEventListener(categoryChangedEvent, refreshCategories)

onBeforeUnmount(() => {
  window.removeEventListener(categoryChangedEvent, refreshCategories)
})
</script>
