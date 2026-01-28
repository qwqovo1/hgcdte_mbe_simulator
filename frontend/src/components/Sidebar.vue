<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>MBE数字孪生</h2>
    </div>
    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-text">{{ item.name }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  data() {
    return {
      menuItems: [
        { path: '/home', name: '首页', icon: '🏠' },
        { path: '/model', name: '模型展示', icon: '📊' },
        { path: '/experiment', name: '实验', icon: '🔬' }
      ]
    }
  },
  methods: {
    isActive(path) {
      return this.$route.path === path
    }
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
}

.sidebar-header {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 500;
}

.sidebar-nav {
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 25px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background-color: var(--primary-color);
  color: white;
}

.nav-icon {
  margin-right: 12px;
  font-size: 18px;
}

.nav-text {
  font-size: 15px;
}
</style>