<template>
  <div :class="['notification-item', { unread: !notification.is_read }]" @click="handleClick">
    <div class="notif-icon">
      <el-icon :size="20" :color="notification.is_read ? '#909399' : '#FF6B6B'">
        <Bell />
      </el-icon>
    </div>
    <div class="notif-content">
      <div class="notif-title">{{ notification.event_name }}</div>
      <div class="notif-message">{{ notification.message }}</div>
      <div class="notif-time">{{ formatTime(notification.created_at) }}</div>
    </div>
    <div class="notif-badge" v-if="!notification.is_read">
      <span class="dot"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Notification } from '../stores/notifications'

const props = defineProps<{ notification: Notification }>()
const emit = defineEmits(['read'])

function formatTime(time: string) {
  const d = new Date(time)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function handleClick() {
  if (!props.notification.is_read) {
    emit('read', props.notification.id)
  }
}
</script>

<style scoped>
.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:hover {
  background: #F5F7FA;
}

.notification-item.unread {
  background: #FFF5F5;
}

.notif-icon {
  flex-shrink: 0;
  padding-top: 2px;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.notif-message {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.notif-time {
  font-size: 12px;
  color: var(--info-color);
}

.notif-badge {
  flex-shrink: 0;
  padding-top: 6px;
}

.dot {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
}
</style>
