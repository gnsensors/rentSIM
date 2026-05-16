import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useSimWebSocket } from '../hooks/useSimWebSocket'
import { FloatingNotifications, useNotifications } from './FloatingNotification'
import HouseList from './HouseList'
import LoanList from './LoanList'
import PortfolioControls from './PortfolioControls'

export default function PortfolioCard({ portfolio, onDelete }) {
  const { token } = useAuth()
  const { state, month, lastEvents, connected, send } = useSimWebSocket(portfolio.id)
  const { notifications, add } = useNotifications()

  // Fire floating notifications from incoming events
  useEffect(() => {
    const ev = lastEvents[lastEvents.length - 1]
    if (!ev) return
    if (ev.type === 'rent_collected')
      add(`+$${Number(ev.amount).toLocaleString()}`, 'green')
    else if (ev.type === 'loan_payment')
      add(`-$${Number(ev.amount).toLocaleString()}`, 'red')
    else if (ev.type === 'loan_paid_off')
      add('Paid off!', 'green')
    else if (ev.type === 'house_sold' && ev.reason !== 'close')
      add(`Sold: $${Number(ev.value).toLocaleString()}`, 'green')
  }, [lastEvents])

  const handleStep        = ()    => send({ action: 'step' })
  const handleInvest      = (amt) => send({ action: 'invest', amount: amt })
  const handleBuy         = (price) => send({ action: 'buy_house', price })
  const handleSell        = (id)  => send({ action: 'sell_house', house_id: id })
  const handleRepayRate   = (r)   => send({ action: 'update_settings', loan_repay_rate: r })
  const handleSettings    = (s)   => send({ action: 'update_settings', ...s })

  return (
    <div className="bg-gray-900 rounded-2xl shadow-xl border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
        <h2 className="font-bold text-lg text-white">{portfolio.name}</h2>
        <button
          onClick={onDelete}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors"
        >
          Delete
        </button>
      </div>

      {/* 3-column body */}
      <div className="grid grid-cols-3 divide-x divide-gray-800 p-6 gap-0">
        <div className="pr-6">
          <PortfolioControls
            state={state}
            month={month}
            connected={connected}
            onStep={handleStep}
            onInvest={handleInvest}
            onUpdateSettings={handleSettings}
          />
        </div>

        <div className="px-6">
          <HouseList
            houses={state?.houses ?? []}
            portfolioId={portfolio.id}
            token={token}
            onSell={handleSell}
            onBuy={handleBuy}
            cash={state?.cash}
            reserved={state?.reserved}
          />
        </div>

        <div className="pl-6">
          <LoanList
            loans={state?.loans ?? []}
            loanRepayRate={state?.loan_repay_rate ?? 1}
            onRepayRateChange={handleRepayRate}
          />
        </div>
      </div>

      <FloatingNotifications notifications={notifications} />
    </div>
  )
}
