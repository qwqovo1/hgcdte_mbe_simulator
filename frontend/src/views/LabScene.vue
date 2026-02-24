<template>
  <div class="scene-container">
    <div ref="canvas" class="canvas-box"></div>
    <div v-if="loading" class="loader-overlay">
      <div class="spinner"></div>
      <p>正在初始化 MBE 真空室环境...</p>
    </div>
    <div v-if="hoveredParams" class="hover-tooltip"
      :style="{ left: tooltipPos.x + 'px', top: tooltipPos.y + 'px' }">{{ hoveredParams }}</div>
  </div>
</template>

<script>
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
export default {
  name: 'LabScene',
  emits: ['device-click'],
  props: {
    params: { type: Array, default: function() { return []; } },
    growing: { type: Boolean, default: false },
    paused: { type: Boolean, default: false }
  },
  data: function() {
    return {
      loading: true, hoveredParams: null, tooltipPos: {x:0,y:0},
      mouse: new THREE.Vector2(), raycaster: new THREE.Raycaster(),
      currentHover: null, originalEmissive: null,
      interactables: [], particleSystems: [], indicators: [],
      clock: new THREE.Clock(),
      deviceMeshes: {},
      growActive: false,
      growTime: 0,
      beamSpeedBase: 0.35,
      srcCoils: [],
      substrateFilm: null,
      depositLight: null
    };
  },
  watch: {
    params: {
      deep: true,
      handler: function(newParams) {
        if (!newParams || newParams.length < 10) return;
        this.applyVisuals(newParams);
      }
    },
    growing: function(val) {
      this.growActive = val;
      if (val) { this.onGrowStart(); }
      else if (!this.paused) { this.onGrowStop(); }
    },
    paused: function(val) {
      if (val) { this.growActive = false; }
      else if (this.growing) { this.growActive = true; }
    }
  },
  mounted: function() {
    this.initThree();
    this.build();
    this.loading = false;
    window.addEventListener('mousemove', this.onMove, false);
    window.addEventListener('click', this.onClick, false);
  },
  beforeUnmount: function() {
    window.removeEventListener('mousemove', this.onMove);
    window.removeEventListener('click', this.onClick);
    window.removeEventListener('resize', this.onResize);
    if (this.renderer) { this.renderer.dispose(); this.renderer.forceContextLoss(); }
    cancelAnimationFrame(this.frameId);
  },
  methods: {
    M: function(c,r,m,ex) {
      var cfg = {color:c, roughness:r, metalness:m};
      if (ex) { Object.assign(cfg, ex); }
      if (this.env) { cfg.envMap = this.env; cfg.envMapIntensity = 0.6; }
      return new THREE.MeshStandardMaterial(cfg);
    },
    GM: function(c,i) {
      return new THREE.MeshStandardMaterial({color:c, emissive:c, emissiveIntensity:i||1, roughness:0.4, metalness:0.2});
    },
    reg: function(mesh, name, label) {
      mesh.name = name;
      mesh.userData = {label: label};
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.interactables.push(mesh);
      this.deviceMeshes[name] = mesh;
    },
    led: function(g, x, y, z, c) {
      var s = new THREE.Mesh(new THREE.SphereGeometry(0.05,10,10), this.GM(c||0x00ff88, 1.0));
      s.position.set(x,y,z);
      g.add(s);
      this.indicators.push(s);
    },

    onGrowStart: function() {
      this.growTime = 0;
      var i;
      for (i = 0; i < this.particleSystems.length; i++) {
        var ps = this.particleSystems[i];
        ps.points.material.opacity = 0.85;
        ps.points.material.size = 0.08;
      }
      if (this.substrateFilm) {
        this.substrateFilm.visible = true;
        this.substrateFilm.scale.y = 0.01;
        this.substrateFilm.material.opacity = 0.1;
      }
      if (this.depositLight) { this.depositLight.intensity = 0; }
      if (this.chamberLight) {
        this.chamberLight.color.setHex(0x5599ff);
        this.chamberLight.intensity = 2.0;
      }
    },
    onGrowStop: function() {
      var i;
      for (i = 0; i < this.particleSystems.length; i++) {
        var ps = this.particleSystems[i];
        ps.points.material.opacity = 0.6;
        ps.points.material.size = 0.05;
      }
      if (this.chamberLight) {
        this.chamberLight.color.setHex(0x4488cc);
        this.chamberLight.intensity = 1.5;
      }
    },

    applyVisuals: function(p) {
      var self = this;
      var srcMap = {'Hg_Source':1, 'CdTe_Source':2, 'Te_Source':3};
      var name, mesh, ratio;
      for (name in srcMap) {
        mesh = self.deviceMeshes[name];
        if (mesh) {
          ratio = p[srcMap[name]].value / p[srcMap[name]].normal;
          mesh.material.emissive.setHex(0xff4400);
          mesh.material.emissiveIntensity = Math.min(ratio * 0.35, 1.2);
        }
      }
      mesh = self.deviceMeshes['Substrate_Heater'];
      if (mesh) {
        ratio = p[0].value / p[0].normal;
        mesh.material.emissive.setHex(0xff4400);
        mesh.material.emissiveIntensity = Math.min(ratio * 0.4, 1.5);
      }
      if (p[7]) { self.rotSpeed = (p[7].value / p[7].normal) * 0.5; }
      if (p[4] && self.particleSystems.length > 0) {
        ratio = p[4].value / p[4].normal;
        var psf = self.particleSystems[0];
        if (psf && psf.points && psf.points.material) {
          psf.points.material.opacity = Math.min(ratio * 0.6, 0.85);
          psf.points.material.size = 0.05 * Math.max(0.5, ratio);
        }
      }
      mesh = self.deviceMeshes['Cooling_System'];
      if (mesh && p[8]) {
        ratio = p[8].value / p[8].normal;
        if (ratio > 1.3) { mesh.material.emissive.setHex(0xff4400); mesh.material.emissiveIntensity = 0.2; }
        else { mesh.material.emissive.setHex(0x0055bb); mesh.material.emissiveIntensity = 0.1; }
      }
      mesh = self.deviceMeshes['Main_Chamber'];
      if (mesh && p[5] && self.chamberLight) {
        ratio = p[5].value / p[5].normal;
        self.chamberLight.intensity = 1.5 * Math.max(0.4, ratio);
      }
      if (self.growActive) {
        var cdteRatio = p[2].value / p[2].normal;
        self.beamSpeedBase = 0.2 + cdteRatio * 0.18;
        for (var si = 0; si < self.particleSystems.length; si++) {
          self.particleSystems[si].points.material.size = 0.04 + cdteRatio * 0.03;
        }
      }
    },

    initThree: function() {
      var c = this.$refs.canvas;
      this.scene = new THREE.Scene();

      // 更明亮、开阔的背景色 - 浅蓝灰色
      this.scene.background = new THREE.Color(0x3a4555);
      // 减弱雾效，增加空间感
      this.scene.fog = new THREE.Fog(0x3a4555, 40, 120);

      this.camera = new THREE.PerspectiveCamera(38, c.clientWidth/c.clientHeight, 0.1, 250);
      // 拉远相机，增加空间感
      this.camera.position.set(18, 14, 24);

      this.renderer = new THREE.WebGLRenderer({antialias:true});
      this.renderer.setSize(c.clientWidth, c.clientHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      // 提高曝光度
      this.renderer.toneMappingExposure = 2.0;
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      c.appendChild(this.renderer.domElement);

      // 更明亮的环境贴图
      var cRT = new THREE.WebGLCubeRenderTarget(256);
      var cCam = new THREE.CubeCamera(0.1,100,cRT);
      var ts = new THREE.Scene();
      ts.background = new THREE.Color(0x8899aa);
      ts.add(new THREE.AmbientLight(0xffffff, 5));
      cCam.update(this.renderer, ts);
      this.env = cRT.texture;

      // ===== 柔和明亮的照明系统 =====

      // 环境光 - 柔和的暖白色，提高强度
      this.scene.add(new THREE.AmbientLight(0xeef4ff, 1.2));

      // 半球光 - 天空色和地面色，更柔和
      var hemi = new THREE.HemisphereLight(0xddeeff, 0x8899aa, 1.0);
      this.scene.add(hemi);

      // 主方向光 - 柔和的日光感
      var dir1 = new THREE.DirectionalLight(0xfffaf0, 1.8);
      dir1.position.set(15, 25, 15);
      dir1.castShadow = true;
      dir1.shadow.mapSize.set(2048, 2048);
      dir1.shadow.camera.left = -20;
      dir1.shadow.camera.right = 20;
      dir1.shadow.camera.top = 20;
      dir1.shadow.camera.bottom = -20;
      dir1.shadow.bias = -0.0003;
      dir1.shadow.radius = 3;
      this.scene.add(dir1);

      // 补光 - 柔和暖色
      var dir2 = new THREE.DirectionalLight(0xfff0e0, 0.8);
      dir2.position.set(-12, 18, -8);
      this.scene.add(dir2);

      // 顶部柔和区域光
      var topLight1 = new THREE.PointLight(0xffffff, 1.0, 40);
      topLight1.position.set(0, 12, 0);
      this.scene.add(topLight1);

      var topLight2 = new THREE.PointLight(0xffffff, 0.8, 35);
      topLight2.position.set(-8, 11, -5);
      this.scene.add(topLight2);

      var topLight3 = new THREE.PointLight(0xffffff, 0.8, 35);
      topLight3.position.set(8, 11, 5);
      this.scene.add(topLight3);

      // 柔和的填充光
      this.scene.add(new THREE.PointLight(0xddeeff, 0.5, 25)).position.set(-15, 6, 10);
      this.scene.add(new THREE.PointLight(0xffeedd, 0.5, 25)).position.set(15, 6, -10);
      this.scene.add(new THREE.PointLight(0xffffff, 0.4, 20)).position.set(0, 5, 15);

      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.06;
      this.controls.rotateSpeed = 0.4;
      this.controls.zoomSpeed = 0.7;
      this.controls.panSpeed = 0.3;
      this.controls.maxPolarAngle = Math.PI * 0.48;
      this.controls.minPolarAngle = 0.1;
      this.controls.minDistance = 10;
      this.controls.maxDistance = 50;
      this.controls.target.set(0, 4, 0);

      this.rotSpeed = 0.5;
      window.addEventListener('resize', this.onResize);
      this.animate();
    },

    build: function() {
      var labGroup = new THREE.Group();

      this.mkLabRoom(labGroup);
      this.mkLabBench(labGroup);
      this.mkChamber(labGroup);
      this.mkSrc(labGroup,'Hg_Source','Hg 源温度',-5, 3.2, 0, 0xcc8855);
      this.mkSrc(labGroup,'CdTe_Source','CdTe 源温度', 4.2, 3.2, -2.8, 0x6699cc);
      this.mkSrc(labGroup,'Te_Source','Te₂ 源温度', 4.2, 3.2, 2.8, 0x77bb88);
      this.mkSub(labGroup);
      this.mkRack(labGroup, -8, 0, -2);
      this.mkBox(labGroup,'Hg_Flux','Hg 通量', -8, 4.2, -2, 0x00ff88);
      this.mkGauge(labGroup,'Beam_Pressure','束流压力', 3.8, 5.8, 3.2);
      this.mkMotor(labGroup);
      this.mkPump(labGroup);
      this.mkCool(labGroup);
      this.mkCtrl(labGroup);
      this.mkMonitors(labGroup);
      this.mkBeams(labGroup);

      this.scene.add(labGroup);
    },

    mkLabRoom: function(p) {
      // 更大的空间 - 开阔的实验室
      var floorGeo = new THREE.PlaneGeometry(60, 50);
      // 浅色地板
      var floorMat = this.M(0x4a5565, 0.8, 0.1);
      var floor = new THREE.Mesh(floorGeo, floorMat);
      floor.rotation.x = -Math.PI / 2;
      floor.position.y = 0;
      floor.receiveShadow = true;
      p.add(floor);

      // 柔和的地板网格
      var gridHelper = new THREE.GridHelper(60, 60, 0x5a6575, 0x4a5565);
      gridHelper.position.y = 0.01;
      gridHelper.material.opacity = 0.3;
      gridHelper.material.transparent = true;
      p.add(gridHelper);

      // 墙壁 - 浅色，增加空间感
      var wallMat = this.M(0x6a7585, 0.92, 0.03);

      // 后墙 - 更远
      var backWall = new THREE.Mesh(new THREE.PlaneGeometry(60, 14), wallMat);
      backWall.position.set(0, 7, -18);
      backWall.receiveShadow = true;
      p.add(backWall);

      // 侧墙 - 更远
      var sideWall1 = new THREE.Mesh(new THREE.PlaneGeometry(50, 14), wallMat);
      sideWall1.rotation.y = Math.PI / 2;
      sideWall1.position.set(-22, 7, 7);
      p.add(sideWall1);

      var sideWall2 = new THREE.Mesh(new THREE.PlaneGeometry(50, 14), wallMat);
      sideWall2.rotation.y = -Math.PI / 2;
      sideWall2.position.set(22, 7, 7);
      p.add(sideWall2);

      // 天花板 - 浅色
      var ceiling = new THREE.Mesh(
        new THREE.PlaneGeometry(60, 50),
        this.M(0x7a8595, 0.95, 0.02)
      );
      ceiling.rotation.x = Math.PI / 2;
      ceiling.position.y = 13;
      p.add(ceiling);

      // 天花板灯具 - 柔和的面板灯
      var panelLightMat = this.M(0xffffff, 0.1, 0.05, {
        emissive: 0xffffff,
        emissiveIntensity: 0.6
      });

      // 多个灯板分布
      var lightPositions = [
        [0, 0], [-10, -6], [10, -6], [-10, 6], [10, 6]
      ];

      lightPositions.forEach(function(pos) {
        var panel = new THREE.Mesh(
          new THREE.BoxGeometry(4, 0.1, 2),
          panelLightMat
        );
        panel.position.set(pos[0], 12.9, pos[1]);
        p.add(panel);
      });

      // 墙面装饰条 - 科技感但不压抑
      var stripMat = this.M(0x8a9aaa, 0.5, 0.4, {emissive: 0x4466aa, emissiveIntensity: 0.15});
      for (var i = 0; i < 2; i++) {
        var strip = new THREE.Mesh(new THREE.BoxGeometry(60, 0.03, 0.03), stripMat);
        strip.position.set(0, 3 + i * 5, -17.9);
        p.add(strip);
      }
    },

    mkLabBench: function(p) {
      var g = new THREE.Group();

      // 实验台面 - 深色但不压抑
      var topMat = this.M(0x2a2a32, 0.4, 0.65);
      var tabletop = new THREE.Mesh(new THREE.BoxGeometry(11, 0.1, 7.5), topMat);
      tabletop.position.y = 2.4;
      tabletop.receiveShadow = true;
      tabletop.castShadow = true;
      g.add(tabletop);

      // 台面边缘 - 金属色
      var edgeMat = this.M(0x8899aa, 0.25, 0.85);
      var edgeF = new THREE.Mesh(new THREE.BoxGeometry(11, 0.1, 0.06), edgeMat);
      edgeF.position.set(0, 2.4, 3.75);
      g.add(edgeF);
      var edgeB = edgeF.clone();
      edgeB.position.z = -3.75;
      g.add(edgeB);

      // 支撑腿 - 亮银色
      var frameMat = this.M(0x9aaabc, 0.28, 0.9);
      var legGeo = new THREE.CylinderGeometry(0.07, 0.07, 2.35, 12);

      var legPos = [
        [-5.2, 1.2, -3.5], [5.2, 1.2, -3.5],
        [-5.2, 1.2, 3.5], [5.2, 1.2, 3.5]
      ];

      legPos.forEach(function(pos) {
        var leg = new THREE.Mesh(legGeo, frameMat);
        leg.position.set(pos[0], pos[1], pos[2]);
        leg.castShadow = true;
        g.add(leg);
      });

      // 横梁
      var beam1 = new THREE.Mesh(new THREE.BoxGeometry(10.5, 0.05, 0.05), frameMat);
      beam1.position.set(0, 0.3, 3.5);
      g.add(beam1);
      var beam2 = beam1.clone();
      beam2.position.z = -3.5;
      g.add(beam2);

      // 脚垫
      var padMat = this.M(0x3a3a3a, 0.85, 0.08);
      legPos.forEach(function(pos) {
        var pad = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.15, 0.05, 12), padMat);
        pad.position.set(pos[0], 0.025, pos[2]);
        g.add(pad);
      });

      p.add(g);
    },

    mkChamber: function(p) {
      var g = new THREE.Group();

      // 主腔体 - 明亮的不锈钢
      var chamberMat = this.M(0xa8b8c8, 0.12, 0.94);
      var shell = new THREE.Mesh(
        new THREE.CylinderGeometry(2.8, 3.0, 6.5, 36, 1, false),
        chamberMat
      );
      shell.position.y = 5.7;
      shell.castShadow = true;
      shell.receiveShadow = true;
      g.add(shell);

      // 顶部法兰
      var topFlange = new THREE.Mesh(
        new THREE.CylinderGeometry(3.2, 3.2, 0.22, 36),
        chamberMat
      );
      topFlange.position.y = 9.1;
      topFlange.castShadow = true;
      g.add(topFlange);

      // 底部法兰
      var baseFlange = new THREE.Mesh(
        new THREE.CylinderGeometry(3.4, 3.5, 0.3, 36),
        chamberMat
      );
      baseFlange.position.y = 2.6;
      baseFlange.castShadow = true;
      g.add(baseFlange);

      // 观察窗 - 6个
      for(var i = 0; i < 6; i++) {
        var angle = (i * Math.PI * 2) / 6;
        var wx = Math.sin(angle) * 2.95;
        var wz = Math.cos(angle) * 2.95;

        var flange = new THREE.Mesh(
          new THREE.CylinderGeometry(0.4, 0.4, 0.15, 16),
          chamberMat
        );
        flange.rotation.z = Math.PI / 2;
        flange.position.set(wx, 5.7, wz);
        flange.lookAt(0, 5.7, 0);
        g.add(flange);

        // 玻璃窗 - 略带蓝色
        var glass = new THREE.Mesh(
          new THREE.CircleGeometry(0.3, 16),
          this.M(0xaaddff, 0.02, 0.08, {transparent: true, opacity: 0.35})
        );
        glass.position.set(wx * 1.02, 5.7, wz * 1.02);
        glass.lookAt(0, 5.7, 0);
        g.add(glass);
      }

      // 加强筋
      for(var j = 0; j < 4; j++) {
        var ring = new THREE.Mesh(
          new THREE.TorusGeometry(2.92, 0.05, 8, 36),
          chamberMat
        );
        ring.position.y = 3.5 + j * 1.6;
        g.add(ring);
      }

      // 腔体内部蓝光 - 柔和
      var cl = new THREE.PointLight(0x4488cc, 1.5, 5);
      cl.position.set(0, 5.7, 0);
      g.add(cl);
      this.chamberLight = cl;

      // 状态指示灯
      this.led(g, 0, 9.3, 0, 0x00ff88);
      this.led(g, 0.35, 9.25, 0.35, 0xffcc00);

      this.reg(shell, 'Main_Chamber', '背景真空');
      p.add(g);
    },

    mkSrc: function(p, name, label, x, y, z, color) {
      var g = new THREE.Group();

      // 更亮的源炉颜色
      var brightColor = new THREE.Color(color).multiplyScalar(1.2).getHex();
      var srcMat = this.M(brightColor, 0.22, 0.85);
      var body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.4, 0.6, 2.5, 16),
        srcMat
      );
      body.castShadow = true;
      g.add(body);

      // 加热区
      var heaterMat = this.M(0x7a6050, 0.6, 0.35);
      var heater = new THREE.Mesh(
        new THREE.CylinderGeometry(0.28, 0.32, 1.2, 12),
        heaterMat
      );
      heater.position.y = 0.35;
      g.add(heater);

      // 加热线圈
      for(var i = 0; i < 5; i++) {
        var coil = new THREE.Mesh(
          new THREE.TorusGeometry(0.45, 0.015, 6, 16),
          this.M(0xdd9966, 0.2, 0.88)
        );
        coil.position.y = -0.75 + i * 0.38;
        g.add(coil);
        this.srcCoils.push(coil);
      }

      // 连接管
      var pipe = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.12, 2.3, 8),
        this.M(0x9aaabc, 0.25, 0.88)
      );
      pipe.position.set(x/2.2, y+1.1, z/2.2);
      pipe.lookAt(0, y+1.1, 0);
      pipe.rotateX(Math.PI/2);
      p.add(pipe);

      // 控制阀
      var valve = new THREE.Mesh(
        new THREE.CylinderGeometry(0.18, 0.18, 0.22, 8),
        this.M(0x7799cc, 0.28, 0.82)
      );
      valve.position.set(x*0.65, y+1.1, z*0.65);
      p.add(valve);

      this.led(g, 0, 1.4, 0, 0xff6600);

      g.position.set(x, y, z);
      this.reg(body, name, label);
      p.add(g);
    },

    mkSub: function(p) {
      var g = new THREE.Group();

      // 衬底加热器 - 铜色
      var heaterMat = this.M(0xccaa77, 0.18, 0.9);
      var h = new THREE.Mesh(
        new THREE.CylinderGeometry(0.95, 0.95, 0.18, 32),
        heaterMat
      );
      h.position.y = 0.16;
      g.add(h);

      // 基座
      var base = new THREE.Mesh(
        new THREE.CylinderGeometry(1.15, 1.25, 0.22, 32),
        this.M(0x8899aa, 0.28, 0.85)
      );
      g.add(base);

      // 晶圆
      var wafer = new THREE.Mesh(
        new THREE.CylinderGeometry(0.7, 0.7, 0.012, 32),
        this.M(0x1e1e28, 0.05, 0.96)
      );
      wafer.position.y = 0.28;
      g.add(wafer);

      // 薄膜层
      var filmMat = new THREE.MeshStandardMaterial({
        color: 0x5577aa,
        emissive: 0x334466,
        emissiveIntensity: 0.2,
        transparent: true,
        opacity: 0,
        roughness: 0.08,
        metalness: 0.94
      });
      var film = new THREE.Mesh(
        new THREE.CylinderGeometry(0.68, 0.68, 0.006, 32),
        filmMat
      );
      film.position.y = 0.3;
      film.visible = false;
      g.add(film);
      this.substrateFilm = film;

      // 加热光
      var heatLight = new THREE.PointLight(0xff6600, 1.2, 2.5);
      heatLight.position.y = 0.1;
      g.add(heatLight);

      // 沉积光
      var dl = new THREE.PointLight(0x5599ff, 0, 1.8);
      dl.position.y = 0.32;
      g.add(dl);
      this.depositLight = dl;

      // 旋转轴
      var shaft = new THREE.Mesh(
        new THREE.CylinderGeometry(0.07, 0.07, 2.0, 8),
        this.M(0x8899aa, 0.25, 0.85)
      );
      shaft.position.y = -1.1;
      g.add(shaft);

      g.position.set(0, 8.2, 0);
      g.rotation.x = Math.PI;
      this.reg(h, 'Substrate_Heater', '衬底温度 Ts');
      this.subG = g;
      p.add(g);
    },

    mkRack: function(p, x, y, z) {
      var g = new THREE.Group();

      // 机柜 - 稍亮
      var frameMat = this.M(0x4a5565, 0.7, 0.28);
      var cabinet = new THREE.Mesh(
        new THREE.BoxGeometry(1.7, 4.3, 1.2),
        frameMat
      );
      cabinet.position.y = 2.15;
      cabinet.castShadow = true;
      g.add(cabinet);

      // 前面板
      var panelMat = this.M(0x3a4555, 0.8, 0.18);
      var panel = new THREE.Mesh(
        new THREE.BoxGeometry(1.5, 4.0, 0.06),
        panelMat
      );
      panel.position.set(0, 2.15, 0.65);
      g.add(panel);

      // 通风孔
      for(var i = 0; i < 12; i++) {
        for(var j = 0; j < 3; j++) {
          var vent = new THREE.Mesh(
            new THREE.BoxGeometry(0.035, 0.1, 0.12),
            this.M(0x1a1a1f, 1, 0)
          );
          vent.position.set(-0.45 + j * 0.45, 3.8 - i * 0.2, 0.65);
          g.add(vent);
        }
      }

      // 指示灯
      for(var k = 0; k < 4; k++) {
        this.led(g, -0.55, 3.0 - k * 0.35, 0.7, k % 2 ? 0x00ff88 : 0x00aaff);
      }

      g.position.set(x, y, z);
      p.add(g);
    },

    mkBox: function(p, name, label, x, y, z, c) {
      var g = new THREE.Group();

      var boxMat = this.M(0x3a4555, 0.6, 0.38);
      var b = new THREE.Mesh(
        new THREE.BoxGeometry(0.95, 0.65, 0.45),
        boxMat
      );
      b.castShadow = true;
      g.add(b);

      // 显示屏
      var screen = new THREE.Mesh(
        new THREE.PlaneGeometry(0.45, 0.22),
        this.M(0x002838, 0.1, 0.2, {emissive: 0x0066aa, emissiveIntensity: 0.4})
      );
      screen.position.set(0, 0.07, 0.235);
      g.add(screen);

      // 旋钮
      for(var i = 0; i < 3; i++) {
        var knob = new THREE.Mesh(
          new THREE.CylinderGeometry(0.055, 0.055, 0.07, 10),
          this.M(0x8899aa, 0.32, 0.8)
        );
        knob.rotation.x = Math.PI / 2;
        knob.position.set(-0.22 + i * 0.22, -0.16, 0.27);
        g.add(knob);
      }

      this.led(g, 0.35, 0.22, 0.235, c);

      g.position.set(x, y, z);
      g.lookAt(0, y, 0);
      this.reg(b, name, label);
      p.add(g);
    },

    mkPump: function(p) {
      var g = new THREE.Group();

      var pumpMat = this.M(0x8899aa, 0.25, 0.85);
      var body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.95, 0.95, 2.0, 18),
        pumpMat
      );
      body.castShadow = true;
      g.add(body);

      // 散热片
      for(var i = 0; i < 8; i++) {
        var fin = new THREE.Mesh(
          new THREE.BoxGeometry(0.035, 1.5, 1.2),
          this.M(0x7a8a9a, 0.4, 0.75)
        );
        fin.position.set(Math.sin(i * Math.PI / 4) * 1.0, 0, Math.cos(i * Math.PI / 4) * 1.0);
        fin.lookAt(0, 0, 0);
        g.add(fin);
      }

      // 进气口
      var inlet = new THREE.Mesh(
        new THREE.CylinderGeometry(0.22, 0.22, 0.45, 12),
        pumpMat
      );
      inlet.position.y = 1.25;
      g.add(inlet);

      // 管路
      var pipeC = new THREE.CatmullRomCurve3([
        new THREE.Vector3(0, 1.5, 0),
        new THREE.Vector3(0, 2.6, -1.5),
        new THREE.Vector3(0, 3.5, -3.2),
        new THREE.Vector3(0, 4.2, -5)
      ]);
      var pipeGeo = new THREE.TubeGeometry(pipeC, 20, 0.18, 8, false);
      var pipe = new THREE.Mesh(pipeGeo, this.M(0x9aaabc, 0.25, 0.8));
      g.add(pipe);

      this.led(g, 0.45, 0.8, 0.8, 0x00ff88);

      g.position.set(0, 1, -6.5);
      this.reg(body, 'Vacuum_Pump', '背景真空（泵组）');
      p.add(g);
    },

    mkGauge: function(p, name, label, x, y, z) {
      var g = new THREE.Group();

      var gaugeBody = new THREE.Mesh(
        new THREE.CylinderGeometry(0.14, 0.14, 1.2, 12),
        this.M(0xa8b8c8, 0.18, 0.9)
      );
      g.add(gaugeBody);

      // 传感器头
      var sensor = new THREE.Mesh(
        new THREE.SphereGeometry(0.1, 12, 8),
        this.M(0xb8c8d8, 0.1, 0.92)
      );
      sensor.position.y = 0.65;
      g.add(sensor);

      // 显示器
      var display = new THREE.Mesh(
        new THREE.BoxGeometry(0.28, 0.2, 0.07),
        this.M(0x002530, 0.1, 0.2, {emissive: 0x00ff44, emissiveIntensity: 0.3})
      );
      display.position.set(0, -0.22, 0.1);
      g.add(display);

      // 连接座
      var mount = new THREE.Mesh(
        new THREE.CylinderGeometry(0.22, 0.22, 0.14, 12),
        this.M(0x8899aa, 0.28, 0.85)
      );
      mount.position.y = -0.68;
      g.add(mount);

      // 发光环
      var ring = new THREE.Mesh(
        new THREE.TorusGeometry(0.07, 0.012, 8, 16),
        this.GM(0xff6600, 0.6)
      );
      ring.position.y = 0.22;
      g.add(ring);
      this.indicators.push(ring);

      g.position.set(x, y, z);
      this.reg(gaugeBody, name, label);
      p.add(g);
    },

    mkMotor: function(p) {
      var g = new THREE.Group();

      var motorMat = this.M(0x8899aa, 0.25, 0.84);
      var body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.5, 0.5, 1.2, 18),
        motorMat
      );
      body.castShadow = true;
      g.add(body);

      // 散热筋
      for(var i = 0; i < 5; i++) {
        var rib = new THREE.Mesh(
          new THREE.BoxGeometry(1.1, 0.035, 0.6),
          this.M(0x7a8a9a, 0.42, 0.72)
        );
        rib.position.y = -0.45 + i * 0.2;
        g.add(rib);
      }

      // 输出轴
      var shaft = new THREE.Mesh(
        new THREE.CylinderGeometry(0.055, 0.055, 0.9, 8),
        this.M(0xb8c8d8, 0.15, 0.92)
      );
      shaft.position.y = 1.05;
      g.add(shaft);

      // 编码器
      var encoder = new THREE.Mesh(
        new THREE.CylinderGeometry(0.28, 0.28, 0.22, 12),
        this.M(0x3a4555, 0.55, 0.42)
      );
      encoder.position.y = -0.72;
      g.add(encoder);

      this.led(g, 0.35, 0.45, 0.35, 0x00ff88);

      g.position.set(0, 10.2, 0);
      this.reg(body, 'Rotation_Motor', '转台转速');
      p.add(g);
    },

    mkCool: function(p) {
      var g = new THREE.Group();

      var coolerMat = this.M(0x5599cc, 0.22, 0.72);
      var tank = new THREE.Mesh(
        new THREE.BoxGeometry(1.6, 0.9, 0.8),
        coolerMat
      );
      tank.castShadow = true;
      g.add(tank);

      // 散热风扇
      var fanFrame = new THREE.Mesh(
        new THREE.BoxGeometry(0.6, 0.6, 0.12),
        this.M(0x3a4555, 0.52, 0.45)
      );
      fanFrame.position.set(0.42, 0, 0.46);
      g.add(fanFrame);

      // 管路接口
      for(var i = 0; i < 2; i++) {
        var connector = new THREE.Mesh(
          new THREE.CylinderGeometry(0.08, 0.08, 0.22, 8),
          this.M(0xb8c8d8, 0.18, 0.9)
        );
        connector.rotation.z = Math.PI / 2;
        connector.position.set(-0.45 + i * 0.9, 0.32, 0);
        g.add(connector);
      }

      // 水管
      var curves = [
        new THREE.CatmullRomCurve3([
          new THREE.Vector3(-0.45, 0.32, 0),
          new THREE.Vector3(-1.6, 1.2, 0.7),
          new THREE.Vector3(-2.2, 2.5, 1.3),
          new THREE.Vector3(-2.2, 4.2, 1.3)
        ]),
        new THREE.CatmullRomCurve3([
          new THREE.Vector3(0.45, 0.32, 0),
          new THREE.Vector3(1.6, 1.2, 0.7),
          new THREE.Vector3(2.2, 2.5, 1.3),
          new THREE.Vector3(2.2, 4.2, 1.3)
        ])
      ];

      curves.forEach(function(curve) {
        var tube = new THREE.TubeGeometry(curve, 20, 0.055, 8, false);
        var pipeMesh = new THREE.Mesh(
          tube,
          this.M(0x66aadd, 0.25, 0.6, {emissive: 0x224466, emissiveIntensity: 0.15})
        );
        g.add(pipeMesh);
      }.bind(this));

      this.led(g, 0.65, 0.35, 0.42, 0x00aaff);

      g.position.set(-7, 0.85, 3.5);
      this.reg(tank, 'Cooling_System', '冷却水温');
      p.add(g);
    },

    mkCtrl: function(p) {
      var g = new THREE.Group();

      var cabinetMat = this.M(0x4a5565, 0.6, 0.35);
      var cb = new THREE.Mesh(
        new THREE.BoxGeometry(1.2, 2.5, 0.65),
        cabinetMat
      );
      cb.castShadow = true;
      g.add(cb);

      // 触摸屏
      var screenMat = this.M(0x002838, 0.05, 0.28, {emissive: 0x0066aa, emissiveIntensity: 0.45});
      var screen = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.55), screenMat);
      screen.position.set(0, 0.65, 0.335);
      g.add(screen);

      // 按钮阵列
      var btnColors = [0x22cc66, 0x22cc66, 0xffbb22, 0xffbb22, 0xff5544, 0xff5544];
      for(var i = 0; i < 2; i++) {
        for(var j = 0; j < 3; j++) {
          var btn = new THREE.Mesh(
            new THREE.BoxGeometry(0.1, 0.1, 0.035),
            this.M(btnColors[i*3+j], 0.28, 0.5, {emissive: btnColors[i*3+j], emissiveIntensity: 0.12})
          );
          btn.position.set(-0.32 + j * 0.2, -0.12 - i * 0.2, 0.345);
          g.add(btn);
        }
      }

      // 紧急停止
      var eStop = new THREE.Mesh(
        new THREE.CylinderGeometry(0.1, 0.1, 0.055, 16),
        this.M(0xff3322, 0.22, 0.6, {emissive: 0xff3322, emissiveIntensity: 0.3})
      );
      eStop.rotation.x = Math.PI / 2;
      eStop.position.set(0, -0.85, 0.355);
      g.add(eStop);

      this.led(g, 0.45, 1.0, 0.335, 0x00ff88);

      g.position.set(7, 1.25, -2);
      this.reg(cb, 'Growth_Controller', '生长修正');
      p.add(g);
    },

    mkMonitors: function(p) {
      var g = new THREE.Group();

      // 显示器支架
      var standMat = this.M(0x5a6575, 0.48, 0.52);

      // 显示器1
      var mon1Frame = new THREE.Mesh(new THREE.BoxGeometry(1.7, 1.1, 0.07), this.M(0x3a4555, 0.82, 0.22));
      mon1Frame.position.set(-6, 4.6, -16);
      g.add(mon1Frame);

      var mon1Screen = new THREE.Mesh(
        new THREE.PlaneGeometry(1.5, 0.9),
        this.M(0x002838, 0.05, 0.1, {emissive: 0x004477, emissiveIntensity: 0.3})
      );
      mon1Screen.position.set(-6, 4.6, -15.95);
      g.add(mon1Screen);

      var stand1 = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.55, 0.07), standMat);
      stand1.position.set(-6, 3.85, -16);
      g.add(stand1);

      // 显示器2
      var mon2Frame = mon1Frame.clone();
      mon2Frame.position.set(6, 4.6, -16);
      g.add(mon2Frame);

      var mon2Screen = mon1Screen.clone();
      mon2Screen.position.set(6, 4.6, -15.95);
      g.add(mon2Screen);

      var stand2 = stand1.clone();
      stand2.position.set(6, 3.85, -16);
      g.add(stand2);

      p.add(g);
    },

    mkBeams: function(p) {
      var sources = [
        {from: new THREE.Vector3(-5, 4.5, 0), color: 0xff8866},
        {from: new THREE.Vector3(4.2, 4.5, -2.8), color: 0x66bbff},
        {from: new THREE.Vector3(4.2, 4.5, 2.8), color: 0x88ffbb}
      ];
      var target = new THREE.Vector3(0, 7.2, 0);

      sources.forEach(function(src) {
        var count = 70;
        var geo = new THREE.BufferGeometry();
        var positions = new Float32Array(count * 3);
        var randoms = new Float32Array(count);

        for(var i = 0; i < count; i++) {
          randoms[i] = Math.random();
          var t = randoms[i];
          positions[i * 3] = src.from.x + (target.x - src.from.x) * t + (Math.random() - 0.5) * 0.1;
          positions[i * 3 + 1] = src.from.y + (target.y - src.from.y) * t + (Math.random() - 0.5) * 0.1;
          positions[i * 3 + 2] = src.from.z + (target.z - src.from.z) * t + (Math.random() - 0.5) * 0.1;
        }

        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        var mat = new THREE.PointsMaterial({
          color: src.color,
          size: 0.05,
          transparent: true,
          opacity: 0.6,
          blending: THREE.AdditiveBlending,
          depthWrite: false
        });

        var points = new THREE.Points(geo, mat);
        p.add(points);

        this.particleSystems.push({
          points: points,
          from: src.from,
          target: target,
          randoms: randoms
        });
      }.bind(this));
    },

    animate: function() {
      var self = this;
      this.frameId = requestAnimationFrame(function(){ self.animate(); });
      var dt = this.clock.getDelta();
      var t = this.clock.getElapsedTime();

      if(this.subG) { this.subG.rotation.y += dt * (this.rotSpeed || 0.5); }

      var i;
      for(i = 0; i < this.indicators.length; i++) {
        var o = this.indicators[i];
        if(o.isMesh && o.material) {
          o.material.emissiveIntensity = 0.45 + Math.sin(t * 2.5 + i * 1.1) * 0.35;
        }
      }

      if (this.growActive) {
        this.growTime += dt;

        var beamSpeed = this.beamSpeedBase * 1.5;
        for(i = 0; i < this.particleSystems.length; i++) {
          var s = this.particleSystems[i];
          var pa = s.points.geometry.attributes.position.array;

          for(var ri = 0; ri < s.randoms.length; ri++) {
            s.randoms[ri] += dt * beamSpeed;
            if(s.randoms[ri] > 1) { s.randoms[ri] = 0; }

            var pr = s.randoms[ri];
            var scatter = 0.02;
            pa[ri * 3] = s.from.x + (s.target.x - s.from.x) * pr + (Math.random() - 0.5) * scatter;
            pa[ri * 3 + 1] = s.from.y + (s.target.y - s.from.y) * pr + (Math.random() - 0.5) * scatter;
            pa[ri * 3 + 2] = s.from.z + (s.target.z - s.from.z) * pr + (Math.random() - 0.5) * scatter;
          }

          s.points.geometry.attributes.position.needsUpdate = true;
          s.points.material.opacity = 0.5 + Math.sin(t * 3 + i) * 0.28;
        }

        for(i = 0; i < this.srcCoils.length; i++) {
          var coil = this.srcCoils[i];
          coil.material.emissive.setHex(0xff5500);
          coil.material.emissiveIntensity = 0.2 + Math.sin(t * 4 + i * 0.7) * 0.3;
        }

        if (this.substrateFilm) {
          var filmProgress = Math.min(this.growTime / 60, 1.0);
          this.substrateFilm.visible = true;
          this.substrateFilm.material.opacity = 0.12 + filmProgress * 0.6;
          this.substrateFilm.scale.y = 1 + filmProgress * 3;

          var r = 0.28 + filmProgress * 0.42;
          var gb = 0.32 + filmProgress * 0.32;
          var b = 0.48 - filmProgress * 0.12;
          this.substrateFilm.material.color.setRGB(r, gb, b);
          this.substrateFilm.material.emissive.setRGB(r * 0.2, gb * 0.2, b * 0.2);
        }

        if (this.depositLight) {
          this.depositLight.intensity = 0.9 + Math.sin(t * 5) * 0.45;
          this.depositLight.color.setHex(this.growTime < 30 ? 0x5599ff : 0x9988ff);
        }

        if (this.chamberLight) {
          this.chamberLight.intensity = 1.8 + Math.sin(t * 2) * 0.5;
        }

      } else {
        for(i = 0; i < this.particleSystems.length; i++) {
          var s2 = this.particleSystems[i];
          var pa2 = s2.points.geometry.attributes.position.array;

          for(var ri2 = 0; ri2 < s2.randoms.length; ri2++) {
            s2.randoms[ri2] += dt * 0.28;
            if(s2.randoms[ri2] > 1) { s2.randoms[ri2] = 0; }

            var pr2 = s2.randoms[ri2];
            pa2[ri2 * 3] = s2.from.x + (s2.target.x - s2.from.x) * pr2 + (Math.random() - 0.5) * 0.06;
            pa2[ri2 * 3 + 1] = s2.from.y + (s2.target.y - s2.from.y) * pr2 + (Math.random() - 0.5) * 0.06;
            pa2[ri2 * 3 + 2] = s2.from.z + (s2.target.z - s2.from.z) * pr2 + (Math.random() - 0.5) * 0.06;
          }
          s2.points.geometry.attributes.position.needsUpdate = true;
        }

        for(i = 0; i < this.srcCoils.length; i++) {
          this.srcCoils[i].material.emissiveIntensity = 0.03;
        }
      }

      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    },

    onMove: function(e) {
      var rect = this.$refs.canvas.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      this.tooltipPos = {x: e.clientX + 15, y: e.clientY + 15};

      this.raycaster.setFromCamera(this.mouse, this.camera);
      var intersects = this.raycaster.intersectObjects(this.interactables, false);

      if(intersects.length > 0) {
        var hit = intersects[0].object;
        document.body.style.cursor = 'pointer';
        this.hoveredParams = hit.userData.label || hit.name;

        if(this.currentHover !== hit) {
          this.rh();
          this.currentHover = hit;
          this.originalEmissive = hit.material.emissive.getHex();
          hit.material.emissive.setHex(0x00aaff);
          hit.material.emissiveIntensity = 0.7;
        }
      } else {
        document.body.style.cursor = 'default';
        this.hoveredParams = null;
        this.rh();
      }
    },

    rh: function() {
      if(this.currentHover) {
        this.currentHover.material.emissive.setHex(this.originalEmissive || 0x000000);
        this.currentHover.material.emissiveIntensity = 0.2;
        this.currentHover = null;
      }
    },

    onClick: function() {
      if(this.currentHover) {
        this.$emit('device-click', this.currentHover.name);
        var m = this.currentHover.material;
        m.emissive.setHex(0x00ffff);
        m.emissiveIntensity = 1.8;
        var self = this;
        setTimeout(function() {
          if(self.currentHover) {
            m.emissive.setHex(0x00aaff);
            m.emissiveIntensity = 0.7;
          }
        }, 150);
      }
    },

    onResize: function() {
      var c = this.$refs.canvas;
      if(c) {
        this.camera.aspect = c.clientWidth / c.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(c.clientWidth, c.clientHeight);
      }
    }
  }
};
</script>

<style scoped>
.scene-container{width:100%;height:100%;position:relative;overflow:hidden;border-radius:8px}
.canvas-box{width:100%;height:100%}
.loader-overlay{position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(30,40,55,0.9);z-index:10;display:flex;flex-direction:column;justify-content:center;align-items:center;color:#00c7ff;pointer-events:none}
.spinner{width:40px;height:40px;border:3px solid rgba(0,199,255,0.3);border-top-color:#00c7ff;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:15px}
.hover-tooltip{position:fixed;z-index:9999;background:rgba(30,45,65,0.94);border:1px solid #00aaff;box-shadow:0 0 12px rgba(0,150,255,0.3);color:#fff;padding:6px 12px;border-radius:4px;font-size:13px;font-weight:bold;pointer-events:none;backdrop-filter:blur(4px)}
@keyframes spin{to{transform:rotate(360deg)}}
</style>