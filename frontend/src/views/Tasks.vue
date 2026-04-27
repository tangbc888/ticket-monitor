<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">监控任务</h2>
      <el-button type="primary" @click="openAddDialog">
        <el-icon><Plus /></el-icon>手动添加任务
      </el-button>
    </div>

    <div v-if="tasksStore.loading" class="loading-state">
      <el-skeleton v-for="i in 3" :key="i" :rows="3" animated style="margin-bottom: 16px" />
    </div>

    <div v-else-if="tasksStore.tasks.length === 0" class="empty-state">
      <el-empty description="暂无监控任务，请先搜索演出并添加监控">
        <el-button type="primary" @click="$router.push('/search')">去搜索演出</el-button>
      </el-empty>
    </div>

    <div v-else>
      <TaskCard v-for="task in tasksStore.tasks" :key="task.id" :task="task"
        @edit="openEditDialog" />
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑任务' : '添加任务'" width="500px">
      <el-form :model="taskForm" :rules="formRules" ref="formRef" label-width="90px">
        <el-form-item label="演出名称" prop="event_name">
          <el-input v-model="taskForm.event_name" placeholder="请输入演出名称" />
        </el-form-item>
        <el-form-item label="演出链接" prop="event_url">
          <el-input v-model="taskForm.event_url" placeholder="请输入演出页面链接" />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-select v-model="taskForm.platform" placeholder="选择平台" style="width: 100%">
            <el-option label="大麦" value="大麦" />
            <el-option label="猫眼" value="猫眼" />
            <el-option label="纷玩岛" value="纷玩岛" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标场次">
          <el-input v-model="taskForm.target_session" placeholder="选填，如：2026-05-01 19:30" />
        </el-form-item>
        <el-form-item label="检查间隔">
          <el-input-number v-model="taskForm.check_interval" :min="30" :max="3600" :step="30" />
          <span style="margin-left: 8px; color: var(--text-secondary)">秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存修改' : '添加任务' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useTasksStore } from '../stores/tasks'
import type { Task } from '../stores/tasks'
import TaskCard from '../components/TaskCard.vue'

const tasksStore = useTasksStore()
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(0)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const taskForm = reactive({
  event_name: '',
  event_url: '',
  platform: '',
  target_session: '',
  check_interval: 60
})

const formRules: FormRules = {
  event_name: [{ required: true, message: '请输入演出名称', trigger: 'blur' }],
  event_url: [{ required: true, message: '请输入演出链接', trigger: 'blur' }],
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }]
}

function openAddDialog() {
  isEdit.value = false
  Object.assign(taskForm, { event_name: '', event_url: '', platform: '', target_session: '', check_interval: 60 })
  dialogVisible.value = true
}

function openEditDialog(task: Task) {
  isEdit.value = true
  editId.value = task.id
  Object.assign(taskForm, {
    event_name: task.event_name,
    event_url: task.event_url,
    platform: task.platform,
    target_session: task.target_session || '',
    check_interval: task.check_interval
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await tasksStore.editTask(editId.value, { ...taskForm })
      ElMessage.success('修改成功')
    } else {
      await tasksStore.addTask({ ...taskForm })
      ElMessage.success('任务已添加')
    }
    dialogVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  tasksStore.fetchTasks()
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

.loading-state {
  padding: 20px 0;
}

.empty-state {
  padding: 60px 0;
}
</style>
