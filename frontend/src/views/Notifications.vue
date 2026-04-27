<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">通知中心</h2>
      <el-button type="primary" text @click="handleMarkAllRead" :disabled="notifStore.unreadCount === 0">
        <el-icon><Check /></el-icon>全部标记已读
      </el-button>
    </div>

    <el-card class="notification-card" shadow="never">
      <div v-if="notifStore.loading" class="loading-state">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="notifStore.notifications.length === 0" class="empty-state">
        <el-empty description="暂无通知" :image-size="100" />
      </div>
      <div v-else>
        <NotificationItem v-for="n in notifStore.notifications" :key="n.id"
          :notification="n" @read="handleMarkRead" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useNotificationsStore } from '../stores/notifications'
import NotificationItem from '../components/NotificationItem.vue'

const notifStore = useNotificationsStore()

async function handleMarkRead(id: number) {
  try {
    await notifStore.markRead(id)
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleMarkAllRead() {
  try {
    await notifStore.markAllRead()
    ElMessage.success('已全部标记为已读')
  } catch {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  notifStore.fetchNotifications()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
}

.notification-card {
  border-radius: 12px;
}

.notification-card :deep(.el-card__body) {
  padding: 0;
}

.loading-state {
  padding: 24px;
}

.empty-state {
  padding: 60px 0;
}
</style>
