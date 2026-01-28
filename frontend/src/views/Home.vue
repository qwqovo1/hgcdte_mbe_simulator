        <template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="home-container">
        <!-- 黄金比例布局: 左侧61.8%, 右侧38.2% -->
        <div class="content-wrapper">
          <div class="primary-section">
            <h1 class="page-title">分子束外延数字孪生系统</h1>
            <div class="intro-card">
              <h2>项目简介</h2>
              <p>
                本系统是基于分子束外延（Molecular Beam Epitaxy, MBE）技术开发的数字孪生仿真平台。
                通过构建MBE设备与工艺过程的虚拟映射，实现对薄膜外延生长过程的实时监控、
                仿真预测与智能优化。
              </p>
            </div>

            <div class="intro-card">
              <h2>技术背景</h2>
              <p>
                分子束外延是一种在超高真空环境下，通过精确控制原子或分子束流，
                在衬底表面逐层生长高质量单晶薄膜的先进技术。该技术广泛应用于
                半导体器件、光电子器件、量子器件等前沿领域的材料制备。
              </p>
            </div>

            <div class="intro-card">
              <h2>系统功能</h2>
              <ul class="feature-list">
                <li>🔬 <strong>工艺参数监控</strong>：实时采集并展示温度、压力、束流等关键参数</li>
                <li>📈 <strong>生长过程仿真</strong>：基于物理模型模拟薄膜逐层生长过程</li>
                <li>🤖 <strong>AI辅助优化</strong>：利用机器学习算法优化工艺参数配置</li>
                <li>🎨 <strong>三维可视化</strong>：直观展示薄膜微观结构与表面形貌</li>
              </ul>
            </div>
          </div>

          <div class="secondary-section">
            <div class="info-card">
              <h3>系统状态</h3>
              <div class="status-item">
                <span class="status-dot online"></span>
                <span>后端服务: 运行中</span>
              </div>
              <div class="status-item">
                <span class="status-dot online"></span>
                <span>数据库: 已连接</span>
              </div>
            </div>

            <div class="info-card">
              <h3>快速导航</h3>
              <div class="quick-links">
                <router-link to="/model" class="quick-link">
                  📊 模型展示
                </router-link>
                <router-link to="/experiment" class="quick-link">
                  🔬 实验模块
                </router-link>
              </div>
            </div>

            <div class="info-card">
              <h3>版本信息</h3>
              <p>当前版本: v1.0.1</p>
              <p>更新日期: 2026年</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'

export default {
  name: 'Home',
  components: {
    Sidebar
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  margin-left: var(--sidebar-width);
  flex: 1;
  padding: 30px;
  background-color: var(--bg-color);
}

.home-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  color: var(--text-color);
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid var(--primary-color);
}

/* 黄金比例布局 */
.content-wrapper {
  display: flex;
  gap: 30px;
}

.primary-section {
  flex: 0 0 61.8%;
}

.secondary-section {
  flex: 0 0 calc(38.2% - 30px);
}

/* 卡片样式 */
.intro-card, .info-card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.intro-card:hover, .info-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

.intro-card h2 {
  font-size: 20px;
  color: var(--primary-color);
  margin-bottom: 15px;
}

.intro-card p {
  line-height: 1.8;
  color: #606266;
  text-align: justify;
}

.feature-list {
  list-style: none;
  padding: 0;
}

.feature-list li {
  padding: 10px 0;
  line-height: 1.6;
  color: #606266;
  border-bottom: 1px dashed var(--border-color);
}

.feature-list li:last-child {
  border-bottom: none;
}

/* 信息卡片 */
.info-card h3 {
  font-size: 16px;
  color: var(--text-color);
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.status-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 10px;
}

.status-dot.online {
  background-color: #67c23a;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.6);
}

.quick-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-link {
  display: block;
  padding: 12px 15px;
  background: var(--bg-color);
  border-radius: 6px;
  text-decoration: none;
  color: var(--text-color);
  transition: all 0.3s ease;
}

.quick-link:hover {
  background: var(--primary-color);
  color: white;
}

.info-card p {
  font-size: 14px;
  color: #909399;
  margin: 5px 0;
}
</style>