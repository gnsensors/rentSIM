import { useEffect, useState } from 'react'

const fmt = (n) => '$' + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })
const API = window.__API_URL__ || import.meta.env.VITE_API_URL || ''

function HouseCard({ house, onSell, onRemove }) {
  const gain = ((house.value - house.price) / house.price * 100).toFixed(1)

  return (
    <div className="bg-gray-800 rounded-xl p-4 space-y-2 border border-gray-700">
      <div className="flex justify-between items-start">
        <span className="text-xs text-gray-400 font-medium">
          {house.metadata?.market_label || `House #${house.id}`}
        </span>
        <div className="flex gap-2">
          <button onClick={() => onSell(house.id)} className="text-xs text-red-400 hover:text-red-300 transition-colors">
            Sell
          </button>
          <button onClick={() => onRemove(house.id)} className="text-xs text-gray-500 hover:text-red-400 transition-colors">
            Remove
          </button>
        </div>
      </div>

      <div className="flex justify-between">
        <span className="text-sm text-gray-300">Current value</span>
        <span className="tabular font-semibold text-white">{fmt(house.value)}</span>
      </div>

      <div className="flex justify-between text-xs text-gray-400">
        <span>Bought: {fmt(house.price)}</span>
        <span className={gain >= 0 ? 'text-income' : 'text-expense'}>
          {gain >= 0 ? '+' : ''}{gain}%
        </span>
      </div>

      <div className="flex justify-between">
        <span className="text-sm text-gray-300">Monthly expenses</span>
        <span className="tabular text-sm text-expense">{fmt(house.monthly_expenses)}</span>
      </div>

      {house.metadata?.bedrooms && (
        <div className="text-xs text-gray-500">
          {house.metadata.bedrooms}BR · {house.metadata.gross_yield_pct}% yield
        </div>
      )}
    </div>
  )
}

function BuyModal({ portfolioId, token, onBuy, onClose }) {
  const [houses, setHouses]   = useState(null)
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    const res = await fetch(`${API}/api/portfolios/${portfolioId}/available-houses`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    setHouses(await res.json())
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-40 p-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-2xl shadow-2xl p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold">Available Houses</h2>
          <div className="flex gap-2">
            <button onClick={load} className="text-xs text-gray-400 hover:text-white">Refresh</button>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
          </div>
        </div>

        {loading && <p className="text-center text-gray-400 py-8">Generating listings…</p>}

        <div className="grid grid-cols-2 gap-4">
          {houses?.map((h, i) => (
            <div
              key={i}
              className="bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-accent cursor-pointer transition-all space-y-2"
              onClick={() => { onBuy(h.price); onClose() }}
            >
              <div className="text-xs text-gray-400">{h.metadata?.market_label}</div>
              <div className="font-semibold">{fmt(h.price)}</div>
              <div className="text-sm text-income">~{fmt(h.expected_rent)}/mo rent</div>
              <div className="text-xs text-gray-400">
                {h.metadata?.bedrooms}BR · Down: {fmt(h.down_payment)}
              </div>
              <div className="text-xs text-gray-500">{h.metadata?.gross_yield_pct}% yield</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function HouseList({ houses = [], portfolioId, token, onSell, onRemove, onBuy, cash, reserved }) {
  const [showModal, setShowModal] = useState(false)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-200">Houses</h3>
        <span className="text-xs text-gray-400">{houses.length} owned</span>
      </div>

      {houses.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-8">No properties owned</p>
      )}

      <div className="space-y-3">
        {houses.map(h => (
          <HouseCard key={h.id} house={h} onSell={onSell} onRemove={onRemove} />
        ))}
      </div>

      <button
        onClick={() => setShowModal(true)}
        className="mt-auto w-full border border-dashed border-gray-600 hover:border-accent text-gray-400 hover:text-accent rounded-xl py-3 text-sm font-medium transition-all"
      >
        + Buy House
      </button>

      {showModal && (
        <BuyModal
          portfolioId={portfolioId}
          token={token}
          onBuy={onBuy}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  )
}
