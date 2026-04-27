<template>
  <el-card class="task-card" shadow="hover">
    <div class="task-header">
      <div class="task-platform">
        <el-tag :type="platformType" size="small">{{ task.platform }}</el-tag>
      </div>
      <el-switch v-model="isActive" @change="handleToggle"
        active-text="" inactive-text="" :loading="toggling" />
    </div>
    <div class="task-body">
      <h3 class="task-name">{{ task.event_name }}</h3>
      <div class="task-info">
        <div class="info-item">
          <el-icon><Ticket /></el-icon>
          <span>{{ task.target_session || '全部场次' }}</span>
        </div>
        <div class="info-item">
          <el-icon><Timer /></el-icon>
          <span>每 {{ task.check_interval }} 秒检查</span>
        </div>
        <div class="info-item" v-if="task.last_checked_at">
          <el-icon><Clock /></el-icon>
          <span>{{ formatTime(task.last_checked_at) }}</span>
        </div>
      </div>
    </div>
    <div class="task-actions">
      <el-button text type="primary" @click="$emit('edit', task)">
        <el-icon><Edit /></el-icon>编辑
      </el-button>
      <el-button text type="danger" @click="handleDelete">
        <el-icon><Delete /></el-icon>删除
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useTasksStore } from '../stores/tasks'
import type { Task } from '../stores/tasks'

const props = defineProps<{ task: Task }>()
const emit = defineEmits(['edit', 'deleted'])

const tasksStore = useTasksStore()
const isActive = ref(props.task.is_active)
const toggling = ref(false)

const platformType = (() => {
  const map: Record<string, string> = { '大麦': 'danger', '猫眼': '', '纷玩岛': 'success' }
  return map[props.task.platform] || 'info'
})()

function formatTime(time: string) {
  const d = new Date(time)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  return d.toLocaleDateString('zh-CN')
}

async function handleToggle(val: boolean) {
  toggling.value = true
  try {
    await tasksStore.editTask(props.task.id, { is_active: val })
    ElMessage.success(val ? '已开启监控' : '已暂停监控')
  } catch {
    isActive.value = !val
    ElMessage.error('操作失败')
  } finally {
    toggling.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除这个监控任务吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    })
    await tasksStore.removeTask(props.task.id)
    ElMessage.success('已删除')
    emit('deleted')
  } catch {}
}
</script>

<style scoped>
.task-card {
  margin-bottom: 12px;
  border-radius: 12px;
}

.task-card :deep(.el-card__body) {
  padding: 16px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-body {
  margin-bottom: 12px;
}

.task-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.task-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}

.task-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}
</style>
