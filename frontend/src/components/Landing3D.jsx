import React, { Suspense, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text3D, Environment } from '@react-three/drei'
import * as THREE from 'three'

function InstancedCrops({ count = 500, predictionScore = 0.7 }) {
  const meshRef = useRef()
  const dummy = useMemo(() => new THREE.Object3D(), [])

  // Stable random positions/sizes per mount
  const seeds = useMemo(() => {
    const rng = new Math.seedrandom ? new Math.seedrandom('krishi') : null
    const values = []
    for (let i = 0; i < count; i++) {
      const rx = rng ? rng() : Math.random()
      const rz = rng ? rng() : Math.random()
      const rh = rng ? rng() : Math.random()
      values.push({
        x: rx * 8 - 4,
        z: rz * 8 - 4,
        h: 0.6 + rh * 1.8,
        r: (rng ? rng() : Math.random()) * Math.PI * 2,
      })
    }
    return values
  }, [count])

  useFrame((state) => {
    const t = state.clock.elapsedTime
    const growth = THREE.MathUtils.clamp(predictionScore, 0, 1)
    seeds.forEach((s, i) => {
      const sway = Math.sin(t * 1.2 + s.r) * 0.04
      const height = THREE.MathUtils.lerp(0.3, s.h, growth)
      dummy.position.set(s.x, height / 2, s.z)
      dummy.rotation.set(0, s.r + sway, 0)
      dummy.scale.set(0.06, height, 0.06)
      dummy.updateMatrix()
      meshRef.current.setMatrixAt(i, dummy.matrix)
    })
    meshRef.current.instanceMatrix.needsUpdate = true
  })

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <cylinderGeometry args={[0.05, 0.05, 1, 6]} />
      <meshStandardMaterial color="#2d5016" roughness={0.8} metalness={0.05} />
    </instancedMesh>
  )
}

function FarmField({ predictionScore = 0.7, cropCount = 500 }) {
  const fieldRef = useRef()
  useFrame((state) => {
    if (!fieldRef.current) return
    fieldRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.06
  })
  return (
    <group ref={fieldRef}>
      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[18, 18, 64, 64]} />
        <meshStandardMaterial color="#4a7c59" />
      </mesh>
      <InstancedCrops count={cropCount} predictionScore={predictionScore} />
    </group>
  )
}

export default function Landing3D({ predictionScore = 0.7, headline = 'Krishi AI', cropCount = 500 }) {
  return (
    <div className="h-screen">
      <Canvas dpr={[1, 2]} camera={{ position: [7, 6, 7], fov: 50 }} shadows>
        <Suspense fallback={null}>
          <Environment preset="sunset" />
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 12, 6]} intensity={1.1} castShadow />

          <FarmField predictionScore={predictionScore} cropCount={cropCount} />

          <mesh position={[-3.5, 2.8, 0]}>
            <boxGeometry args={[2, 0.5, 0.1]} />
            <meshStandardMaterial color="#ff6b6b" />
          </mesh>

          <OrbitControls enablePan={false} enableZoom={false} minPolarAngle={0.7} maxPolarAngle={1.2} />
        </Suspense>
      </Canvas>
    </div>
  )
}


