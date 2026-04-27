<template>
  <div class="page-container">
    <h2 class="page-title">仪表盘</h2>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(255,107,107,0.1); color: #FF6B6B">
            <el-icon :size="28"><Monitor /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ activeCount }}</div>
            <div class="stat-label">活跃监控</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(230,162,60,0.1); color: #E6A23C">
            <el-icon :size="28"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ unreadCount }}</div>
            <div class="stat-label">未读通知</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(103,194,58,0.1); color: #67C23A">
            <el-icon :size="28"><Platform /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ platformCount }}</div>
            <div class="stat-label">监控平台</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近通知 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <span>最近通知</span>
          <el-button text type="primary" @click="$router.push('/notifications')">查看全部</el-button>
        </div>
      </template>
      <div v-if="recentNotifications.length === 0" class="empty-state">
        <el-empty description="暂无通知" :image-size="80" />
      </div>
      <NotificationItem v-for="n in recentNotifications" :key="n.id" :notification="n"
        @read="notifStore.markRead" />
    </el-card>

    <!-- 活跃监控任务 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="section-header">
          <span>活跃监控任务</span>
          <el-button text type="primary" @click="$router.push('/tasks')">管理任务</el-button>
        </div>
      </template>
      <div v-if="tasksStore.loading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="activeTasks.length === 0" class="empty-state">
        <el-empty description="暂无活跃监控任务">
          <el-button type="primary" @click="$router.push('/search')">去搜索演出</el-button>
        </el-empty>
      </div>
      <TaskCard v-for="task in activeTasks" :key="task.id" :task="task" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useTasksStore } from '../stores/tasks'
import { useNotificationsStore } from '../stores/notifications'
import NotificationItem from '../components/NotificationItem.vue'
import TaskCard from '../components/TaskCard.vue'

const tasksStore = useTasksStore()
const notifStore = useNotificationsStore()

const activeCount = computed(() => tasksStore.tasks.filter(t => t.is_active).length)
const unreadCount = computed(() => notifStore.unreadCount)
const platformCount = computed(() => new Set(tasksStore.tasks.map(t => t.platform)).size)
const recentNotifications = computed(() => notifStore.notifications.slice(0, 5))
const activeTasks = computed(() => tasksStore.tasks.filter(t => t.is_active).slice(0, 5))

onMounted(() => {
  tasksStore.fetchTasks()
  notifStore.fetchNotifications()
})
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  margin-bottom: 12px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.section-card {
  border-radius: 12px;
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.empty-state {
  padding: 20px 0;
}

.loading-state {
  padding: 20px;
}
</style>
