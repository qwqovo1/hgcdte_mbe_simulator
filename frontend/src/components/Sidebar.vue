<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2 class="full-title">MBE数字孪生</h2>
      <h2 class="short-title">MBE</h2>
    </div>
    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        :title="item.name"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-text">{{ item.name }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
export default {
  name: 'Sidebar',
  data() {
    return {
      menuItems: [
        { path: '/home', name: '首页', icon: '🏠' },
        { path: '/model', name: '模型', icon: '📊' },
        { path: '/experiment', name: '实验', icon: '🔬' },
        { path: '/analysis', name: '智能分析和建议', icon: '🤖' },
        { path: '/reports', name: '报告', icon: '📁' }
      ]
    }
  },
  methods: {
    isActive(path) { return this.$route.path.startsWith(path) }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
  border-right: 1px solid rgba(255,255,255,0.05);
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px 10px;
  text-align: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.full-title {
  font-size: clamp(14px, 1.5vw, 18px);
  white-space: nowrap;
  margin: 0;
}
.short-title {
  display: none;
  font-size: 12px;
  margin: 0;
}

.sidebar-nav { padding: 15px 0; }
.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 15px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: 0.3s;
  white-space: nowrap;
}
.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}
.nav-item.active {
  background-color: var(--primary-color);
  color: white;
}
.nav-icon { margin-right: 10px; font-size: 18px; flex-shrink: 0; }
.nav-text { font-size: clamp(12px, 1.2vw, 15px); }

/* ━━━ 手机端：窄版侧边栏 ━━━ */
@media (max-width: 768px) {
  .sidebar {
    width: var(--sidebar-width-mobile, 60px);
  }
  .full-title { display: none; }
  .short-title { display: block; }
  .nav-text { display: none; }
  .nav-icon { margin-right: 0; font-size: 22px; }
  .nav-item { justify-content: center; padding: 18px 10px; }
  .sidebar-header { padding: 15px 5px; }
}
</style>