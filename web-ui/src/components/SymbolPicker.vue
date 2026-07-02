<script setup lang="ts">
// 选标的 + 取行情（按日期范围）。
// 后端 /bars 仅支持 count（上限 800，约 3.2 年），固定拉满后前端按日期过滤。
// 默认：结束日=今天（最近交易日），开始日=3年前。

import { ref } from 'vue'

import { fetchBars, formatError } from '../api'
import { useBacktestStore } from '../stores/backtest'
import type { Category } from '../types'

const store = useBacktestStore()

const market = ref('SZ')
const code = ref('000001')
const category = ref<Category>('DAY')

// 日期默认：结束=今天，开始=3年前
function isoDaysFromNow(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}
const endDate = ref(isoDaysFromNow(0))
const startDate = ref(isoDaysFromNow(-365 * 3))

const loading = ref(false)
const error = ref('')

const CATEGORIES: Category[] = ['DAY', 'WEEK', 'MONTH', 'MIN_5', 'MIN_15', 'MIN_30', 'MIN_60']

async function loadBars() {
  // 基本校验
  if (!/^\d{6}$/.test(code.value)) {
    error.value = '股票代码必须是 6 位数字'
    return
  }
  if (startDate.value >= endDate.value) {
    error.value = '开始日期必须早于结束日期'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const bars = await fetchBars(
      market.value,
      code.value,
      category.value,
      startDate.value,
      endDate.value,
    )
    if (bars.length < 2) {
      error.value = `该日期范围内仅取到 ${bars.length} 根 K 线，不足以回测`
      return
    }
    const range = `${startDate.value} ~ ${endDate.value}`
    store.setOhlcv(bars, `${market.value}:${code.value} ${category.value} ${range}`)
    store.clearResult()
  } catch (e) {
    error.value = formatError(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="symbol-picker">
    <div class="row">
      <div class="field">
        <label>市场</label>
        <select v-model="market">
          <option value="SZ">深市</option>
          <option value="SH">沪市</option>
          <option value="BJ">北交所</option>
        </select>
      </div>
      <div class="field code-field">
        <label>代码</label>
        <input
          v-model="code"
          maxlength="6"
          placeholder="6位代码"
          @keyup.enter="loadBars"
        />
      </div>
    </div>

    <div class="field">
      <label>周期</label>
      <select v-model="category">
        <option v-for="c in CATEGORIES" :key="c" :value="c">{{ c }}</option>
      </select>
    </div>

    <div class="row">
      <div class="field">
        <label>开始日期</label>
        <input v-model="startDate" type="date" />
      </div>
      <div class="field">
        <label>结束日期</label>
        <input v-model="endDate" type="date" />
      </div>
    </div>

    <button class="primary" :disabled="loading" @click="loadBars">
      {{ loading ? '取行情中…' : '取行情' }}
    </button>

    <p v-if="error" class="err">{{ error }}</p>
    <p v-if="store.barsSource" class="ok">
      已加载：{{ store.barsSource }}（{{ store.ohlcv.length }} 根）
    </p>
  </div>
</template>

<style scoped>
.code-field {
  flex: 2;
}
.err {
  color: var(--up);
  font-size: 12px;
  margin-top: 8px;
}
.ok {
  color: var(--down);
  font-size: 12px;
  margin-top: 8px;
}
</style>
