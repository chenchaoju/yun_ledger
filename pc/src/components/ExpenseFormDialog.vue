<template>
  <el-dialog v-model="visible" :title="dialogTitle" width="min(520px, calc(100vw - 24px))" class="finance-dialog" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="金额" prop="amount">
        <el-input-number v-model="form.amount" :min="0.01" :precision="2" :step="10" controls-position="right" />
      </el-form-item>
      <el-form-item label="分类" prop="category">
        <div class="category-picker">
          <button
            v-for="item in expenseCategories"
            :key="item.value"
            type="button"
            class="category-choice"
            :class="{ active: form.category === item.value }"
            :style="{ '--category-color': item.color }"
            :title="item.label"
            @click="setCategory(item.value)"
          >
            <span class="category-choice-icon">
              <el-icon><component :is="categoryIconMap[item.value]" /></el-icon>
            </span>
            <span>{{ item.label }}</span>
          </button>
        </div>
      </el-form-item>
      <el-form-item label="日期" prop="spent_at">
        <el-date-picker v-model="form.spent_at" type="date" value-format="YYYY-MM-DD" class="full-width" />
      </el-form-item>
      <el-form-item label="备注" prop="note">
        <el-input v-model="form.note" maxlength="255" show-word-limit />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import dayjs from 'dayjs'
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Bowl,
  FirstAidKit,
  House,
  MoreFilled,
  Present,
  Reading,
  Service,
  ShoppingBag,
  ShoppingCart,
  Trophy,
  Van
} from '@element-plus/icons-vue'
import { expenseCategories } from '../constants/categories'
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
const form = reactive(emptyForm())
const categoryIconMap = {
  餐饮: Bowl,
  交通: Van,
  购物: ShoppingBag,
  网购: ShoppingCart,
  服务: Service,
  居住: House,
  送礼: Present,
  娱乐: Trophy,
  医疗: FirstAidKit,
  教育: Reading,
  其他: MoreFilled
}

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => (props.expense?.id ? '编辑支出' : '新增支出'))

const rules = {
  amount: [{ required: true, message: '请输入金额', trigger: 'change' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  spent_at: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

function emptyForm() {
  return {
    amount: 0.01,
    category: '餐饮',
    spent_at: dayjs().format('YYYY-MM-DD'),
    note: ''
  }
}

function fillForm() {
  Object.assign(form, emptyForm(), props.expense || {})
  form.amount = Number(form.amount || 0.01)
  form.note = form.note || ''
}

function setCategory(category) {
  form.category = category
}

async function submit() {
  await formRef.value.validate()
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
</script>
