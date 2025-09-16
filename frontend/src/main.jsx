import React from 'react'
import { createRoot } from 'react-dom/client'
import Dashboard from './components/Dashboard'
import Landing3D from './components/Landing3D'

function App() {
  return (
    <div style={{ fontFamily: 'Arial, sans-serif' }}>
      <div style={{ height: '60vh', border: '1px solid #ccc' }}>
        <Landing3D predictionScore={0.8} />
      </div>
      <div style={{ padding: '20px' }}>
        <Dashboard />
      </div>
    </div>
  )
}

const root = createRoot(document.getElementById('root'))
root.render(<App />)



