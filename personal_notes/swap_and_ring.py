import re

with open('personal_notes/deck_v3.html', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's inspect createTrackMarkings, createBoulders, init3D, buildRoverModel, updateSimKinematics
three_block = """    // ====================================================================
    // THREE.JS 3D MARS SIMULATION (AAA AEROSPACE CAD & DETERMINISTIC KINEMATICS)
    // ====================================================================
    let scene, camera, renderer;
    let simTime = 0;
    let simPlaying = true;
    const simDuration = 12.0;

    // Rover 3D Objects
    let vanillaRover, jamesianRover;
    let vanillaWheels = [], jamesianWheels = [];
    let jamesianFrontSteerGroup;
    let vanillaHeatGlowMesh, vanillaHeatLight;
    let jamesianLedMesh, jamesianOpticalLight;

    function init3D() {
      const container = document.querySelector('.sim-canvas-wrap');
      const canvas = document.getElementById('webgl-canvas');
      const width = container.clientWidth;
      const height = container.clientHeight;

      scene = new THREE.Scene();
      scene.background = new THREE.Color(0x1a0f0c);
      scene.fog = new THREE.FogExp2(0x1a0f0c, 0.035);

      // Fixed 3/4 aerial perspective camera - perfectly framing Lane A (left), Lane B (right), and Bypass
      camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
      camera.position.set(13.5, 11.2, 7.5);
      camera.lookAt(0.2, 0.6, -0.6);

      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;

      // Cinematic ACES Filmic Tone Mapping for authentic aerospace metals and shadows
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.12;
      renderer.outputEncoding = THREE.sRGBEncoding;

      // Lighting Suite
      const ambientLight = new THREE.AmbientLight(0xffbfa8, 0.95);
      scene.add(ambientLight);

      const sunLight = new THREE.DirectionalLight(0xfff0dd, 2.2);
      sunLight.position.set(16, 22, 14);
      sunLight.castShadow = true;
      sunLight.shadow.mapSize.width = 1024;
      sunLight.shadow.mapSize.height = 1024;
      sunLight.shadow.bias = -0.0004;
      sunLight.shadow.camera.near = 0.5;
      sunLight.shadow.camera.far = 45;
      sunLight.shadow.camera.left = -14;
      sunLight.shadow.camera.right = 14;
      sunLight.shadow.camera.top = 14;
      sunLight.shadow.camera.bottom = -14;
      scene.add(sunLight);

      // Mars Ground Plane with Rust Dust Tone
      const groundGeo = new THREE.PlaneGeometry(55, 45, 32, 32);
      const groundMat = new THREE.MeshStandardMaterial({
        color: 0x983e26,
        roughness: 0.94,
        metalness: 0.04
      });
      const ground = new THREE.Mesh(groundGeo, groundMat);
      ground.rotation.x = -Math.PI / 2;
      ground.receiveShadow = true;
      scene.add(ground);

      // Subtle track guides on Martian soil (Lane A on Screen-Left, Lane B on Screen-Right)
      createTrackMarkings();

      // Rocks / Boulders
      createBoulders();

      // Build Both Rovers:
      // LANE A: Vanilla Rover at Z = 2.6 (Screen-Left / Foreground)
      vanillaRover = buildRoverModel(false);
      vanillaRover.position.set(-5.2, 0, 2.6);
      scene.add(vanillaRover);

      // LANE B: Jamesian Rover at Z = -2.6 (Screen-Right / Background)
      jamesianRover = buildRoverModel(true);
      jamesianRover.position.set(-5.2, 0, -2.6);
      scene.add(jamesianRover);

      window.addEventListener('resize', onWindowResize);
      animate3D();
    }

    function createTrackMarkings() {
      const lineMat = new THREE.MeshBasicMaterial({ color: 0x7c301d, transparent: true, opacity: 0.35 });

      // Lane A (Vanilla) centerline at Z = 2.6 (Screen-Left)
      const lineGeoA = new THREE.PlaneGeometry(16, 0.08);
      const trackA = new THREE.Mesh(lineGeoA, lineMat);
      trackA.rotation.x = -Math.PI / 2;
      trackA.position.set(0, 0.01, 2.6);
      scene.add(trackA);

      // Lane B (Jamesian) approach centerline at Z = -2.6 (Screen-Right)
      const trackB = new THREE.Mesh(lineGeoA, lineMat);
      trackB.rotation.x = -Math.PI / 2;
      trackB.position.set(-2.5, 0.01, -2.6);
      scene.add(trackB);

      // Lane B Lateral bypass track guide (from Z = -2.6 to Z = -4.5)
      const lineGeoLat = new THREE.PlaneGeometry(0.08, 1.9);
      const trackLat = new THREE.Mesh(lineGeoLat, lineMat);
      trackLat.rotation.x = -Math.PI / 2;
      trackLat.position.set(-0.6, 0.01, -3.55);
      scene.add(trackLat);

      // Lane B Clear bypass forward track at Z = -4.5
      const lineGeoBypass = new THREE.PlaneGeometry(10, 0.08);
      const trackBypass = new THREE.Mesh(lineGeoBypass, lineMat);
      trackBypass.rotation.x = -Math.PI / 2;
      trackBypass.position.set(2.0, 0.01, -4.5);
      scene.add(trackBypass);
    }

    function createBoulders() {
      const rockGeo = new THREE.DodecahedronGeometry(0.72, 1);
      const rockMat = new THREE.MeshStandardMaterial({
        color: 0x38241e,
        roughness: 0.96,
        metalness: 0.05
      });

      // Rock in Lane A (Vanilla hits it at x=-0.6, z=2.6)
      const rockA = new THREE.Mesh(rockGeo, rockMat);
      rockA.position.set(0.65, 0.52, 2.6);
      rockA.scale.set(1.25, 0.95, 1.35);
      rockA.castShadow = true;
      rockA.receiveShadow = true;
      scene.add(rockA);

      // Rock in Lane B (Jamesian encounters at x=-0.6, z=-2.6)
      const rockB = new THREE.Mesh(rockGeo, rockMat);
      rockB.position.set(0.65, 0.52, -2.6);
      rockB.scale.set(1.25, 0.95, 1.35);
      rockB.castShadow = true;
      rockB.receiveShadow = true;
      scene.add(rockB);

      // Scattered Natural Rocks
      const bgRockGeo = new THREE.DodecahedronGeometry(0.35, 0);
      for (let i = 0; i < 22; i++) {
        const bgRock = new THREE.Mesh(bgRockGeo, rockMat);
        const rx = (Math.random() - 0.5) * 36;
        const rz = (Math.random() - 0.5) * 26;
        if (Math.abs(rz - 2.6) > 1.3 && Math.abs(rz + 2.6) > 1.3 && Math.abs(rz + 4.5) > 1.2) {
          bgRock.position.set(rx, 0.2, rz);
          bgRock.scale.setScalar(0.4 + Math.random() * 0.9);
          bgRock.castShadow = true;
          scene.add(bgRock);
        }
      }
    }

    // Procedural High-Fidelity Rover Generator (Matches user's generated photo morphology)
    function buildRoverModel(isJamesian) {
      const roverGroup = new THREE.Group();

      // Materials
      const titaniumMat = new THREE.MeshStandardMaterial({
        color: 0x484e55,
        metalness: 0.85,
        roughness: 0.32
      });
      const carbonMat = new THREE.MeshStandardMaterial({
        color: 0x1c1e22,
        metalness: 0.45,
        roughness: 0.65
      });
      const wheelRimMat = new THREE.MeshStandardMaterial({
        color: 0x2b2f35,
        metalness: 0.88,
        roughness: 0.28
      });
      const cleatMat = new THREE.MeshStandardMaterial({
        color: 0x3d434a,
        metalness: 0.82,
        roughness: 0.38
      });
      const solarMat = new THREE.MeshStandardMaterial({
        color: 0x142338,
        metalness: 0.65,
        roughness: 0.12
      });

      // 1. Chassis Main Body
      const chassisGeo = new THREE.BoxGeometry(1.9, 0.75, 1.2);
      const chassis = new THREE.Mesh(chassisGeo, titaniumMat);
      chassis.position.y = 0.68;
      chassis.castShadow = true;
      chassis.receiveShadow = true;
      roverGroup.add(chassis);

      // Carbon Fiber side inset plates
      const sidePlateGeo = new THREE.BoxGeometry(1.2, 0.5, 0.05);
      const sideL = new THREE.Mesh(sidePlateGeo, carbonMat);
      sideL.position.set(0, 0.68, 0.61);
      roverGroup.add(sideL);
      const sideR = new THREE.Mesh(sidePlateGeo, carbonMat);
      sideR.position.set(0, 0.68, -0.61);
      roverGroup.add(sideR);

      // Solar Panel on Top Deck
      const solarGeo = new THREE.BoxGeometry(1.4, 0.03, 0.95);
      const solar = new THREE.Mesh(solarGeo, solarMat);
      solar.position.set(-0.1, 1.07, 0);
      roverGroup.add(solar);

      // 2. Camera Mast & Stereo Sensor
      const mastPoleGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.7, 12);
      const mastPole = new THREE.Mesh(mastPoleGeo, titaniumMat);
      mastPole.position.set(0.65, 1.35, 0.2);
      mastPole.castShadow = true;
      roverGroup.add(mastPole);

      const mastHeadGeo = new THREE.BoxGeometry(0.2, 0.15, 0.32);
      const mastHead = new THREE.Mesh(mastHeadGeo, titaniumMat);
      mastHead.position.set(0.65, 1.72, 0.2);
      roverGroup.add(mastHead);

      // Dual camera lenses
      const lensGeo = new THREE.CylinderGeometry(0.035, 0.035, 0.05, 12);
      lensGeo.rotateZ(Math.PI / 2);
      const lensMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.1, metalness: 0.9 });
      const lens1 = new THREE.Mesh(lensGeo, lensMat);
      lens1.position.set(0.76, 1.72, 0.12);
      roverGroup.add(lens1);
      const lens2 = new THREE.Mesh(lensGeo, lensMat);
      lens2.position.set(0.76, 1.72, 0.28);
      roverGroup.add(lens2);

      // 3. Realistic Treaded All-Terrain Wheels (Curiosity/Perseverance Cleats)
      function makeDetailedWheel() {
        const wGroup = new THREE.Group();
        const mainCyl = new THREE.CylinderGeometry(0.38, 0.38, 0.28, 24);
        mainCyl.rotateX(Math.PI / 2);
        const rimMesh = new THREE.Mesh(mainCyl, wheelRimMat);
        rimMesh.castShadow = true;
        wGroup.add(rimMesh);

        // Radial Chevron Cleats / Treads around perimeter
        const cleatGeo = new THREE.BoxGeometry(0.03, 0.06, 0.29);
        for (let a = 0; a < Math.PI * 2; a += Math.PI / 6) {
          const cleat = new THREE.Mesh(cleatGeo, cleatMat);
          cleat.position.set(Math.cos(a) * 0.385, Math.sin(a) * 0.385, 0);
          cleat.rotation.z = a;
          wGroup.add(cleat);
        }
        return wGroup;
      }

      const wheelsArray = [];
      const wheelPositions = [
        { x: 0.75, y: 0.38, z: 0.78, isFront: true },
        { x: 0.75, y: 0.38, z: -0.78, isFront: true },
        { x: -0.75, y: 0.38, z: 0.78, isFront: false },
        { x: -0.75, y: 0.38, z: -0.78, isFront: false }
      ];

      if (isJamesian) {
        // Jamesian Front Steering Pivot Group
        jamesianFrontSteerGroup = new THREE.Group();
        jamesianFrontSteerGroup.position.set(0.75, 0.38, 0);
        roverGroup.add(jamesianFrontSteerGroup);

        wheelPositions.forEach(wp => {
          const w = makeDetailedWheel();
          if (wp.isFront) {
            w.position.set(0, 0, wp.z);
            jamesianFrontSteerGroup.add(w);
          } else {
            w.position.set(wp.x, wp.y, wp.z);
            roverGroup.add(w);
          }
          wheelsArray.push(w);
        });
        jamesianWheels = wheelsArray;
      } else {
        wheelPositions.forEach(wp => {
          const w = makeDetailedWheel();
          w.position.set(wp.x, wp.y, wp.z);
          roverGroup.add(w);
          wheelsArray.push(w);
        });
        vanillaWheels = wheelsArray;

        // ===============================================================
        // GLOWING NEON-RED COIL RING ON WHEEL HUB (MATCHING USER SKETCH)
        // ===============================================================
        // A sleek 3D Torus Ring mounted flat on the front-left wheel motor hubcap
        const ringGeo = new THREE.TorusGeometry(0.24, 0.038, 16, 32);
        // Position flat against the outer wheel face facing camera
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0xff1a00,
          transparent: true,
          opacity: 0.0
        });
        vanillaHeatGlowMesh = new THREE.Mesh(ringGeo, ringMat);
        // Front wheel is at x: 0.75, y: 0.38, z: 0.78; outer face is at z: 0.78 + 0.15
        vanillaHeatGlowMesh.position.set(0.75, 0.38, 0.935);
        roverGroup.add(vanillaHeatGlowMesh);

        // Dynamic Point Light casting ambient thermal heat on wheel and soil
        vanillaHeatLight = new THREE.PointLight(0xff2200, 0.0, 3.5);
        vanillaHeatLight.position.set(0.75, 0.38, 0.95);
        roverGroup.add(vanillaHeatLight);
      }

      // 4. JAMESIAN HARDWARE ADDON (Brushed Gold Heatsink & Emerald Optical Bus)
      if (isJamesian) {
        const addonGroup = new THREE.Group();
        addonGroup.position.set(-0.15, 1.15, 0);

        // Gold Heatsink Module Base
        const goldMat = new THREE.MeshStandardMaterial({
          color: 0xFDC57E,
          metalness: 0.94,
          roughness: 0.20
        });
        const heatsinkBase = new THREE.BoxGeometry(0.85, 0.12, 0.65);
        const hs = new THREE.Mesh(heatsinkBase, goldMat);
        hs.castShadow = true;
        addonGroup.add(hs);

        // Gold Ribbed Cooling Fins
        const finGeo = new THREE.BoxGeometry(0.85, 0.06, 0.03);
        for (let f = -0.25; f <= 0.25; f += 0.08) {
          const fin = new THREE.Mesh(finGeo, goldMat);
          fin.position.set(0, 0.08, f);
          fin.castShadow = true;
          addonGroup.add(fin);
        }

        // Emerald Green Glowing LED Data Bus Strip
        const ledGeo = new THREE.BoxGeometry(0.86, 0.04, 0.67);
        const ledMat = new THREE.MeshBasicMaterial({
          color: 0x10b981
        });
        jamesianLedMesh = new THREE.Mesh(ledGeo, ledMat);
        jamesianLedMesh.position.set(0, -0.02, 0);
        addonGroup.add(jamesianLedMesh);

        // Volumetric Emerald Point Light casting glow on chassis & ground
        jamesianOpticalLight = new THREE.PointLight(0x10b981, 1.4, 4.0);
        jamesianOpticalLight.position.set(0, 0.1, 0);
        addonGroup.add(jamesianOpticalLight);

        // Braided Gold Conduit Cables to Wheel Hubs
        const cableMat = new THREE.MeshStandardMaterial({
          color: 0xd4af37,
          metalness: 0.88,
          roughness: 0.35
        });
        const cableGeoL = new THREE.CylinderGeometry(0.025, 0.025, 0.8, 8);
        cableGeoL.rotateZ(Math.PI / 3);
        const cableL = new THREE.Mesh(cableGeoL, cableMat);
        cableL.position.set(0.2, 0, 0.45);
        addonGroup.add(cableL);

        const cableR = new THREE.Mesh(cableGeoL, cableMat);
        cableR.position.set(0.2, 0, -0.45);
        addonGroup.add(cableR);

        roverGroup.add(addonGroup);
      }

      return roverGroup;
    }

    function onWindowResize() {
      const container = document.querySelector('.sim-canvas-wrap');
      if (!container || !renderer || !camera) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }

    function toggleSim() {
      simPlaying = !simPlaying;
      document.getElementById('simPlayBtn').innerText = simPlaying ? 'Pause ⏸' : 'Play ▶';
    }

    function scrubSim(val) {
      simTime = parseFloat(val);
      updateSimKinematics(0);
    }

    // Helper: Cubic Smoothstep Interpolation
    function smoothstep(t) {
      const x = Math.max(0, Math.min(1, t));
      return x * x * (3 - 2 * x);
    }

    // ====================================================================
    // KINEMATIC ANIMATION LOOP: LANE A (VANILLA @ Z=2.6) & LANE B (JAMESIAN @ Z=-2.6)
    // ====================================================================
    function updateSimKinematics(dt) {
      if (simPlaying) {
        simTime += dt;
        if (simTime > simDuration) simTime = 0;
      }

      document.getElementById('simScrubber').value = simTime;
      document.getElementById('simTimeDisplay').innerText = `${simTime.toFixed(1)}s`;

      // ---------------------------------------------------------------
      // PHASE 1: 0.0s – 3.0s (Straight Approach: Driving to x = -0.6)
      // ---------------------------------------------------------------
      if (simTime < 3.0) {
        const u = smoothstep(simTime / 3.0);
        const posX = -5.2 + u * 4.6; // Approaches -0.6

        // LANE A: Vanilla Rover in foreground/left at Z = 2.6
        vanillaRover.position.set(posX, 0, 2.6);
        vanillaRover.rotation.set(0, 0, 0);

        // LANE B: Jamesian Rover in background/right at Z = -2.6
        jamesianRover.position.set(posX, 0, -2.6);
        jamesianRover.rotation.set(0, 0, 0);
        if (jamesianFrontSteerGroup) jamesianFrontSteerGroup.rotation.y = 0;

        // Wheels spin forward
        vanillaWheels.forEach(w => w.rotation.z -= dt * 6.5);
        jamesianWheels.forEach(w => w.rotation.z -= dt * 6.5);

        // Visuals
        if (vanillaHeatGlowMesh) vanillaHeatGlowMesh.material.opacity = 0.0;
        if (vanillaHeatLight) vanillaHeatLight.intensity = 0.0;
        if (jamesianLedMesh) jamesianLedMesh.material.color.setHex(0x10b981);
        if (jamesianOpticalLight) jamesianOpticalLight.intensity = 1.4;

        setTelemetryState('NOMINAL', 25.0, 4.0, 'robot_actuator', 'AUTOPILOT', 25.0, '0.0%', '0-Token Cruise');
      }

      // ---------------------------------------------------------------
      // PHASE 2: 3.0s – 5.5s (Boulder Impact, Slip Sensing & Breaker Trip)
      // ---------------------------------------------------------------
      else if (simTime < 5.5) {
        // LANE A: Vanilla Stalls at boulder (x=-0.6, z=2.6) & violently spins wheels in sand
        vanillaRover.position.set(-0.6, 0, 2.6);
        vanillaWheels.forEach(w => w.rotation.z -= dt * 15.0); // 100% Slip spin!

        // LANE B: Jamesian stops completely at boulder (x=-0.6, z=-2.6)
        jamesianRover.position.set(-0.6, 0, -2.6);
        jamesianRover.rotation.set(0, 0, 0);
        if (jamesianFrontSteerGroup) jamesianFrontSteerGroup.rotation.y = 0;

        // Coil heat rising in Vanilla -> Glowing Neon-Red Ring starts fading in
        const tProgress = (simTime - 3.0) / 2.5;
        const vTemp = 25.0 + tProgress * 42.0; // 25°C -> 67°C
        if (vanillaHeatGlowMesh) {
          vanillaHeatGlowMesh.material.opacity = tProgress * 0.75;
          const pulse = 1.0 + 0.08 * Math.sin(simTime * 15);
          vanillaHeatGlowMesh.scale.set(pulse, pulse, 1.0);
        }
        if (vanillaHeatLight) vanillaHeatLight.intensity = tProgress * 1.6;

        // Jamesian Optical Bus pulses with high-frequency alert
        if (jamesianLedMesh) {
          const pulse = Math.sin(simTime * 18) * 0.5 + 0.5;
          jamesianLedMesh.material.color.setRGB(1.0 * pulse, 0.78 * pulse, 0.15); // Pulsing Gold alert
        }
        if (jamesianOpticalLight) {
          jamesianOpticalLight.color.setHex(0xFDC57E);
          jamesianOpticalLight.intensity = 2.0;
        }

        setTelemetryState('SLIP BLOCKED', vTemp, 20.0, 'robot_actuator (Mash)', 'ALERT: 81% SLIP', 28.4, '81.0% (Detected)', 'Efference Trip');
      }

      // ---------------------------------------------------------------
      // PHASE 3: 5.5s – 7.2s (TURN 1: Jamesian 90° Turn to Lateral Bypass Lane)
      // ---------------------------------------------------------------
      else if (simTime < 7.2) {
        // LANE A: Vanilla remains trapped, coil heating intensifies
        vanillaRover.position.set(-0.6, 0, 2.6);
        vanillaWheels.forEach(w => w.rotation.z -= dt * 16.0);
        const tProgress = (simTime - 5.5) / 1.7;
        const vTemp = 67.0 + tProgress * 18.0; // 67°C -> 85°C
        if (vanillaHeatGlowMesh) {
          vanillaHeatGlowMesh.material.opacity = 0.75 + tProgress * 0.2;
          const pulse = 1.0 + 0.12 * Math.sin(simTime * 18);
          vanillaHeatGlowMesh.scale.set(pulse, pulse, 1.0);
        }
        if (vanillaHeatLight) vanillaHeatLight.intensity = 1.6 + tProgress * 1.2;

        // LANE B: Jamesian Executes First 90° Turn: rotates heading from 0 to +PI/2 (facing -Z / outer terrain)
        const uTurn = smoothstep(tProgress);
        const angle = uTurn * (Math.PI / 2); // 0 to +90 deg
        jamesianRover.position.set(-0.6, 0, -2.6);
        jamesianRover.rotation.y = angle;

        // Front wheels pivot smoothly during turn
        if (jamesianFrontSteerGroup) {
          jamesianFrontSteerGroup.rotation.y = Math.sin(uTurn * Math.PI) * 0.65;
        }

        if (jamesianLedMesh) jamesianLedMesh.material.color.setHex(0x10b981);
        if (jamesianOpticalLight) {
          jamesianOpticalLight.color.setHex(0x10b981);
          jamesianOpticalLight.intensity = 1.6;
        }

        setTelemetryState('ATTRACTOR TRAP', vTemp, 20.0, 'robot_actuator (Mash)', 'BREAKER FIRED', 31.8, 'Forward Locked', 'turn_bearing(90°)');
      }

      // ---------------------------------------------------------------
      // PHASE 4: 7.2s – 9.0s (LATERAL BYPASS: Driving Along -Z Clear of Rock)
      // ---------------------------------------------------------------
      else if (simTime < 9.0) {
        // LANE A: Vanilla coil breaches derating limit (85°C -> 98°C)
        vanillaRover.position.set(-0.6, 0, 2.6);
        vanillaWheels.forEach(w => w.rotation.z -= dt * 16.0);
        const tProgress = (simTime - 7.2) / 1.8;
        const vTemp = 85.0 + tProgress * 13.0; // 85°C -> 98°C
        if (vanillaHeatGlowMesh) {
          vanillaHeatGlowMesh.material.opacity = 0.95;
          const pulse = 1.0 + 0.15 * Math.sin(simTime * 22);
          vanillaHeatGlowMesh.scale.set(pulse, pulse, 1.0);
        }
        if (vanillaHeatLight) vanillaHeatLight.intensity = 2.8 + tProgress * 1.0;

        // LANE B: Jamesian drives straight along -Z heading (Z moves from -2.6 to -4.5)
        const uDrive = smoothstep(tProgress);
        const posZ = -2.6 - uDrive * 1.9; // Shift from Z=-2.6 to Z=-4.5 (outer bypass)
        jamesianRover.position.set(-0.6, 0, posZ);
        jamesianRover.rotation.y = Math.PI / 2; // Fixed at +90 deg
        if (jamesianFrontSteerGroup) jamesianFrontSteerGroup.rotation.y = 0;

        // Wheels spin forward in the -Z direction
        jamesianWheels.forEach(w => w.rotation.z -= dt * 6.0);

        setTelemetryState('CRITICAL HEAT', vTemp, 20.0, 'robot_actuator (Mash)', 'BYPASSING OBSTACLE', 33.5, 'Obstacle Cleared', 'Lateral Drive (-Z)');
      }

      // ---------------------------------------------------------------
      // PHASE 5: 9.0s – 10.3s (TURN 2: 90° Counter-Turn to Re-Align Forward)
      // ---------------------------------------------------------------
      else if (simTime < 10.3) {
        // LANE A: Vanilla temperature peaks near destruction (98°C -> 104.9°C)
        vanillaRover.position.set(-0.6, 0, 2.6);
        vanillaWheels.forEach(w => w.rotation.z -= dt * 14.0);
        const tProgress = (simTime - 9.0) / 1.3;
        const vTemp = 98.0 + tProgress * 6.9; // 98°C -> 104.9°C
        if (vanillaHeatGlowMesh) {
          vanillaHeatGlowMesh.material.opacity = 1.0;
          const pulse = 1.0 + 0.18 * Math.sin(simTime * 25);
          vanillaHeatGlowMesh.scale.set(pulse, pulse, 1.0);
        }
        if (vanillaHeatLight) vanillaHeatLight.intensity = 3.8;

        // LANE B: Jamesian executes second 90° turn: rotates from +PI/2 back to 0 (facing +X)
        const uTurn = smoothstep(tProgress);
        const angle = Math.PI / 2 - uTurn * (Math.PI / 2); // +90 deg back to 0 deg
        jamesianRover.position.set(-0.6, 0, -4.5);
        jamesianRover.rotation.y = angle;

        if (jamesianFrontSteerGroup) {
          jamesianFrontSteerGroup.rotation.y = -Math.sin(uTurn * Math.PI) * 0.65;
        }

        setTelemetryState('ENAMEL BURNOUT', vTemp, 20.0, 'robot_actuator (Mash)', 'RE-ALIGNING HEADING', 34.2, 'Lane Clear', 'turn_bearing(-90°)');
      }

      // ---------------------------------------------------------------
      // PHASE 6: 10.3s – 12.0s (STRAIGHT CRUISE: 0-Token Autopilot in Clear Track)
      // ---------------------------------------------------------------
      else {
        // LANE A: Vanilla is dead: motor coil destroyed, hardware burnout at 104.9°C
        vanillaRover.position.set(-0.6, 0, 2.6);
        if (vanillaHeatGlowMesh) {
          vanillaHeatGlowMesh.material.opacity = 1.0;
          const pulse = 1.0 + 0.08 * Math.sin(simTime * 8);
          vanillaHeatGlowMesh.scale.set(pulse, pulse, 1.0);
        }
        if (vanillaHeatLight) vanillaHeatLight.intensity = 3.8;

        // LANE B: Jamesian drives straight forward past the rock along bypass lane (Z = -4.5)
        const tProgress = (simTime - 10.3) / 1.7;
        const uDrive = smoothstep(tProgress);
        const posX = -0.6 + uDrive * 4.4; // Drives past rock to x = 3.8
        jamesianRover.position.set(posX, 0, -4.5);
        jamesianRover.rotation.set(0, 0, 0);
        if (jamesianFrontSteerGroup) jamesianFrontSteerGroup.rotation.y = 0;

        // Wheels spin smoothly forward
        jamesianWheels.forEach(w => w.rotation.z -= dt * 6.5);

        setTelemetryState('DEAD (MELTED)', 104.9, 0.0, 'COIL DESTROYED', 'SAFE CRUISING', 34.7, '0.0% Slip', '0-Token Autopilot');
      }
    }

    function setTelemetryState(vBadge, vTemp, vAmp, vAct, jBadge, jTemp, jSlip, jReflex) {
      // Vanilla HUD
      document.getElementById('vanillaBadge').innerText = vBadge;
      document.getElementById('vanillaTemp').innerText = `${vTemp.toFixed(1)} °C`;
      document.getElementById('vanillaCurrent').innerText = `${vAmp.toFixed(1)} A`;
      document.getElementById('vanillaAction').innerText = vAct;

      // Jamesian HUD
      document.getElementById('jamesianBadge').innerText = jBadge;
      document.getElementById('jamesianTemp').innerText = `${jTemp.toFixed(1)} °C`;
      document.getElementById('jamesianSlip').innerText = jSlip;
      document.getElementById('jamesianReflex').innerText = jReflex;
    }

    let lastClockTime = performance.now();
    function animate3D() {
      requestAnimationFrame(animate3D);
      const now = performance.now();
      const dt = (now - lastClockTime) / 1000;
      lastClockTime = now;

      if (currentSlide === 2) {
        updateSimKinematics(dt);
        renderer.render(scene, camera);
      }
    }
"""

pattern = r"// ====================================================================\s*// THREE\.JS 3D MARS SIMULATION.*"
code = re.sub(pattern, three_block + "\n    // Initialize Everything\n    window.addEventListener('DOMContentLoaded', () => {\n      init3D();\n      updateScriptDrawer();\n    });\n  </script>\n</body>\n</html>", code, flags=re.DOTALL)

with open('personal_notes/deck_v3.html', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated deck_v3.html successfully! New length:', len(code))

