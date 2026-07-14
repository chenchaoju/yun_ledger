<template>
  <button type="button" class="settings-cell settings-row" @click="open"><span>会员固定支出</span><span>{{ summary }}</span></button>
  <el-dialog v-model="visible" title="会员固定支出" width="min(520px, calc(100vw - 24px))" class="finance-dialog">
    <div class="rules">
      <div v-for="item in rules" :key="item.id" class="rule">
        <button class="rule-info" @click="edit(item)"><strong>{{ item.name }}</strong><small>¥{{ Number(item.amount).toFixed(2) }} · {{ item.frequency === 'yearly' ? '每年' : '每月' }} · {{ dateText(item) }}</small></button>
        <el-switch :model-value="item.is_active" @change="toggle(item, $event)" />
        <el-button text type="danger" @click="remove(item)">删除</el-button>
      </div>
      <el-empty v-if="!rules.length" description="还没有固定会员支出" :image-size="72" />
    </div>
    <el-button type="primary" plain class="wide" @click="add">+ 添加会员费用</el-button>
  </el-dialog>
  <el-dialog v-model="editing" :title="form.id ? '编辑会员费用' : '添加会员费用'" width="min(440px, calc(100vw - 24px))" class="finance-dialog">
    <el-form label-position="top">
      <el-form-item label="会员名称"><el-input v-model.trim="form.name" placeholder="例如：腾讯视频、ChatGPT Plus" /></el-form-item>
      <el-form-item label="费用金额"><el-input-number v-model="form.amount" :min="0.01" :precision="2" class="wide" /></el-form-item>
      <el-form-item label="付费周期"><el-radio-group v-model="form.frequency"><el-radio-button value="monthly">每月</el-radio-button><el-radio-button value="yearly">每年</el-radio-button></el-radio-group></el-form-item>
      <el-form-item :label="form.frequency === 'monthly' ? '首次扣款日期（以后每月同日）' : '每年扣款日期'"><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" class="wide" /></el-form-item>
      <el-form-item label="立即启用"><el-switch v-model="form.is_active" /></el-form-item>
    </el-form>
    <template #footer><el-button @click="editing=false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存</el-button></template>
  </el-dialog>
</template>
<script setup>
import dayjs from 'dayjs'
import { computed, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../utils/http'
const visible=ref(false), editing=ref(false), saving=ref(false), rules=ref([])
const form=reactive({id:null,name:'',amount:0,frequency:'monthly',start_date:dayjs().format('YYYY-MM-DD'),is_active:true})
const summary=computed(()=>{const n=rules.value.filter(x=>x.is_active).length;return n?`已启用 ${n} 项`:'未设置'})
async function load(){rules.value=(await http.get('/recurring-expenses')).data}
async function open(){visible.value=true;await load()}
function add(){Object.assign(form,{id:null,name:'',amount:0,frequency:'monthly',start_date:dayjs().format('YYYY-MM-DD'),is_active:true});editing.value=true}
function edit(item){Object.assign(form,item,{amount:Number(item.amount)});editing.value=true}
function dateText(item){const d=dayjs(item.start_date);return item.frequency==='yearly'?`${d.month()+1}月${d.date()}日`:`每月${d.date()}日`}
async function save(){if(!form.name||form.amount<=0||!form.start_date)return ElMessage.error('请完整填写会员名称、金额和日期');saving.value=true;try{const p={name:form.name,amount:form.amount,category:'会员订阅',frequency:form.frequency,start_date:form.start_date,is_active:form.is_active};form.id?await http.put(`/recurring-expenses/${form.id}`,p):await http.post('/recurring-expenses',p);editing.value=false;await load();ElMessage.success('会员固定支出已保存')}finally{saving.value=false}}
async function toggle(item,value){await http.put(`/recurring-expenses/${item.id}`,{is_active:value});item.is_active=value;ElMessage.success(value?'已启用':'已停用')}
async function remove(item){await ElMessageBox.confirm(`确定删除“${item.name}”吗？已生成账单会保留。`,'删除会员费用',{type:'warning'});await http.delete(`/recurring-expenses/${item.id}`);await load()}
load()
</script>
<style scoped>.rules{display:grid;gap:10px;max-height:46vh;overflow:auto}.rule{display:flex;align-items:center;gap:8px;padding:12px;border:1px solid #e5edf7;border-radius:12px}.rule-info{display:grid;gap:4px;flex:1;text-align:left;border:0;background:none;cursor:pointer}.rule-info small{color:#8492a6}.wide{width:100%;margin-top:12px}</style>
