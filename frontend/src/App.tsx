import React, { useState, useEffect, useCallback } from 'react';
import { ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Line } from 'recharts';
// import './App.css'; // Если есть стили - ПОКА ЗАКОММЕНТИРУЕМ

interface Metal {
  symbol: string
  name: string
  price: number
  unit: string
  timestamp: string
}

interface MetalPrice {
  symbol: string
  name: string
  price: number | null
  unit: string
  timestamp: string | null
}

interface MetalData {
  status: string
  data: MetalPrice[]
  message?: string
}

interface HistoricalPrice {
  price: number
  timestamp: string
}

interface MetalHistoryData {
  status: string
  data: HistoricalPrice[]
  message?: string
}

interface BackendStatus {
  status: string
  message: string
  timestamp?: string
  api_status?: string
}

const METALS = [
  { symbol: 'GOLD', name: 'Золото' },
  { symbol: 'SILVER', name: 'Серебро' },
  { symbol: 'PLATINUM', name: 'Платина' },
  { symbol: 'PALLADIUM', name: 'Палладий' },
]

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const App: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; message: string } | null>(null)
  const [metals, setMetals] = useState<Metal[] | null>(null)
  const [loadingMetals, setLoadingMetals] = useState(false)
  const [errorMetals, setErrorMetals] = useState<string | null>(null)
  const [updatingPrices, setUpdatingPrices] = useState(false)
  const [metalPrices, setMetalPrices] = useState<MetalPrice[]>([])
  const [selectedMetal, setSelectedMetal] = useState<string>('GOLD')
  const [dateFrom, setDateFrom] = useState<string>('2024-03-01')
  const [dateTo, setDateTo] = useState<string>('2024-03-10')
  const [metalHistory, setMetalHistory] = useState<HistoricalPrice[]>([])
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isHistoryLoading, setIsHistoryLoading] = useState<boolean>(false)
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null)
  const [selectedCurrency, setSelectedCurrency] = useState<string>('USD')

  const fetchBackendStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/metals/current?limit=1`)
      if (response.ok) {
        setBackendStatus({ status: 'healthy', message: 'API is running' })
      } else {
        setBackendStatus({ status: 'unhealthy', message: `API returned status: ${response.status}` })
      }
    } catch (err) {
      setBackendStatus({ status: 'unhealthy', message: 'API is unreachable' })
      console.error("Failed to fetch backend status:", err)
    }
  }, [])

  const fetchCurrentPrices = useCallback(async (currency: string) => {
    setIsLoading(true)
    setErrorMetals(null)
    try {
      const url = `${API_BASE_URL}/api/metals/current?currency=${currency}`
      const response = await fetch(url)
      if (!response.ok) {
        const errorData: MetalData = await response.json()
        throw new Error(errorData.message || `Ошибка ${response.status} при загрузке текущих цен`)
      }
      const data: MetalData = await response.json()
      if (data.status === 'success') {
        setMetalPrices(data.data)
      } else {
        throw new Error(data.message || 'Не удалось получить данные о ценах')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Произошла неизвестная ошибка при загрузке цен."
      setErrorMetals(errorMessage)
      console.error("Failed to fetch metal prices:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchHistory = useCallback(async () => {
    if (!selectedMetal || !dateFrom || !dateTo) {
      setHistoryError("Пожалуйста, выберите металл и даты для отображения истории.")
      return
    }
    setIsHistoryLoading(true)
    setHistoryError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/api/metals/history?metal=${selectedMetal}&date_from=${dateFrom}&date_to=${dateTo}`)
      if (!response.ok) {
        const errorData: MetalHistoryData = await response.json()
        throw new Error(errorData.message || `Ошибка ${response.status} при загрузке истории цен`)
      }
      const data: MetalHistoryData = await response.json()
      console.log('API Response (History):', data)
      if (data.status === 'success') {
        setMetalHistory(data.data)
        if (data.data.length === 0) {
          setHistoryError('Нет данных за выбранный период.')
        }
      } else {
        throw new Error(data.message || 'Не удалось получить исторические данные')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Произошла неизвестная ошибка при загрузке истории."
      setHistoryError(errorMessage)
      console.error("Failed to fetch metal history:", err)
    } finally {
      setIsHistoryLoading(false)
    }
  }, [selectedMetal, dateFrom, dateTo])

  useEffect(() => {
    fetchBackendStatus()
    fetchCurrentPrices(selectedCurrency)
  }, [fetchBackendStatus, fetchCurrentPrices, selectedCurrency])

  const handleShowHistory = () => {
    fetchHistory()
  }

  const handleCurrencyChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCurrency(event.target.value)
  }

  // Функция для форматирования цены, чтобы избежать ошибок с toLocaleString для null
  const formatPrice = (price: number | null) => {
    if (price === null || typeof price === 'undefined') return 'N/A'
    return price.toLocaleString()
  }

  // Функция для форматирования даты, чтобы избежать ошибок с new Date для null
  const formatDate = (timestamp: string | null) => {
    if (!timestamp) return 'N/A'
    try {
      return new Date(timestamp).toLocaleString()
    } catch (e) {
      console.error("Invalid date format for timestamp:", timestamp, e)
      return 'Invalid Date'
    }
  }

  return (
    <div className="container mx-auto p-4 font-sans">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 text-center">Precious Metals Price Tracker</h1>
        {backendStatus && (
          <p className={`text-center text-sm mt-2 ${backendStatus.status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
            Backend Status: {backendStatus.status} - {backendStatus.message}
          </p>
        )}
      </header>

      <section className="mb-8 p-6 bg-white shadow-lg rounded-lg">
        <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
          <h2 className="text-2xl font-semibold text-gray-700">Текущие цены на металлы</h2>
          <div className="flex items-center">
            <label htmlFor="currency-select" className="mr-2 text-gray-600 whitespace-nowrap">Валюта:</label>
            <select 
              id="currency-select"
              value={selectedCurrency}
              onChange={handleCurrencyChange}
              className="p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 h-10"
            >
              <option value="USD">USD</option>
              <option value="RUB">RUB</option>
              {/* <option value="EUR">EUR</option> */}
            </select>
            <button 
              onClick={() => fetchCurrentPrices(selectedCurrency)} 
              className="ml-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out h-10"
              disabled={isLoading}
            >
              {isLoading ? 'Обновление...' : 'Обновить цены'}
            </button>
          </div>
        </div>
        {errorMetals && <p className="text-red-500 text-center mb-4">{errorMetals}</p>}
        {isLoading && !errorMetals ? (
          <p className="text-gray-500 text-center">Загрузка цен...</p>
        ) : metalPrices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Символ</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Название</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Цена</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Единица</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Дата</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {metalPrices.map((metal) => (
                  <tr key={metal.symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{metal.symbol}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{metal.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{formatPrice(metal.price)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{metal.unit}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(metal.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !isLoading && <p className="text-center text-gray-500">Нет данных для отображения.</p>
        )}
      </section>

      <section className="p-6 bg-white shadow-lg rounded-lg">
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">График изменения курса металла</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4 items-end">
          <div>
            <label htmlFor="metal-select" className="block text-sm font-medium text-gray-700 mb-1">Металл:</label>
            <select 
              id="metal-select"
              value={selectedMetal} 
              onChange={(e) => setSelectedMetal(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm h-10"
            >
              {METALS.map(m => <option key={m.symbol} value={m.symbol}>{m.name}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="date-from" className="block text-sm font-medium text-gray-700 mb-1">С:</label>
            <input 
              type="date" 
              id="date-from"
              value={dateFrom} 
              onChange={(e) => setDateFrom(e.target.value)} 
              className="mt-1 block w-full pl-3 pr-2 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm h-10"
            />
          </div>
          <div>
            <label htmlFor="date-to" className="block text-sm font-medium text-gray-700 mb-1">По:</label>
            <input 
              type="date" 
              id="date-to"
              value={dateTo} 
              onChange={(e) => setDateTo(e.target.value)} 
              className="mt-1 block w-full pl-3 pr-2 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md shadow-sm h-10"
            />
          </div>
          <button 
            onClick={handleShowHistory} 
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out h-10 md:self-end"
            disabled={isHistoryLoading}
          >
            {isHistoryLoading ? 'Загрузка графика...' : 'Показать график'}
          </button>
        </div>
        
        {historyError && <p className="text-red-500 text-center mb-4">{historyError}</p>}
        {isHistoryLoading && !historyError ? (
          <p className="text-gray-500 text-center">Загрузка данных для графика...</p>
        ) : metalHistory.length > 0 ? (
          <div className="h-96 bg-gray-50 p-4 rounded-md">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metalHistory} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(tick: any) => new Date(tick).toLocaleDateString()} />
                <YAxis />
                <Tooltip formatter={(value: number) => [`${value.toFixed(2)} ${(metalPrices.find(m => m.symbol === selectedMetal)?.unit?.split('/')[0]) || 'USD'}`, 'Цена']} />
                <Legend />
                <Line type="monotone" dataKey="price" stroke="#8884d8" activeDot={{ r: 8 }} name={`Цена ${selectedMetal}`} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          !isHistoryLoading && <p className="text-center text-gray-500">Нет данных для отображения графика. Выберите параметры и нажмите "Показать график".</p>
        )}
      </section>
    </div>
  )
}

export default App 