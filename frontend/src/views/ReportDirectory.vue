<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <h1 class="page-title">实验报告中心</h1>

      <div class="directory-container">
        <!-- 左侧入口区 -->
        <div class="dir-grid">
          <button class="entry-card" @click="$router.push('/reports/mbe-sim')">
            <div class="card-icon">📄</div>
            <div class="card-info">
              <h3>分子束模拟仿真实验报告单</h3>
              <p>支持在线查阅、编辑及报告管理</p>
            </div>
            <div class="card-status">已激活</div>
          </button>

          <button class="entry-card disabled">
            <div class="card-icon">🔒</div>
            <div class="card-info">
              <h3>成分梯度分析报告单</h3>
              <p>更多模块正在开发中...</p>
            </div>
          </button>
        </div>

        <!-- 右侧规则简介栏 -->
        <aside class="rule-sidebar">
          <div class="sidebar-section">
            <h4>🔬 计算模型简介</h4>
            <p>系统目前采用<b>加权仿真物理演化模型 (WPM-v1)</b>。该模型通过模拟MBE腔体内的蒸气压动力学，结合实时工艺参数进行积分运算。</p>
          </div>

          <div class="sidebar-section">
            <h4>📈 参数影响逻辑</h4>
            <ul>
              <li><strong>Ga源温度:</strong> 对数相关，主导原子束流通量。</li>
              <li><strong>生长速率:</strong> 线性权重，修正原子沉积效率。</li>
              <li><strong>衬底温度:</strong> 窗口化影响，涉及原子表面迁移率。</li>
            </ul>
          </div>

          <div class="sidebar-section alert-rule">
            <h4>⚠️ 报警保护机制</h4>
            <div class="rule-item yellow">
              <span>● 超限 1.5x:</span> 工艺窗口偏移提示。
            </div>
            <div class="rule-item red">
              <span>● 超限 2.0x:</span> 强制暂停以保护虚拟硬件。
            </div>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
export default {
  name: 'ReportDirectory',
  components: { Sidebar }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background: #05050a; }
.main-content { margin-left: var(--sidebar-width); flex: 1; padding: 40px; transition: margin-left 0.3s ease; }
.page-title { color: #fff; margin-bottom: 40px; font-weight: 300; border-bottom: 1px solid #1e1e35; padding-bottom: 10px; }

.directory-container { display: flex; gap: 40px; align-items: flex-start; }

.dir-grid { flex: 0 0 61.8%; display: flex; flex-direction: column; gap: 20px; }

.entry-card {
  width: 100%; min-height: 100px; background: #11111d; border: 1px solid #2d2d44;
  border-radius: 12px; display: flex; align-items: center; padding: 20px 25px;
  color: white; cursor: pointer; transition: 0.3s; position: relative; text-align: left;
}
.entry-card:hover { border-color: #00c7ff; background: #161625; transform: translateX(10px); }
.card-icon { font-size: 36px; margin-right: 20px; flex-shrink: 0; }
.card-info h3 { font-size: 17px; margin-bottom: 5px; margin-top: 0; }
.card-info p { color: #6a6a85; font-size: 13px; margin: 0; }
.card-status { position: absolute; right: 15px; top: 12px; font-size: 11px; color: #00ff88; background: rgba(0,255,136,0.1); padding: 2px 8px; border-radius: 4px; }

.disabled { opacity: 0.4; cursor: not-allowed; filter: grayscale(1); }

.rule-sidebar {
  flex: 1; background: rgba(22, 22, 37, 0.4); border: 1px solid #1e1e35;
  padding: 25px; border-radius: 12px; display: flex; flex-direction: column; gap: 25px;
}
.sidebar-section h4 { color: #00c7ff; font-size: 16px; margin-bottom: 12px; border-left: 3px solid #00c7ff; padding-left: 10px; margin-top: 0; }
.sidebar-section p { color: #8888a0; font-size: 13px; line-height: 1.6; margin: 0; }
.sidebar-section ul { padding-left: 15px; margin: 0; }
.sidebar-section li { color: #8888a0; font-size: 13px; margin-bottom: 8px; }

.alert-rule .rule-item { font-size: 13px; margin: 10px 0; padding: 8px; border-radius: 4px; }
.yellow { color: #ff9100; background: rgba(255,145,0,0.1); }
.red { color: #ff3d00; background: rgba(255,61,0,0.1); }

/* ━━━ 手机适配 ━━━ */
@media (max-width: 768px) {
  .main-content { margin-left: 60px; padding: 15px; }
  .page-title { font-size: 20px; margin-bottom: 20px; }
  .directory-container { flex-direction: column; gap: 20px; }
  .dir-grid { flex: unset; width: 100%; }
  .entry-card { padding: 15px; flex-wrap: wrap; }
  .entry-card:hover { transform: none; }
  .card-icon { font-size: 28px; margin-right: 12px; }
  .card-info h3 { font-size: 14px; }
  .card-info p { font-size: 12px; }
  .card-status { top: 8px; right: 10px; font-size: 10px; }
  .rule-sidebar { padding: 18px; }
  .sidebar-section h4 { font-size: 14px; }
}
</style>