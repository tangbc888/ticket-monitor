<template>
  <div class="app-layout">
    <AppHeader @toggle-sidebar="sidebarVisible = !sidebarVisible" />
    <AppSidebar />
    <main class="main-content" :class="{ 'mobile': isMobile }">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useWebSocket } from '../composables/useWebSocket'
import { useAuthStore } from '../stores/auth'
import { useNotificationsStore } from '../stores/notifications'

const sidebarVisible = ref(true)
const isMobile = ref(window.innerWidth < 768)

function onResize() { isMobile.value = window.innerWidth < 768 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

const authStore = useAuthStore()
const notifStore = useNotificationsStore()
const { connect } = useWebSocket()

onMounted(async () => {
  await authStore.init()
  notifStore.fetchNotifications()
  connect()
})
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.main-content {
  margin-left: var(--sidebar-width);
  margin-top: var(--header-height);
  min-height: calc(100vh - var(--header-height));
  background: var(--bg-color);
}

.main-content.mobile {
  margin-left: 0;
  padding-bottom: 60px;
}
</style>
