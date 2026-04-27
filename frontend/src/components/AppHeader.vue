<template>
  <div class="app-header">
    <div class="header-left">
      <el-icon class="menu-toggle" @click="$emit('toggle-sidebar')" v-if="isMobile">
        <Fold />
      </el-icon>
      <div class="logo">
        <span class="logo-icon">🎫</span>
        <span class="logo-text">票务监控助手</span>
      </div>
    </div>
    <div class="header-right">
      <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
        <el-icon class="header-icon" @click="$router.push('/notifications')">
          <Bell />
        </el-icon>
      </el-badge>
      <el-dropdown trigger="click">
        <span class="user-info">
          <el-avatar :size="32" class="user-avatar">
            {{ username.charAt(0).toUpperCase() }}
          </el-avatar>
          <span class="username">{{ username }}</span>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="$router.push('/settings')">
              <el-icon><Setting /></el-icon>个人设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'

defineEmits(['toggle-sidebar'])

const authStore = useAuthStore()
const notifStore = useNotificationsStore()

const username = computed(() => authStore.user?.username || '用户')
const unreadCount = computed(() => notifStore.unreadCount)

const isMobile = ref(window.innerWidth < 768)
function onResize() { isMobile.value = window.innerWidth < 768 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

function handleLogout() {
  authStore.logout()
}
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  font-size: 22px;
  cursor: pointer;
  color: var(--text-secondary);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.header-icon:hover {
  color: var(--primary-color);
}

.notification-badge {
  line-height: 1;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-avatar {
  background-color: var(--primary-color);
  color: #fff;
  font-size: 14px;
}

.username {
  font-size: 14px;
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .logo-text {
    display: none;
  }
  .username {
    display: none;
  }
}
</style>
