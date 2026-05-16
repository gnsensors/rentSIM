const fmt = (n) => '$' + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })

function LoanCard({ loan }) {
  const pctPaid = ((loan.original - loan.amount) / loan.original * 100).toFixed(0)

  return (
    <div className="bg-gray-800 rounded-xl p-4 space-y-2 border border-gray-700">
      <div className="flex justify-between items-start">
        <span className="text-xs text-gray-400 font-medium">Loan #{loan.id}</span>
        <span className="text-xs text-gray-400">{(loan.rate * 100).toFixed(1)}% — {loan.years}yr</span>
      </div>

      <div className="flex justify-between">
        <span className="text-sm text-gray-300">Balance</span>
        <span className="tabular font-semibold text-expense">{fmt(loan.amount)}</span>
      </div>

      <div className="w-full bg-gray-700 rounded-full h-1.5">
        <div className="bg-income h-1.5 rounded-full transition-all" style={{ width: `${pctPaid}%` }} />
      </div>

      <div className="flex justify-between text-xs text-gray-400">
        <span>Original: {fmt(loan.original)}</span>
        <span>{pctPaid}% paid</span>
      </div>

      <div className="flex justify-between">
        <span className="text-sm text-gray-300">Monthly payment</span>
        <span className="tabular text-sm">{fmt(loan.monthly_payment)}</span>
      </div>
    </div>
  )
}

export default function LoanList({ loans = [], loanRepayRate, onRepayRateChange }) {
  const total = loans.reduce((s, l) => s + l.amount, 0)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-200">Loans</h3>
        {loans.length > 0 && (
          <span className="text-xs text-expense tabular">{fmt(total)} total</span>
        )}
      </div>

      {loans.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-8">No active loans</p>
      )}

      <div className="space-y-3">
        {[...loans].sort((a, b) => b.amount - a.amount).map(l => (
          <LoanCard key={l.id} loan={l} />
        ))}
      </div>

      <div className="mt-auto pt-4 border-t border-gray-800">
        <div className="flex justify-between items-center mb-1">
          <label className="text-sm text-gray-300">Extra repayment</label>
          <span className="text-sm tabular text-accent">{Math.round(loanRepayRate * 100)}%</span>
        </div>
        <input
          type="range" min="0" max="1" step="0.05"
          value={loanRepayRate}
          onChange={e => onRepayRateChange(parseFloat(e.target.value))}
          className="w-full accent-indigo-500"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0%</span><span>100%</span>
        </div>
      </div>
    </div>
  )
}
