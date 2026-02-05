<template>
  <div class="layout">
    <Sidebar />
    <main class="main-content">
      <div class="page-container">
        <!-- 返回目录按钮：符合 0.618 比例感，圆角矩形 -->
        <div class="breadcrumb">
          <button @click="$router.push('/model')" class="btn-back">
            <span class="icon">⬅</span> 返回模型目录
          </button>
        </div>

        <h1 class="page-title">模型展示</h1>
        <div class="model-card">
          <div class="card-header">
            <div class="header-left">
              <span class="status-badge" :class="{ 'loading-status': loading }">
                {{ loading ? '同步数据中' : 'GPU 实时渲染' }}
              </span>
              <h3>MBE 数字孪生设备预览</h3>
            </div>
            <div class="header-right">
              <button @click="resetCamera" class="btn-mini">重置视角</button>
            </div>
          </div>
          <div ref="sceneContainer" class="three-container">
            <!-- 现代感加载进度条 -->
            <div v-if="loading" class="loader-overlay">
              <div class="loading-box">
                <div class="spinner-modern"></div>
                <div class="progress-wrapper">
                  <div class="progress-fill" :style="{ width: progress + '%' }"></div>
                </div>
                <p class="loading-text">{{ progress < 100 ? `正在拉取云端模型... ${progress}%` : '资源初始化中...' }}</p>
              </div>
            </div>
          </div>
          <div class="card-footer">
            <div class="footer-grid">
              <div class="control-tip">操作：左键旋转 | 右键平移 | 滚轮缩放</div>
              <div class="cache-status">
                加载模式: <span :style="{ color: cacheHit ? '#00ff88' : '#aaa' }">
                  {{ cacheHit ? '🚀 缓存热启动 (秒开)' : '🌐 远程冷启动 (下载中)' }}
                </span>
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
import * as THREE from 'three' // 修正：恢复标准导入
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

export default {
  name: 'ModelDisplay',
  components: { Sidebar },
  data() {
    return {
      loading: true,
      progress: 0,
      cacheHit: false
    }
  },
  mounted() {
    this.initThree();
    this.loadModelWithCache();
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
      this.camera.position.set(12, 12, 12);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setSize(container.clientWidth, container.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.toneMapping = THREE.ReinhardToneMapping;
      this.renderer.toneMappingExposure = 2.2;
      container.appendChild(this.renderer.domElement);

      const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
      this.scene.add(ambientLight);

      const directionalLight = new THREE.DirectionalLight(0xffffff, 2.0);
      directionalLight.position.set(5, 10, 7);
      this.scene.add(directionalLight);

      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      window.addEventListener('resize', this.onWindowResize);
    },

    async loadModelWithCache() {
      const modelUrl = '/models/mbe_equipment.glb';
      const cacheName = 'mbe-3d-cache-v1';
      const loader = new GLTFLoader();

      try {
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(modelUrl);

        if (cachedResponse) {
          this.cacheHit = true;
          const blob = await cachedResponse.blob();
          const url = URL.createObjectURL(blob);
          loader.load(url, (gltf) => {
            this.processModel(gltf);
            URL.revokeObjectURL(url);
          });
        } else {
          loader.load(
            modelUrl,
            async (gltf) => {
              this.processModel(gltf);
              const response = await fetch(modelUrl);
              const cacheCopy = response.clone();
              cache.put(modelUrl, cacheCopy);
            },
            (xhr) => {
              this.progress = Math.round((xhr.loaded / xhr.total) * 100);
            }
          );
        }
      } catch (err) {
        loader.load(modelUrl, (gltf) => this.processModel(gltf));
      }
    },

    processModel(gltf) {
      this.model = gltf.scene;
      const box = new THREE.Box3().setFromObject(this.model);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const scale = 10 / Math.max(size.x, size.y, size.z);
      this.model.scale.set(scale, scale, scale);
      this.model.position.sub(center.multiplyScalar(scale));
      this.scene.add(this.model);
      this.loading = false;
      this.animate();
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
      this.camera.position.set(12, 12, 12);
      this.controls.target.set(0, 0, 0);
    }
  }
}
</script>

<style scoped>
.layout { display: flex; min-height: 100vh; background-color: #05050a; }
.main-content { margin-left: var(--sidebar-width); flex: 1; padding: 25px; }
.page-container { max-width: 1400px; margin: 0 auto; }

/* 按钮设计：圆角矩形，黄金比例长宽感 */
.breadcrumb { margin-bottom: 20px; }
.btn-back {
  background: rgba(22, 22, 37, 0.8);
  border: 1px solid #2d2d44;
  color: #00c7ff;
  padding: 10px 22px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-back:hover {
  background: rgba(0, 199, 255, 0.1);
  border-color: #00c7ff;
  transform: translateX(-5px);
}

.page-title { color: #fff; margin-bottom: 20px; font-weight: 300; }
.model-card { background: #11111d; border-radius: 12px; border: 1px solid #2d2d44; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
.card-header { padding: 15px 25px; background: #161625; border-bottom: 1px solid #2d2d44; display: flex; justify-content: space-between; align-items: center; }
.header-left { display: flex; align-items: center; gap: 15px; color: #e1e1e6; }
.status-badge { background: #00c853; color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 4px; }
.loading-status { background: #ff9100; animation: pulse 1.5s infinite; }
.three-container { width: 100%; height: 620px; position: relative; background: radial-gradient(circle at center, #1a1a2e 0%, #0a0a12 100%); }
.loader-overlay { position: absolute; inset: 0; background: #0a0a12; display: flex; justify-content: center; align-items: center; z-index: 100; }
.loading-box { width: 320px; text-align: center; }
.spinner-modern { width: 45px; height: 45px; border: 3px solid rgba(0, 199, 255, 0.1); border-top: 3px solid #00c7ff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
.progress-wrapper { width: 100%; height: 4px; background: #1f1f35; border-radius: 2px; margin-bottom: 15px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #00c7ff, #0078ff); transition: width 0.3s ease; }
.loading-text { color: #8888a0; font-size: 13px; }
.card-footer { padding: 12px 25px; background: #161625; border-top: 1px solid #2d2d44; }
.footer-grid { display: flex; justify-content: space-between; color: #6a6a85; font-size: 12px; }
.btn-mini { background: transparent; border: 1px solid #444466; color: #aaaabf; padding: 5px 12px; border-radius: 4px; cursor: pointer; }

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
</style>