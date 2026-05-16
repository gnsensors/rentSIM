import { useState } from 'react'

const fmt  = (n) => '$' + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })
const pct  = (n) => Number(n).toFixed(2) + '%'

export default function PortfolioControls({ state, month, connected, onStep, onInvest, onUpdateSettings }) {
  const [investAmt, setInvestAmt]   = useState('')
  const [reserveAmt, setReserveAmt] = useState(state?.reserved ?? '')
  const [autoBuy, setAutoBuy]       = useState(state?.auto_buy_threshold ?? '')
  const [autoStep, setAutoStep]     = useState(false)
  const [stepMs, setStepMs]         = useState(1000)
  const timerRef = useState(null)

  function toggleAuto() {
    if (autoStep) {
      clearInterval(timerRef[0])
      timerRef[0] = null
      setAutoStep(false)
    } else {
      timerRef[0] = setInterval(onStep, stepMs)
      setAutoStep(true)
    }
  }

  function handleInvest(e) {
    e.preventDefault()
    const amt = parseFloat(investAmt)
    if (!amt || amt <= 0) return
    onInvest(amt)
    setInvestAmt('')
  }

  function handleSettings() {
    onUpdateSettings({
      reserved: parseFloat(reserveAmt) || 0,
      auto_buy_threshold: autoBuy ? parseFloat(autoBuy) : null,
    })
  }

  if (!state) return <div className="text-gray-500 text-sm">Connecting…</div>

  const netCashflow = state.houses.reduce((s, h) => s + (h.monthly_expenses || 0), 0)

  return (
    <div className="flex flex-col gap-4">
      {/* Stats */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-sm text-gray-400">Cash</span>
          <span className={`tabular font-semibold ${state.cash >= 0 ? 'text-white' : 'text-expense'}`}>
            {fmt(state.cash)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-400">Assets</span>
          <span className="tabular text-white">{fmt(state.total_asset_value)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-400">Debt</span>
          <span className="tabular text-expense">{fmt(state.total_loan_balance)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-400">Invested</span>
          <span className="tabular text-gray-300">{fmt(state.invested)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-400">Price level</span>
          <span className="tabular text-gray-300" title="Cumulative price multiplier since month 0">
            ×{state.inflation.toFixed(3)}
          </span>
        </div>
      </div>

      <hr className="border-gray-700" />

      {/* Month controls */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Month</span>
          <span className="tabular text-white font-semibold">{month} / {state.length}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-1.5">
          <div
            className="bg-accent h-1.5 rounded-full transition-all"
            style={{ width: `${(month / state.length) * 100}%` }}
          />
        </div>
        <span className="text-xs text-gray-500">{state.life_remaining} months remaining</span>

        <button
          onClick={onStep}
          disabled={!connected}
          className="w-full bg-accent hover:bg-indigo-500 disabled:opacity-40 text-white font-semibold rounded-lg py-2 transition-all"
        >
          Next Month →
        </button>

        <div className="flex gap-2">
          <button
            onClick={toggleAuto}
            className={`flex-1 rounded-lg py-1.5 text-sm font-medium transition-all border
              ${autoStep ? 'border-accent text-accent' : 'border-gray-600 text-gray-400 hover:border-gray-400'}`}
          >
            {autoStep ? 'Stop Auto' : 'Auto'}
          </button>
          <select
            value={stepMs}
            onChange={e => setStepMs(+e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-2 text-sm text-gray-300"
          >
            <option value={500}>0.5s</option>
            <option value={1000}>1s</option>
            <option value={2000}>2s</option>
            <option value={5000}>5s</option>
          </select>
        </div>
      </div>

      <hr className="border-gray-700" />

      {/* Invest */}
      <form onSubmit={handleInvest} className="flex gap-2">
        <input
          type="number" placeholder="Amount"
          value={investAmt} onChange={e => setInvestAmt(e.target.value)}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white min-w-0"
        />
        <button type="submit" className="bg-income/20 hover:bg-income/30 text-income border border-income/30 rounded-lg px-3 text-sm font-medium transition-all">
          Invest
        </button>
      </form>

      {/* Reserve & auto-buy */}
      <div className="space-y-2">
        <div className="flex gap-2 items-center">
          <label className="text-sm text-gray-400 w-20 shrink-0">Reserve</label>
          <input
            type="number"
            value={reserveAmt} onChange={e => setReserveAmt(e.target.value)}
            onBlur={handleSettings}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-sm text-white min-w-0"
          />
        </div>
        <div className="flex gap-2 items-center">
          <label className="text-sm text-gray-400 w-20 shrink-0">Auto-buy $</label>
          <input
            type="number" placeholder="off"
            value={autoBuy} onChange={e => setAutoBuy(e.target.value)}
            onBlur={handleSettings}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-sm text-white min-w-0"
          />
        </div>
      </div>

      <div className="text-xs text-gray-500 mt-auto">
        {connected ? '● connected' : '○ reconnecting…'}
      </div>
    </div>
  )
}
