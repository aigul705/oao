import { Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'

interface Metal {
  symbol: string
  name: string
  price: number
  unit: string
  timestamp: string
}

function App() {
  const [health, setHealth] = useState<{ status: string; message: string } | null>(null)
  const [metals, setMetals] = useState<Metal[] | null>(null)
  const [loadingMetals, setLoadingMetals] = useState(false)
  const [errorMetals, setErrorMetals] = useState<string | null>(null)
  const [updatingPrices, setUpdatingPrices] = useState(false)

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

  useEffect(() => {
    const fetchMetals = async () => {
      setLoadingMetals(true)
      setErrorMetals(null)
      try {
        const response = await axios.get('/api/metals/current')
        setMetals(response.data.data)
      } catch (error) {
        setErrorMetals('Не удалось загрузить цены на металлы')
      } finally {
        setLoadingMetals(false)
      }
    }
    fetchMetals()
  }, [])

  const updatePrices = async () => {
    setUpdatingPrices(true)
    try {
      await axios.post('/api/metals/update')
      const response = await axios.get('/api/metals/current')
      setMetals(response.data.data)
      setErrorMetals(null)
    } catch (error: any) {
      if (error.response && error.response.data && error.response.data.message) {
        setErrorMetals('Ошибка: ' + error.response.data.message)
      } else {
        setErrorMetals('Не удалось обновить цены на металлы')
      }
    } finally {
      setUpdatingPrices(false)
    }
  }

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
                        <div className="text-green-600 mb-4">
                          Backend Status: {health.status} - {health.message}
                        </div>
                      ) : (
                        <div className="text-yellow-600 mb-4">Checking backend status...</div>
                      )}

                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold">Текущие цены на металлы</h3>
                        <button
                          onClick={updatePrices}
                          disabled={updatingPrices}
                          className={`px-4 py-2 rounded ${
                            updatingPrices
                              ? 'bg-gray-400 cursor-not-allowed'
                              : 'bg-blue-500 hover:bg-blue-600'
                          } text-white`}
                        >
                          {updatingPrices ? 'Обновление...' : 'Обновить цены'}
                        </button>
                      </div>
                      {loadingMetals && <div>Загрузка...</div>}
                      {errorMetals && <div className="text-red-600">{errorMetals}</div>}
                      {metals && (
                        <div className="overflow-x-auto">
                          <table className="min-w-full bg-white border border-gray-200 rounded">
                            <thead>
                              <tr>
                                <th className="px-4 py-2 border-b">Символ</th>
                                <th className="px-4 py-2 border-b">Название</th>
                                <th className="px-4 py-2 border-b">Цена</th>
                                <th className="px-4 py-2 border-b">Единица</th>
                                <th className="px-4 py-2 border-b">Дата</th>
                              </tr>
                            </thead>
                            <tbody>
                              {metals.map((metal) => (
                                <tr key={metal.symbol}>
                                  <td className="px-4 py-2 border-b">{metal.symbol}</td>
                                  <td className="px-4 py-2 border-b">{metal.name}</td>
                                  <td className="px-4 py-2 border-b">{metal.price}</td>
                                  <td className="px-4 py-2 border-b">{metal.unit}</td>
                                  <td className="px-4 py-2 border-b">{metal.timestamp}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
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