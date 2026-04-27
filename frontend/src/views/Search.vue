<template>
  <div class="page-container">
    <h2 class="page-title">搜索演出</h2>

    <!-- 搜索栏 -->
    <el-card class="search-bar" shadow="never">
      <el-form :inline="true" @submit.prevent="handleSearch" class="search-form">
        <el-form-item class="search-input">
          <el-input v-model="keyword" placeholder="输入演出名称、艺人..." size="large"
            clearable prefix-icon="Search" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-select v-model="platform" placeholder="全部平台" size="large" clearable style="width: 140px">
            <el-option label="全部平台" value="" />
            <el-option label="大麦" value="damai" />
            <el-option label="猫眼" value="maoyan" />
            <el-option label="纷玩岛" value="funwandao" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" @click="handleSearch" :loading="searching">
            <el-icon><Search /></el-icon>搜索
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 搜索结果 -->
    <div class="search-results">
      <div v-if="searching" class="loading-state">
        <el-skeleton v-for="i in 3" :key="i" :rows="3" animated style="margin-bottom: 16px" />
      </div>
      <div v-else-if="searched && results.length === 0" class="empty-state">
        <el-empty description="未找到相关演出，换个关键词试试" />
      </div>
      <EventCard v-for="(event, idx) in results" :key="idx" :event="event"
        @add-monitor="openMonitorDialog" />
    </div>

    <!-- 添加监控对话框 -->
    <el-dialog v-model="dialogVisible" title="添加监控" width="480px" :close-on-click-modal="false">
      <el-form :model="monitorForm" label-width="80px">
        <el-form-item label="演出名称">
          <el-input :model-value="monitorForm.event_name" disabled />
        </el-form-item>
        <el-form-item label="平台">
          <el-input :model-value="monitorForm.platform" disabled />
        </el-form-item>
        <el-form-item label="目标场次">
          <el-select v-model="monitorForm.target_session" placeholder="选择场次（可选）" clearable style="width: 100%"
            :loading="loadingSessions" loading-text="正在获取场次..." no-data-text="该演出暂无场次信息">
            <el-option v-for="s in currentSessions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="检查间隔">
          <el-input-number v-model="monitorForm.check_interval" :min="30" :max="3600" :step="30" />
          <span style="margin-left: 8px; color: var(--text-secondary)">秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmMonitor" :loading="submitting">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { searchEvents, getEventDetail } from '../api/search'
import { useTasksStore } from '../stores/tasks'
import EventCard from '../components/EventCard.vue'
import type { EventInfo } from '../components/EventCard.vue'

const keyword = ref('')
const platform = ref('')
const searching = ref(false)
const searched = ref(false)
const results = ref<EventInfo[]>([])

const tasksStore = useTasksStore()
const dialogVisible = ref(false)
const submitting = ref(false)
const currentSessions = ref<string[]>([])
const loadingSessions = ref(false)

const monitorForm = reactive({
  event_name: '',
  event_url: '',
  platform: '',
  target_session: '',
  check_interval: 60
})

async function handleSearch() {
  if (!keyword.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  searching.value = true
  searched.value = true
  try {
    const res = await searchEvents({ keyword: keyword.value, platform: platform.value || undefined })
    results.value = res.data || []
  } catch (e: any) {
    ElMessage.error('搜索失败，请稍后重试')
    results.value = []
  } finally {
    searching.value = false
  }
}

function openMonitorDialog(event: EventInfo) {
  monitorForm.event_name = event.name
  monitorForm.event_url = event.url
  monitorForm.platform = event.platform
  monitorForm.target_session = ''
  monitorForm.check_interval = 60
  currentSessions.value = []
  dialogVisible.value = true

  // 异步获取场次列表
  fetchSessions(event)
}

async function fetchSessions(event: EventInfo) {
  // 从 URL 中提取 event_id（大麦格式: id=xxx）
  let eventId = ''
  if (event.url && event.url.includes('id=')) {
    eventId = event.url.split('id=').pop()?.split('&')[0] || ''
  }
  if (!eventId) return

  loadingSessions.value = true
  try {
    const res = await getEventDetail(eventId, event.platform)
    const sessions = res.data?.sessions || []
    currentSessions.value = sessions
  } catch (e: any) {
    console.error('获取场次失败', e)
    currentSessions.value = []
  } finally {
    loadingSessions.value = false
  }
}

async function confirmMonitor() {
  submitting.value = true
  try {
    await tasksStore.addTask({
      event_name: monitorForm.event_name,
      event_url: monitorForm.event_url,
      platform: monitorForm.platform,
      target_session: monitorForm.target_session || undefined,
      check_interval: monitorForm.check_interval
    })
    ElMessage.success('监控任务已添加')
    dialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
}

.search-bar {
  border-radius: 12px;
  margin-bottom: 20px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.search-results {
  margin-top: 8px;
}

.loading-state, .empty-state {
  padding: 40px 0;
}

@media (max-width: 768px) {
  .search-form {
    flex-direction: column;
  }
  .search-form .el-form-item {
    margin-right: 0;
    margin-bottom: 8px;
    width: 100%;
  }
  .search-input :deep(.el-input) {
    width: 100%;
  }
}
</style>
