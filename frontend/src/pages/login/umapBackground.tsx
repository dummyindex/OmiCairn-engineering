import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
const csvFile = '/test_dataset.csv';

interface UmapBackgroundProps {
  opacity?: number;
  onCellCountChange?: (count: number) => void;
}

interface CellData {
  position: THREE.Vector3;
  color: number;
  type: string;
}

const UmapBackground: React.FC<UmapBackgroundProps> = ({ opacity = 0.3, onCellCountChange }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const animationIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000,
    );
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    mountRef.current.appendChild(renderer.domElement);

    sceneRef.current = scene;
    rendererRef.current = renderer;

    // Color palette for different cell types
    const colorPalette = [
      0x3498db, // Professional blue
      0x2ecc71, // Academic green
      0xe74c3c, // Muted red
      0xf39c12, // Academic orange
      0x9b59b6, // Professional purple
      0x1abc9c, // Teal
      0xe67e22, // Carrot orange
      0x34495e, // Wet asphalt
      0xf1c40f, // Sunflower yellow
      0x8e44ad, // Wisteria purple
    ];

    async function loadCSVData(): Promise<CellData[]> {
      try {
        const response = await fetch(csvFile);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvText = await response.text();

        const lines = csvText.split('\n');
        const headers = lines[0].split(',').map((h) => h.trim());

        const findColumnIndex = (possibleNames: string[]) => {
          return headers.findIndex((header) =>
            possibleNames.some((name) => header.toLowerCase().includes(name.toLowerCase())),
          );
        };

        const xIndex = findColumnIndex(['UMAP_0']);
        const yIndex = findColumnIndex(['UMAP_1']);
        const zIndex = findColumnIndex(['UMAP_2']);
        const typeIndex = findColumnIndex(['celltype']);

        if (xIndex === -1 || yIndex === -1) {
          throw new Error('Could not find X and Y coordinate columns in CSV');
        }

        const cells: CellData[] = [];
        const cellTypeColors = new Map<string, number>();
        let colorIndex = 0;

        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim();
          if (!line) continue;

          const values = line.split(',');
          if (values.length < Math.max(xIndex, yIndex) + 1) continue;

          const x = parseFloat(values[xIndex]);
          const y = parseFloat(values[yIndex]);
          const z = zIndex !== -1 ? parseFloat(values[zIndex]) : 0;
          const cellType = typeIndex !== -1 ? values[typeIndex].trim() : 'Unknown';

          if (isNaN(x) || isNaN(y)) continue;

          if (!cellTypeColors.has(cellType)) {
            cellTypeColors.set(cellType, colorPalette[colorIndex % colorPalette.length]);
            colorIndex++;
          }

          cells.push({
            position: new THREE.Vector3(x, y, z),
            color: cellTypeColors.get(cellType)!,
            type: cellType,
          });
        }

        return cells;
      } catch (error) {
        console.error('Error loading CSV data:', error);
        return generateMockData();
      }
    }

    function generateMockData(): CellData[] {
      const cells: CellData[] = [];
      const cellTypes = [
        { name: 'T cells', color: 0x3498db, count: 800 },
        { name: 'B cells', color: 0x2ecc71, count: 600 },
        { name: 'NK cells', color: 0xe74c3c, count: 400 },
        { name: 'Monocytes', color: 0xf39c12, count: 500 },
        { name: 'Dendritic', color: 0x9b59b6, count: 300 },
        { name: 'Neutrophils', color: 0x1abc9c, count: 247 },
      ];

      cellTypes.forEach((cellType) => {
        for (let i = 0; i < cellType.count; i++) {
          const angle = Math.random() * Math.PI * 2;
          const radius = Math.random() * 0.5 + 0.2;
          const clusterX = Math.cos(angle) * radius;
          const clusterY = Math.sin(angle) * radius;

          const x = clusterX + (Math.random() - 0.5) * 0.3;
          const y = clusterY + (Math.random() - 0.5) * 0.3;
          const z = (Math.random() - 0.5) * 0.2;

          cells.push({
            position: new THREE.Vector3(x * 15, y * 15, z * 15),
            color: cellType.color,
            type: cellType.name,
          });
        }
      });

      return cells;
    }

    function normalizeAndScaleData(cells: CellData[]): CellData[] {
      if (cells.length === 0) return cells;

      const bounds = {
        x: { min: Infinity, max: -Infinity },
        y: { min: Infinity, max: -Infinity },
        z: { min: Infinity, max: -Infinity },
      };

      cells.forEach((cell) => {
        bounds.x.min = Math.min(bounds.x.min, cell.position.x);
        bounds.x.max = Math.max(bounds.x.max, cell.position.x);
        bounds.y.min = Math.min(bounds.y.min, cell.position.y);
        bounds.y.max = Math.max(bounds.y.max, cell.position.y);
        bounds.z.min = Math.min(bounds.z.min, cell.position.z);
        bounds.z.max = Math.max(bounds.z.max, cell.position.z);
      });

      const xRange = bounds.x.max - bounds.x.min;
      const yRange = bounds.y.max - bounds.y.min;
      const zRange = bounds.z.max - bounds.z.min;

      const scale = 30 / Math.max(xRange, yRange, zRange || 1);

      return cells.map((cell) => ({
        ...cell,
        position: new THREE.Vector3(
          (cell.position.x - bounds.x.min - xRange / 2) * scale,
          (cell.position.y - bounds.y.min - yRange / 2) * scale,
          (cell.position.z - bounds.z.min - zRange / 2) * scale,
        ),
      }));
    }

    async function initializeVisualization() {
      const rawCells = await loadCSVData();
      const cells = normalizeAndScaleData(rawCells);
      if (onCellCountChange) onCellCountChange(cells.length);

      const geometry = new THREE.BufferGeometry();
      const positions: number[] = [];
      const colors: number[] = [];

      cells.forEach((cell) => {
        positions.push(cell.position.x, cell.position.y, cell.position.z);
        const color = new THREE.Color(cell.color);
        colors.push(color.r, color.g, color.b);
      });

      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

      const material = new THREE.PointsMaterial({
        size: 0.2,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
      });

      const points = new THREE.Points(geometry, material);
      scene.add(points);

      createAxes();

      const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
      scene.add(ambientLight);

      camera.position.set(0, 0, 25);
      camera.lookAt(0, 0, 0);

      function animate() {
        animationIdRef.current = requestAnimationFrame(animate);

        points.rotation.y += 0.003;

        const time = Date.now() * 0.001;
        points.scale.setScalar(1 + Math.sin(time * 0.5) * 0.05);

        renderer.render(scene, camera);
      }

      animate();
    }

    function createAxes() {
      const axisLength = 20;
      const axisGeometry = new THREE.BufferGeometry();
      const axisPositions: number[] = [];
      const axisColors: number[] = [];

      // X-axis (red)
      axisPositions.push(-axisLength, 0, 0);
      axisPositions.push(axisLength, 0, 0);
      axisColors.push(0.8, 0.2, 0.2);
      axisColors.push(0.8, 0.2, 0.2);

      // Y-axis (green)
      axisPositions.push(0, -axisLength, 0);
      axisPositions.push(0, axisLength, 0);
      axisColors.push(0.2, 0.8, 0.2);
      axisColors.push(0.2, 0.8, 0.2);

      // Z-axis (blue)
      axisPositions.push(0, 0, -axisLength);
      axisPositions.push(0, 0, axisLength);
      axisColors.push(0.2, 0.2, 0.8);
      axisColors.push(0.2, 0.2, 0.8);

      axisGeometry.setAttribute('position', new THREE.Float32BufferAttribute(axisPositions, 3));
      axisGeometry.setAttribute('color', new THREE.Float32BufferAttribute(axisColors, 3));

      const axisMaterial = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.6,
      });

      const axes = new THREE.LineSegments(axisGeometry, axisMaterial);
      scene.add(axes);
    }

    // Handle window resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('resize', handleResize);

    function createFloatingParticles() {
      const particleGeometry = new THREE.BufferGeometry();
      const particleCount = 500;
      const particlePositions: number[] = [];

      for (let i = 0; i < particleCount; i++) {
        particlePositions.push(
          (Math.random() - 0.5) * 100,
          (Math.random() - 0.5) * 100,
          (Math.random() - 0.5) * 100,
        );
      }

      particleGeometry.setAttribute(
        'position',
        new THREE.Float32BufferAttribute(particlePositions, 3),
      );

      const particleMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.3,
        transparent: true,
        opacity: 0.3,
      });

      const particles = new THREE.Points(particleGeometry, particleMaterial);
      scene.add(particles);

      const animateParticles = () => {
        particles.rotation.x += 0.001;
        particles.rotation.y += 0.001;
        setTimeout(animateParticles, 16);
      };
      animateParticles();
    }

    createFloatingParticles();

    initializeVisualization();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 1,
        opacity,
        pointerEvents: 'none',
      }}
    />
  );
};

export default UmapBackground;
