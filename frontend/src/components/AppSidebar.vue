<template>
  <!-- PC端侧边栏 -->
  <div class="sidebar-pc" v-if="!isMobile">
    <el-menu :default-active="activeRoute" router class="sidebar-menu">
      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>
      <el-menu-item index="/search">
        <el-icon><Search /></el-icon>
        <span>搜索演出</span>
      </el-menu-item>
      <el-menu-item index="/tasks">
        <el-icon><Monitor /></el-icon>
        <span>监控任务</span>
      </el-menu-item>
      <el-menu-item index="/notifications">
        <el-icon><Bell /></el-icon>
        <span>通知中心</span>
      </el-menu-item>
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </el-menu-item>
    </el-menu>
  </div>

  <!-- 移动端底部导航 -->
  <div class="bottom-nav" v-if="isMobile">
    <router-link v-for="item in navItems" :key="item.path" :to="item.path"
      :class="['nav-item', { active: activeRoute === item.path }]">
      <el-icon :size="22"><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, Search, Monitor, Bell, Setting } from '@element-plus/icons-vue'

const route = useRoute()
const activeRoute = computed(() => route.path === '/' ? '/' : '/' + route.path.split('/')[1])

const isMobile = ref(window.innerWidth < 768)
function onResize() { isMobile.value = window.innerWidth < 768 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

const navItems = [
  { path: '/', icon: HomeFilled, label: '首页' },
  { path: '/search', icon: Search, label: '搜索' },
  { path: '/tasks', icon: Monitor, label: '监控' },
  { path: '/notifications', icon: Bell, label: '通知' },
  { path: '/settings', icon: Setting, label: '设置' }
]
</script>

<style scoped>
.sidebar-pc {
  width: var(--sidebar-width);
  height: calc(100vh - var(--header-height));
  position: fixed;
  top: var(--header-height);
  left: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.sidebar-menu {
  border-right: none;
  padding-top: 8px;
}

.sidebar-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 2px 8px;
  border-radius: 8px;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: rgba(255, 107, 107, 0.1);
  color: var(--primary-color);
}

/* 底部导航 */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: #fff;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 4px 0;
  min-width: 56px;
  transition: color 0.2s;
}

.nav-item.active {
  color: var(--primary-color);
}
</style>
