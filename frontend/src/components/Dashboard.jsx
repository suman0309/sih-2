import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  RadialLinearScale,
  Title,
  Tooltip,
} from 'chart.js'
import React, { useEffect, useMemo, useState } from 'react'
import { Bar, Line, Radar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  RadialLinearScale,
  Tooltip,
  Legend,
  Title,
)

function LanguageSelector({ currentLang, onLanguageChange }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <label htmlFor="lang" style={{ fontSize: '14px', fontWeight: '500' }}>Language</label>
      <select
        id="lang"
        value={currentLang}
        onChange={(e) => onLanguageChange(e.target.value)}
        style={{ border: '1px solid #ccc', borderRadius: '4px', padding: '4px 8px', fontSize: '14px' }}
      >
        <option value="en">English</option>
        <option value="hi">हिन्दी</option>
        <option value="or">ଓଡିଆ</option>
      </select>
    </div>
  )
}

function YieldPredictionCard({ predictions }) {
  const lineData = useMemo(() => ({
    labels: Array.from({ length: 7 }).map((_, i) => `Day ${i + 1}`),
    datasets: [
      {
        label: 'Predicted Yield (t/ha)',
        data: predictions?.trend || [3.2, 3.3, 3.35, 3.4, 3.42, 3.45, 3.5],
        borderColor: '#36a2eb',
        backgroundColor: 'rgba(54,162,235,0.2)',
        tension: 0.3,
      },
    ],
  }), [predictions])

  const barData = useMemo(() => ({
    labels: ['Rice', 'Wheat', 'Maize', 'Sugarcane'],
    datasets: [
      {
        label: 'Confidence',
        data: predictions?.confidence || [0.82, 0.76, 0.71, 0.79],
        backgroundColor: ['#4bc0c0', '#ffcd56', '#ff9f40', '#9966ff'],
      },
    ],
  }), [predictions])

  const radarData = useMemo(() => ({
    labels: ['Rainfall', 'Temperature', 'Soil Moisture', 'N', 'P', 'K'],
    datasets: [
      {
        label: 'Risk Factors',
        data: predictions?.risks || [60, 40, 70, 35, 45, 50],
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
      },
    ],
  }), [predictions])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px' }}>
        <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>Yield Forecast</h3>
        <Line data={lineData} options={{ responsive: true, maintainAspectRatio: false }} height={180} />
      </div>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px' }}>
        <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>Model Confidence</h3>
        <Bar data={barData} options={{ responsive: true, maintainAspectRatio: false }} height={180} />
      </div>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px' }}>
        <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>Risk Radar</h3>
        <Radar data={radarData} options={{ responsive: true, maintainAspectRatio: false }} height={180} />
      </div>
    </div>
  )
}

function WeatherWidget() {
  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px', marginTop: '20px' }}>
      <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>Weather</h3>
      <p style={{ fontSize: '14px', color: '#666' }}>Connected to IMD for real-time updates.</p>
    </div>
  )
}

function SoilHealthCard() {
  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px', marginTop: '20px' }}>
      <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>Soil Health</h3>
      <p style={{ fontSize: '14px', color: '#666' }}>Nutrient plan and pH adjustments from SHC.</p>
    </div>
  )
}

function ARCropScanner() {
  return (
    <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', padding: '20px', marginTop: '20px' }}>
      <h3 style={{ fontWeight: 'bold', marginBottom: '10px' }}>AR Crop Scanner</h3>
      <p style={{ fontSize: '14px', color: '#666' }}>Scan crops for issues (coming soon).</p>
    </div>
  )
}

export default function Dashboard() {
  const [predictions, setPredictions] = useState(null)
  const [selectedLanguage, setSelectedLanguage] = useState('en')

  useEffect(() => {
    // TODO: Replace with real API call to backend predictor
    const timer = setTimeout(() => {
      setPredictions({
        trend: [3.2, 3.31, 3.35, 3.41, 3.46, 3.5, 3.58],
        confidence: [0.84, 0.76, 0.72, 0.8],
        risks: [55, 42, 68, 35, 45, 51],
      })
    }, 400)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 'bold' }}>Interactive Dashboard</h2>
        <LanguageSelector currentLang={selectedLanguage} onLanguageChange={setSelectedLanguage} />
      </div>

      <YieldPredictionCard predictions={predictions} />
      <WeatherWidget />
      <SoilHealthCard />
      <ARCropScanner />
    </div>
  )
}


