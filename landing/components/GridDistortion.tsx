"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

type Props = {
  className?: string;
  /** 0..1 — how strongly the cursor warps the grid. */
  strength?: number;
  /** How quickly the wave decays (lower = slower). */
  relaxation?: number;
  gridSize?: number;
};

/**
 * Mouse-reactive ripple distortion of a procedural grid. Renders into
 * a fixed canvas inside the wrapping element. Pauses its rAF loop
 * whenever it leaves the viewport.
 */
export function GridDistortion({
  className,
  strength = 0.3,
  relaxation = 0.93,
  gridSize = 22,
}: Props) {
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      premultipliedAlpha: false,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    wrap.appendChild(renderer.domElement);
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const dataTexture = createDataTexture(gridSize);

    const uniforms = {
      uTime: { value: 0 },
      uResolution: { value: new THREE.Vector2(1, 1) },
      uMouse: { value: new THREE.Vector2(0.5, 0.5) },
      uDataTexture: { value: dataTexture },
      uStrength: { value: strength },
    };

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader,
      fragmentShader,
      transparent: true,
    });
    const geometry = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    let width = wrap.clientWidth || 1;
    let height = wrap.clientHeight || 1;

    const resize = () => {
      width = wrap.clientWidth || 1;
      height = wrap.clientHeight || 1;
      renderer.setSize(width, height, false);
      uniforms.uResolution.value.set(width, height);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(wrap);

    const mouse = { x: 0.5, y: 0.5, vx: 0, vy: 0, prevX: 0.5, prevY: 0.5 };
    const onMove = (e: MouseEvent) => {
      const rect = wrap.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = (e.clientY - rect.top) / rect.height;
      mouse.vx = x - mouse.prevX;
      mouse.vy = y - mouse.prevY;
      mouse.prevX = x;
      mouse.prevY = y;
      mouse.x = x;
      mouse.y = y;
    };
    window.addEventListener("mousemove", onMove);

    let visible = true;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          visible = entry.isIntersecting;
        });
      },
      { threshold: 0 }
    );
    io.observe(wrap);

    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      if (!visible) return;
      uniforms.uTime.value += 0.01;
      updateDataTexture(dataTexture, gridSize, mouse, relaxation);
      renderer.render(scene, camera);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      ro.disconnect();
      io.disconnect();
      geometry.dispose();
      material.dispose();
      dataTexture.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === wrap) {
        wrap.removeChild(renderer.domElement);
      }
    };
  }, [strength, relaxation, gridSize]);

  return (
    <div
      ref={wrapRef}
      className={`pointer-events-none absolute inset-0 ${className ?? ""}`}
    />
  );
}

function createDataTexture(size: number) {
  const data = new Float32Array(size * size * 4);
  for (let i = 0; i < size * size; i++) {
    data[i * 4 + 0] = 0;
    data[i * 4 + 1] = 0;
    data[i * 4 + 2] = 0;
    data[i * 4 + 3] = 1;
  }
  const tex = new THREE.DataTexture(
    data,
    size,
    size,
    THREE.RGBAFormat,
    THREE.FloatType
  );
  tex.magFilter = THREE.NearestFilter;
  tex.minFilter = THREE.NearestFilter;
  tex.needsUpdate = true;
  return tex;
}

function updateDataTexture(
  tex: THREE.DataTexture,
  size: number,
  mouse: { x: number; y: number; vx: number; vy: number },
  relaxation: number
) {
  const data = tex.image.data as unknown as Float32Array;
  // Decay
  for (let i = 0; i < size * size; i++) {
    data[i * 4 + 0] *= relaxation;
    data[i * 4 + 1] *= relaxation;
  }
  // Inject mouse velocity
  const gridMouseX = mouse.x * size;
  const gridMouseY = (1 - mouse.y) * size;
  const maxDist = size * 0.18;
  const aspect = 1;
  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      const dx = gridMouseX - i;
      const dy = gridMouseY - j;
      const dist = dx * dx + dy * dy;
      if (dist < maxDist * maxDist) {
        const idx = 4 * (i + size * j);
        let power = maxDist / Math.sqrt(dist);
        power = Math.min(power, 10);
        data[idx + 0] += mouse.vx * power * 80 * aspect;
        data[idx + 1] -= mouse.vy * power * 80;
      }
    }
  }
  tex.needsUpdate = true;
}

const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position, 1.0);
  }
`;

const fragmentShader = `
  uniform vec2 uResolution;
  uniform sampler2D uDataTexture;
  uniform float uTime;
  uniform float uStrength;
  varying vec2 vUv;

  // procedural grid colour — soft ember dots on a dark canvas
  vec3 gridColour(vec2 uv) {
    vec2 grid = fract(uv * 36.0);
    float lineX = smoothstep(0.0, 0.04, grid.x) * smoothstep(1.0, 0.96, grid.x);
    float lineY = smoothstep(0.0, 0.04, grid.y) * smoothstep(1.0, 0.96, grid.y);
    float line = 1.0 - min(lineX, lineY);
    vec3 ember = vec3(0.984, 0.573, 0.235);
    vec3 violet = vec3(0.654, 0.545, 0.980);
    vec3 base = mix(ember, violet, smoothstep(0.0, 1.0, uv.y));
    return base * line * 0.55;
  }

  void main() {
    vec4 offset = texture2D(uDataTexture, vUv);
    vec2 displaced = vUv + uStrength * offset.rg * 0.01;
    vec3 col = gridColour(displaced);
    // subtle vignette
    float vig = smoothstep(1.1, 0.4, length(vUv - 0.5));
    col *= vig;
    gl_FragColor = vec4(col, 1.0);
  }
`;
