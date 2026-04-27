<template>
  <el-card class="event-card" shadow="hover">
    <div class="event-header">
      <el-tag :type="platformType" size="small">{{ event.platform }}</el-tag>
    </div>
    <h3 class="event-name">{{ event.name }}</h3>
    <div class="event-details">
      <div class="detail-item" v-if="event.artist">
        <el-icon><User /></el-icon>
        <span>{{ event.artist }}</span>
      </div>
      <div class="detail-item" v-if="event.venue">
        <el-icon><Location /></el-icon>
        <span>{{ event.venue }}</span>
      </div>
      <div class="detail-item" v-if="event.date">
        <el-icon><Calendar /></el-icon>
        <span>{{ event.date }}</span>
      </div>
    </div>
    <div class="event-actions">
      <el-button type="primary" size="small" @click="$emit('add-monitor', event)">
        <el-icon><Plus /></el-icon>添加监控
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface EventInfo {
  name: string
  artist?: string
  venue?: string
  date?: string
  platform: string
  url: string
  sessions?: string[]
}

const props = defineProps<{ event: EventInfo }>()
defineEmits(['add-monitor'])

const platformType = computed(() => {
  const map: Record<string, string> = { '大麦': 'danger', '猫眼': '', '纷玩岛': 'success' }
  return map[props.event.platform] || 'info'
})
</script>

<style scoped>
.event-card {
  margin-bottom: 12px;
  border-radius: 12px;
  transition: transform 0.2s;
}

.event-card:hover {
  transform: translateY(-2px);
}

.event-card :deep(.el-card__body) {
  padding: 16px;
}

.event-header {
  margin-bottom: 8px;
}

.event-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-primary);
  line-height: 1.4;
}

.event-details {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.event-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
