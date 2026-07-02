<script setup lang="ts">
// 多标的输入（组合回测用）。逐个添加 市场:代码，可删除。

import { ref } from 'vue'

const props = defineProps<{
  modelValue: string[]
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()

const market = ref('SZ')
const code = ref('')

function add() {
  if (!/^\d{6}$/.test(code.value)) return
  const sym = `${market.value}:${code.value}`
  if (!props.modelValue.includes(sym)) {
    emit('update:modelValue', [...props.modelValue, sym])
  }
  code.value = ''
}

function remove(sym: string) {
  emit('update:modelValue', props.modelValue.filter((s) => s !== sym))
}
</script>

<template>
  <div class="stocks-picker">
    <div class="row">
      <select v-model="market">
        <option value="SZ">深市</option>
        <option value="SH">沪市</option>
        <option value="BJ">北交所</option>
      </select>
      <input
        v-model="code"
        maxlength="6"
        placeholder="6位代码"
        @keyup.enter="add"
      />
      <button @click="add">添加</button>
    </div>

    <div v-if="modelValue.length" class="stock-list">
      <span v-for="s in modelValue" :key="s" class="stock-tag">
        {{ s }}
        <button class="remove" @click="remove(s)">×</button>
      </span>
    </div>
    <p v-else class="hint">至少添加 1 只标的</p>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  gap: 6px;
}
.row select {
  width: auto;
}
.row input {
  flex: 1;
}
.stock-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.stock-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: var(--font-mono);
}
.remove {
  border: none;
  background: none;
  color: var(--text-dim);
  padding: 0 2px;
  font-size: 14px;
  line-height: 1;
}
.remove:hover {
  color: var(--up);
}
.hint {
  color: var(--text-dim);
  font-size: 11px;
  margin-top: 8px;
}
</style>
