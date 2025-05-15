import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'

function App() {
  const [health, setHealth] = useState<{ status: string; message: string } | null>(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get('/api/health')
        setHealth(response.data)
      } catch (error) {
        console.error('Failed to fetch health status:', error)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">Flask + TypeScript App</h1>
        </div>
      </header>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="border-4 border-dashed border-gray-200 rounded-lg p-4">
              <Routes>
                <Route
                  path="/"
                  element={
                    <div>
                      <h2 className="text-xl font-semibold mb-4">Welcome to the App</h2>
                      {health ? (
                        <div className="text-green-600">
                          Backend Status: {health.status} - {health.message}
                        </div>
                      ) : (
                        <div className="text-yellow-600">Checking backend status...</div>
                      )}
                    </div>
                  }
                />
              </Routes>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App 