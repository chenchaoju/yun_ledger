<template>
  <el-dialog v-model="visible" title="本月收入" width="min(600px, calc(100vw - 24px))" class="finance-dialog" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="工资收入" prop="salary_income">
        <el-input-number
          v-model="form.salary_income"
          :min="0"
          :precision="2"
          :step="500"
          controls-position="right"
          class="full-width"
        />
      </el-form-item>

      <div class="extra-income-panel">
        <div class="extra-income-header">
          <span>额外收入</span>
          <strong>{{ currency(extraIncomeTotal) }}</strong>
        </div>

        <div v-if="form.extra_income_items.length" class="extra-income-list">
          <div v-for="(item, index) in form.extra_income_items" :key="item.key" class="extra-income-row">
            <el-input v-model="item.name" maxlength="60" placeholder="收入来源" class="extra-income-source" />
            <el-input-number
              v-model="item.amount"
              :min="0"
              :precision="2"
              :step="100"
              controls-position="right"
              class="extra-income-amount"
            />
            <el-button :icon="Delete" circle @click="removeExtraIncome(index)" />
          </div>
        </div>

        <el-button :icon="Plus" @click="addExtraIncome">添加一笔</el-button>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { notifyFinanceDataChanged } from '../utils/events'
import { currency } from '../utils/format'
import http from '../utils/http'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  year: {
    type: Number,
    required: true
  },
  month: {
    type: Number,
    required: true
  },
  income: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

let extraIncomeKey = 0
const formRef = ref(null)
const submitting = ref(false)
const form = reactive({
  salary_income: 0,
  extra_income_items: []
})

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const rules = {
  salary_income: [{ required: true, message: '请输入工资收入', trigger: 'change' }]
}

const extraIncomeTotal = computed(() => {
  return form.extra_income_items.reduce((total, item) => total + Number(item.amount || 0), 0)
})

function createExtraIncomeItem(item = {}) {
  extraIncomeKey += 1
  return {
    key: extraIncomeKey,
    name: item.name || '',
    amount: Number(item.amount || 0),
    occurred_at: item.occurred_at || null
  }
}

function fillForm() {
  form.salary_income = Number(props.income?.salary_income || 0)
  form.extra_income_items.splice(0, form.extra_income_items.length)

  const items = Array.isArray(props.income?.extra_income_items) ? props.income.extra_income_items : []
  if (items.length) {
    form.extra_income_items.push(...items.map((item) => createExtraIncomeItem(item)))
    return
  }

  const legacyExtraIncome = Number(props.income?.extra_income || 0)
  if (legacyExtraIncome > 0) {
    form.extra_income_items.push(createExtraIncomeItem({ name: '额外收入', amount: legacyExtraIncome }))
  }
}

function addExtraIncome() {
  form.extra_income_items.push(createExtraIncomeItem())
}

function removeExtraIncome(index) {
  form.extra_income_items.splice(index, 1)
}

function normalizedExtraIncomeItems() {
  return form.extra_income_items
    .map((item) => ({
      name: String(item.name || '额外收入').trim() || '额外收入',
      amount: Number(item.amount || 0),
      occurred_at: item.occurred_at || null
    }))
    .filter((item) => item.amount > 0)
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true

  try {
    await http.put('/incomes/monthly', {
      year: props.year,
      month: props.month,
      salary_income: Number(form.salary_income || 0),
      extra_income_items: normalizedExtraIncomeItems()
    })

    ElMessage.success('收入已保存')
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
</script>

<style scoped>
.extra-income-panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
}

.extra-income-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #475569;
}

.extra-income-header strong {
  color: #0f172a;
  font-size: 16px;
}

.extra-income-list {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.extra-income-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px 36px;
  gap: 10px;
  align-items: center;
}

.extra-income-source,
.extra-income-amount {
  width: 100%;
}

@media (max-width: 720px) {
  .extra-income-row {
    grid-template-columns: minmax(0, 1fr) 140px 36px;
  }
}
</style>
