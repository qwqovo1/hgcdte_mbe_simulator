<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="page-container">
        <div class="breadcrumb">
          <button @click="$router.push('/model')" class="btn-back">
            <span class="icon">⬅</span> <span class="btn-text">返回模型目录</span>
          </button>
        </div>

        <h1 class="page-title">红外高温计 (Infrared Pyrometer)</h1>

        <!-- 3D 模型展示区域 -->
        <div class="model-card">
          <div class="card-header">
            <div class="header-left">
              <span class="status-badge" :class="{ 'loading-status': loading }">
                {{ loading ? '模型同步中...' : 'GPU 强化渲染模式' }}
              </span>
              <h3>高保真物理组件预览</h3>
            </div>
            <div class="header-right">
              <button @click="resetCamera" class="btn-mini">重置视角</button>
            </div>
          </div>

          <div ref="sceneContainer" class="three-container">
            <div v-if="loading" class="loader-overlay">
              <div class="loading-box">
                <div class="spinner-modern"></div>
                <div class="progress-wrapper">
                  <div class="progress-fill" :style="{ width: progress + '%' }"></div>
                </div>
                <p class="loading-text">正在加载 3D 资源... {{ progress }}%</p>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <div class="footer-grid">
              <div class="control-tip">操作：左键旋转 | 右键平移 | 滚轮缩放</div>
              <div class="tech-tag">材质：工业级不锈钢 / 锗(Ge)镜头</div>
            </div>
          </div>
        </div>

        <!-- 学术介绍区域 -->
        <div class="academic-container">
          <!-- 1. 设备背景 -->
          <div class="text-card info-card full-width">
            <h2 class="section-title">一、设备背景与重要性</h2>
            <p class="content-p">
              在分子束外延（MBE）实验中，精确测量和控制衬底温度是至关重要的，因为外延层的质量高度依赖于温度条件。
              红外高温计通过检测物体发出的红外辐射来推断其表面温度，是 MBE 系统中最核心的<strong>非接触式</strong>测温手段。
            </p>
            <div class="device-grid">
              <div class="device-item highlighted">1. 红外高温计 (Infrared Pyrometer) —— MBE系统首选</div>
              <div class="device-item">2. 热电偶 (Thermocouple)</div>
              <div class="device-item">3. 光学高温计 (Optical Pyrometer)</div>
              <div class="device-item">4. 原位温度监控传感器</div>
            </div>
          </div>

          <!-- 2. 物理原理 & 3. 结构与应用 (黄金比例布局) -->
          <div class="golden-ratio-grid">
            <div class="text-card primary-info">
              <h2 class="section-title">二、物理原理：黑体辐射定律</h2>
              <p class="content-p highlight-p">
                基于普朗克黑体辐射定律，任何高于绝对零度的物体都会向外发射电磁辐射，其强度取决于温度和表面发射率。
              </p>
              <div class="logic-list">
                <div class="logic-item">
                  <div class="logic-num">1</div>
                  <div class="logic-content"><strong>热辐射收集：</strong> 镜头聚焦衬底红外辐射。</div>
                </div>
                <div class="logic-item">
                  <div class="logic-num">2</div>
                  <div class="logic-content"><strong>信号转换：</strong> 探测器将红外光转为电信号。</div>
                </div>
                <div class="logic-item">
                  <div class="logic-num">3</div>
                  <div class="logic-content"><strong>线性换算：</strong> 应用斯特藩-玻尔兹曼定律计算绝对温度。</div>
                </div>
              </div>
              <div class="formula-box">
                <code>T = k / log(R + 1)</code>
                <span class="formula-desc">公式说明：T 为温度，R 为探测辐射强度，k 为发射率常数</span>
              </div>
            </div>

            <div class="text-card secondary-info">
              <h2 class="section-title">三、结构与注意事项</h2>
              <h4 class="sub-title">外观结构</h4>
              <ul class="academic-list">
                <li><strong>金属外壳：</strong> 工业级不锈钢，高真空兼容</li>
                <li><strong>瞄准窗口：</strong> 采用透红外 Ge 材质</li>
                <li><strong>光学系统：</strong> 内置 1°/3° 视场透镜组</li>
              </ul>
              <h4 class="sub-title mt-20">应用重点</h4>
              <ul class="academic-list warning">
                <li><strong>发射率标定：</strong> GaAs/Si 必须准确设定</li>
                <li><strong>干扰防护：</strong> 屏蔽腔内热灯丝直射</li>
                <li><strong>清洁维护：</strong> 窗口需定期除污</li>
              </ul>
            </div>
          </div>

          <!-- 4. 总结表 -->
          <div class="summary-section">
            <div class="summary-table">
              <div class="table-header">
                <span>项目名称</span>
                <span>详细内容</span>
              </div>
              <div class="table-body">
                <div class="table-row"><span>设备类型</span><span class="bright">红外高温计 (Infrared Pyrometer)</span></div>
                <div class="table-row"><span>测量方式</span><span class="bright">非接触式</span></div>
                <div class="table-row"><span>测温精度</span><span class="bright">±1°C 左右</span></div>
                <div class="table-row"><span>温度量程</span><span class="bright">~300°C 至 2000°C</span></div>
                <div class="table-row"><span>应用场景</span><span class="bright">MBE 衬底温度原位监控</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import Sidebar from '../components/Sidebar.vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

export default {
  name: 'PyrometerDisplay',
  components: { Sidebar },
  data() {
    return {
      loading: true,
      progress: 0,
      modelUrl: '/models/red_1.glb'
    }
  },
  mounted() {
    this.initThree();
    this.loadModel();
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.onWindowResize);
    if (this.animationId) cancelAnimationFrame(this.animationId);
    if (this.renderer) {
      this.renderer.dispose();
      this.renderer.forceContextLoss();
    }
  },
  methods: {
    initThree() {
      const container = this.$refs.sceneContainer;
      this.scene = new THREE.Scene();
      this.scene.background = new THREE.Color(0x0a0a12);

      this.camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
      this.camera.position.set(4, 3, 4);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setSize(container.clientWidth, container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 2.0;
      container.appendChild(this.renderer.domElement);

      const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 2.0);
      this.scene.add(hemiLight);

      const mainLight = new THREE.DirectionalLight(0xffffff, 3.0);
      mainLight.position.set(2, 5, 4);
      this.scene.add(mainLight);

      const fillLight = new THREE.DirectionalLight(0x00c7ff, 2.0);
      fillLight.position.set(-4, 2, 2);
      this.scene.add(fillLight);

      const backLight = new THREE.DirectionalLight(0xffffff, 2.5);
      backLight.position.set(0, 3, -5);
      this.scene.add(backLight);

      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      window.addEventListener('resize', this.onWindowResize);
    },

    loadModel() {
      const loader = new GLTFLoader();
      loader.load(
        this.modelUrl,
        (gltf) => {
          const model = gltf.scene;
          model.traverse((child) => {
            if (child.isMesh) {
              child.material.envMapIntensity = 2.0;
            }
          });
          const box = new THREE.Box3().setFromObject(model);
          const center = box.getCenter(new THREE.Vector3());
          const size = box.getSize(new THREE.Vector3());
          const scale = 3.0 / Math.max(size.x, size.y, size.z);
          model.scale.set(scale, scale, scale);
          model.position.sub(center.multiplyScalar(scale));
          this.scene.add(model);
          this.loading = false;
          this.animate();
        },
        (xhr) => { this.progress = Math.round((xhr.loaded / xhr.total) * 100); }
      );
    },

    animate() {
      this.animationId = requestAnimationFrame(this.animate);
      if (this.controls) this.controls.update();
      if (this.renderer) this.renderer.render(this.scene, this.camera);
    },

    onWindowResize() {
      const container = this.$refs.sceneContainer;
      if (!container) return;
      this.camera.aspect = container.clientWidth / container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(container.clientWidth, container.clientHeight);
    },

    resetCamera() {
      this.camera.position.set(4, 3, 4);
      this.controls.target.set(0, 0, 0);
    }
  }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background-color: #020205; }
.main-content { margin-left: var(--sidebar-width); flex: 1; padding: 25px; transition: margin-left 0.3s ease; }
.page-container { max-width: 1400px; margin: 0 auto; }

.btn-back {
  background: rgba(30, 30, 50, 0.9);
  border: 1px solid #444;
  color: #00c7ff;
  padding: 10px 22px;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}
.btn-back:hover { border-color: #00c7ff; background: rgba(0, 199, 255, 0.1); }

.page-title { color: #ffffff; margin: 20px 0; font-weight: 300; }

.model-card { background: #11111d; border: 1px solid #333; border-radius: 12px; overflow: hidden; margin-bottom: 30px; }
.card-header { padding: 15px 25px; background: #1a1a2e; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h3 { color: #ffffff; font-size: 16px; margin: 0; }
.status-badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; background: #00c853; color: #fff; white-space: nowrap; }
.loading-status { background: #ff9100; animation: pulse 1.5s infinite; }

.three-container { width: 100%; height: 500px; background: #0a0a12; position: relative; }

.loader-overlay { position: absolute; inset: 0; background: #0a0a12; display: flex; justify-content: center; align-items: center; z-index: 100; }
.loading-box { width: 320px; max-width: 90%; text-align: center; }
.spinner-modern { width: 45px; height: 45px; border: 3px solid rgba(0, 199, 255, 0.1); border-top: 3px solid #00c7ff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
.progress-wrapper { width: 100%; height: 4px; background: #1f1f35; border-radius: 2px; margin-bottom: 15px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00c7ff, #0078ff); transition: width 0.3s ease; }
.loading-text { color: #8888a0; font-size: 13px; }

.card-footer { padding: 12px 25px; background: #1a1a2e; border-top: 1px solid #333; }
.footer-grid { display: flex; justify-content: space-between; color: #6a6a85; font-size: 12px; flex-wrap: wrap; gap: 8px; }

.btn-mini { background: transparent; border: 1px solid #444466; color: #aaaabf; padding: 5px 12px; border-radius: 4px; cursor: pointer; }

/* 学术文字部分 */
.academic-container { display: flex; flex-direction: column; gap: 20px; }
.text-card { background: #161625; border: 1px solid #333; border-radius: 12px; padding: 30px; color: #ffffff; }

.section-title { color: #00c7ff; font-size: 22px; margin-bottom: 20px; border-left: 4px solid #00c7ff; padding-left: 15px; }
.sub-title { color: #00c7ff; font-size: 16px; margin: 15px 0 10px; }
.mt-20 { margin-top: 20px; }

.content-p { color: #e0e0e0; font-size: 16px; line-height: 1.8; margin-bottom: 15px; }
.highlight-p { color: #ffffff; font-weight: 500; }

.device-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px; }
.device-item { background: #0a0a16; padding: 15px; border-radius: 8px; border: 1px solid #333; color: #a0a0a0; font-size: 14px; }
.device-item.highlighted { border-color: #00ff88; color: #00ff88; background: rgba(0, 255, 136, 0.05); }

.golden-ratio-grid { display: flex; gap: 20px; }
.primary-info { flex: 0 0 61.8%; }
.secondary-info { flex: 1; }

.logic-list { margin: 25px 0; }
.logic-item { display: flex; gap: 15px; margin-bottom: 18px; align-items: flex-start; }
.logic-num { background: #00c7ff; color: #000; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; display: flex; justify-content: center; align-items: center; flex-shrink: 0; }
.logic-content { color: #ffffff; font-size: 15px; line-height: 1.6; }

.formula-box { background: #000; border: 1px solid #00ff88; padding: 20px; border-radius: 12px; text-align: center; margin-top: 25px; }
.formula-box code { font-size: 26px; color: #00ff88; font-family: 'Courier New', Courier, monospace; }
.formula-box .formula-desc { color: #a0a0a0; font-size: 12px; display: block; margin-top: 10px; }

.academic-list { list-style: none; padding: 0; }
.academic-list li { color: #e0e0e0; font-size: 15px; padding: 8px 0; padding-left: 20px; position: relative; }
.academic-list li::before { content: '▪'; color: #00c7ff; position: absolute; left: 0; }
.academic-list.warning li::before { color: #ff9100; }

.summary-table { background: #1a1a2e; border: 1px solid #444; border-radius: 12px; overflow: hidden; }
.table-header { display: flex; background: #00c7ff; color: #000; font-weight: bold; padding: 15px 20px; }
.table-header span, .table-row span { flex: 1; }
.table-body {}
.table-row { display: flex; padding: 15px 20px; border-bottom: 1px solid #333; font-size: 15px; color: #00c7ff; }
.table-row .bright { color: #ffffff !important; }

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }

/* ━━━ 手机适配 ━━━ */
@media (max-width: 768px) {
  .main-content { margin-left: 60px; padding: 12px; }
  .page-title { font-size: 18px; }
  .three-container { height: 280px; }
  .card-header { padding: 10px 12px; }
  .header-left h3 { font-size: 12px; }
  .card-footer { padding: 8px 12px; }
  .footer-grid { flex-direction: column; }
  .btn-back { padding: 8px 12px; font-size: 12px; }
  .btn-text { display: none; }

  .text-card { padding: 18px 14px; }
  .section-title { font-size: 17px; padding-left: 10px; }
  .content-p { font-size: 14px; }
  .device-grid { grid-template-columns: 1fr; gap: 10px; }
  .device-item { padding: 12px; font-size: 13px; }

  .golden-ratio-grid { flex-direction: column; }
  .primary-info { flex: unset; }
  .secondary-info { flex: unset; }

  .logic-content { font-size: 13px; }
  .formula-box code { font-size: 18px; }
  .formula-box { padding: 15px; }

  .academic-list li { font-size: 13px; }

  .table-header { padding: 12px 14px; font-size: 13px; }
  .table-row { padding: 12px 14px; font-size: 13px; flex-wrap: wrap; }
}

@media (max-width: 480px) {
  .three-container { height: 220px; }
  .page-title { font-size: 16px; }
  .section-title { font-size: 15px; }
}
</style>