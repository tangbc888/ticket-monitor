<template>
  <div class="page-container">
    <h2 class="page-title">个人设置</h2>

    <el-card class="settings-card" shadow="never">
      <el-form :model="settingsForm" label-width="120px" label-position="top">
        <h3 class="section-title">邮件通知配置</h3>
        <el-form-item label="通知邮箱地址">
          <el-input v-model="settingsForm.email" placeholder="请输入接收通知的邮箱地址"
            prefix-icon="Message" />
        </el-form-item>

        <el-divider />

        <h3 class="section-title">通知偏好</h3>
        <el-form-item label="WebSocket 实时通知">
          <el-switch v-model="settingsForm.ws_notification" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="邮件通知">
          <el-switch v-model="settingsForm.email_notification" active-text="开启" inactive-text="关闭" />
        </el-form-item>

        <el-divider />

        <h3 class="section-title">监控设置</h3>
        <el-form-item label="默认检查间隔（秒）">
          <el-input-number v-model="settingsForm.default_interval" :min="30" :max="3600" :step="30" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleSave" :loading="saving">
            保存设置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings } from '../api/settings'

const saving = ref(false)
const loading = ref(false)

const settingsForm = reactive({
  email: '',
  ws_notification: true,
  email_notification: false,
  default_interval: 60
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await getSettings()
    settingsForm.email = res.data.email || ''
    settingsForm.email_notification = res.data.email_notify_enabled ?? true
    settingsForm.ws_notification = res.data.websocket_notify_enabled ?? true
    settingsForm.default_interval = res.data.default_check_interval ?? 60
  } catch (e) {
    console.error('获取设置失败', e)
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  saving.value = true
  try {
    await updateSettings({
      email: settingsForm.email,
      email_notify_enabled: settingsForm.email_notification,
      websocket_notify_enabled: settingsForm.ws_notification,
    })
    ElMessage.success('设置已保存')
  } catch (e: any) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      ElMessage.error(detail.map((d: any) => d.msg).join('; '))
    } else if (typeof detail === 'string') {
      ElMessage.error(detail)
    } else {
      ElMessage.error('保存设置失败')
    }
    console.error(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
}

.settings-card {
  border-radius: 12px;
  max-width: 600px;
}

.settings-card :deep(.el-card__body) {
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  margin-top: 0;
}
</style>
