import { useEffect, useRef, useState } from 'react'

let nextId = 0

export function useNotifications() {
  const [notifications, setNotifications] = useState([])

  function add(text, color = 'green') {
    const id = ++nextId
    setNotifications(prev => [...prev, { id, text, color }])
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 2200)
  }

  return { notifications, add }
}

export function FloatingNotifications({ notifications }) {
  return (
    <div className="fixed bottom-6 right-6 flex flex-col-reverse gap-2 pointer-events-none z-50">
      {notifications.map(n => (
        <div
          key={n.id}
          className={`px-4 py-2 rounded-lg font-semibold tabular text-sm shadow-lg animate-bounce-up
            ${n.color === 'green' ? 'bg-income/20 text-income border border-income/30' : 'bg-expense/20 text-expense border border-expense/30'}`}
        >
          {n.text}
        </div>
      ))}
    </div>
  )
}
