import { useEffect, useMemo, useState } from "react"
const API = import.meta.env.VITE_API_URL || "https://fuelflow-mavn.onrender.com"

const money = (value) =>
  `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`

const getDates = (range) => {
  const end = new Date()
  const start = new Date(end)

  if (range === "Today") {
    start.setHours(0, 0, 0, 0)
  } else if (range === "7 Days") {
    start.setDate(start.getDate() - 6)
    start.setHours(0, 0, 0, 0)
  } else {
    start.setDate(start.getDate() - 29)
    start.setHours(0, 0, 0, 0)
  }

  return {
    from: start.toISOString(),
    to: end.toISOString(),
  }
}

const normalise = (p) => ({
  ...p,
  gross_amount: Number(p.gross_amount || 0),
  received_amount: Number(p.received_amount || 0),
  quantity_litres: Number(p.quantity_litres || 0),
  unit_price: Number(p.unit_price || 0),
})

function SalesChart({ rows }) {
  const data = useMemo(() => {
    const grouped = {}

    rows.forEach((p) => {
      if (!p.transaction_time) return

      const d = new Date(p.transaction_time)
      if (Number.isNaN(d.getTime())) return

      const key = d.toISOString().slice(0, 10)

      grouped[key] =
        (grouped[key] || 0) + p.received_amount
    })

    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, amount]) => ({
        date,
        amount,
      }))
  }, [rows])

  if (!data.length) {
    return (
      <div className="fake-chart">
        <div style={{ margin: "auto", color: "#94a3b8" }}>
          No sales data available
        </div>
      </div>
    )
  }

  const max = Math.max(...data.map((x) => x.amount), 1)

  const points = data
    .map((item, index) => {
      const x =
        data.length === 1
          ? 50
          : (index / (data.length - 1)) * 100

      const y = 92 - (item.amount / max) * 78

      return `${x},${y}`
    })
    .join(" ")

  return (
    <div className="fake-chart">
      <div className="chart-y">
        <span>{money(max)}</span>
        <span>{money(max * 0.66)}</span>
        <span>{money(max * 0.33)}</span>
        <span>₹0</span>
      </div>

      <svg
        className="line-chart"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <polyline
          points={points}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  )
}

export default function App() {
  const [rows, setRows] = useState([])
  const [range, setRange] = useState("Today")
  const [search, setSearch] = useState("")
  const [active, setActive] = useState("Dashboard")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [liveConnected, setLiveConnected] = useState(false)
  const [lastLivePayment, setLastLivePayment] = useState(null)

  const loadPayments = async () => {
    try {
      setError("")

      const { from, to } = getDates(range)

      const params = new URLSearchParams({
        from,
        to,
        limit: "50000",
      })

      const response = await fetch(
        `${API}/api/payments?${params}`
      )

      if (!response.ok) {
        throw new Error(`API ${response.status}`)
      }

      const data = await response.json()

      if (!Array.isArray(data.payments)) {
        throw new Error("Invalid API response")
      }

      setRows(data.payments.map(normalise))
    } catch (err) {
      console.error(err)
      setError(
        "Unable to load payment data. Check that FastAPI is running."
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    loadPayments()
  }, [range])

  useEffect(() => {
    const source = new EventSource(
      `${API}/api/payments/stream`
    )

    source.onopen = () => {
      setLiveConnected(true)
    }

    source.onmessage = (event) => {
      try {
        const payment = normalise(
          JSON.parse(event.data)
        )

        setLastLivePayment(payment)

        setRows((current) => {
          const exists = current.some(
            (p) =>
              p.payment_id === payment.payment_id
          )

          if (exists) return current

          return [payment, ...current]
        })
      } catch (err) {
        console.error("SSE error:", err)
      }
    }

    source.onerror = () => {
      setLiveConnected(false)
    }

    return () => source.close()
  }, [])

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()

    if (!q) return rows

    return rows.filter((payment) =>
      Object.values(payment).some((value) =>
        String(value)
          .toLowerCase()
          .includes(q)
      )
    )
  }, [rows, search])

  const totalReceived = rows.reduce(
    (sum, p) => sum + p.received_amount,
    0
  )

  const grossAmount = rows.reduce(
    (sum, p) => sum + p.gross_amount,
    0
  )

  const successful = rows.filter(
    (p) => p.payment_status === "success"
  )

  const pending = rows.filter(
    (p) => p.payment_status === "pending"
  )

  const failed = rows.filter(
    (p) => p.payment_status === "failed"
  )

  const successRate = rows.length
    ? Math.round(
        (successful.length / rows.length) * 100
      )
    : 0

  const methods = [
    "Google Pay",
    "PhonePe",
    "Card",
    "Paytm",
    "Cash",
  ].map((name) => ({
    name,
    amount: rows
      .filter((p) => p.payment_app === name)
      .reduce(
        (sum, p) => sum + p.received_amount,
        0
      ),
  }))

  const methodTotal =
    methods.reduce(
      (sum, x) => sum + x.amount,
      0
    ) || 1

  const pumps = [
    "Pump 1",
    "Pump 2",
    "Pump 3",
    "Pump 4",
  ].map((name) => ({
    name,
    amount: rows
      .filter((p) => p.pump_id === name)
      .reduce(
        (sum, p) => sum + p.received_amount,
        0
      ),
  }))

  const pumpMax = Math.max(
    ...pumps.map((p) => p.amount),
    1
  )

  const exportPayments = () => {
    const { from, to } = getDates(range)

    const params = new URLSearchParams({
      from,
      to,
    })

    window.open(
      `${API}/api/payments/export.csv?${params}`,
      "_blank"
    )
  }

  return (
    <div className="app">

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">₹</div>

          <div>
            <h2>FuelFlow</h2>
            <span>Payment Intelligence</span>
          </div>
        </div>

        <div className="menu-title">
          MAIN MENU
        </div>

        <nav>
          {[
            "Dashboard",
            "Payments",
            "Analytics",
            "Settlements",
          ].map((item) => (
            <button
              key={item}
              className={`menu-item ${
                active === item ? "active" : ""
              }`}
              onClick={() => { setActive(item); const targets = { Dashboard: "dashboard-top", Payments: "payments-section", Analytics: "analytics-section", Settlements: "settlements-section" }; document.getElementById(targets[item])?.scrollIntoView({ behavior: "smooth", block: "start" }) }}
            >
              <span>
                {item === "Dashboard"
                  ? "▦"
                  : item === "Payments"
                    ? "▣"
                    : item === "Analytics"
                      ? "◒"
                      : "✓"}
              </span>

              {item}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <div className="menu-title">
            SYSTEM
          </div>

          <button
            className="menu-item"
            onClick={() => setActive("Settings")}
          >
            <span>⚙</span>
            Settings
          </button>

          <div className="system-status">

            <span
              className={`status-dot ${
                liveConnected ? "" : "offline"
              }`}
            />

            <div>
              <strong>
                {liveConnected
                  ? "System Online"
                  : "Connecting..."}
              </strong>

              <small>
                {liveConnected
                  ? "Live / SSE connected"
                  : "Connecting to live stream"}
              </small>
            </div>

          </div>

        </div>

      </aside>

      <main className="main">

        <header className="topbar">

          <button className="mobile-menu">
            ☰
          </button>

          <div className="search-box">
            <span>⌕</span>

            <input
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
              placeholder="Search payments, pump, reference…"
            />
          </div>

          <div className="top-actions">

            <div
              className={`live-status ${
                liveConnected ? "" : "offline"
              }`}
            >
              <span />
              {liveConnected ? "LIVE" : "OFFLINE"}
            </div>

            <button className="icon-button">
              ♢
              <b />
            </button>

            <div className="profile">

              <div className="avatar">
                KR
              </div>

              <div>
                <strong>Admin</strong>
                <small>Fuel Station</small>
              </div>

            </div>

          </div>

        </header>

        <section className="content" id="dashboard-top">

          <div className="page-heading">

            <div>
              <h1>
                {active === "Dashboard"
                  ? "Payment Dashboard"
                  : active}
              </h1>

              <p>
                Monitor fuel sales, collections
                and settlement exceptions in real time.
              </p>
            </div>

            <div className="date-selector">

              <span>Period</span>

              <select
                value={range}
                onChange={(e) =>
                  setRange(e.target.value)
                }
              >
                <option>Today</option>
                <option>7 Days</option>
                <option>30 Days</option>
              </select>

              <button
                className="small-button"
                onClick={loadPayments}
              >
                ↻ Refresh
              </button>

            </div>

          </div>

          {error && (
            <div
              style={{
                padding: "12px 16px",
                marginBottom: "18px",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                borderRadius: "10px",
              }}
            >
              {error}
            </div>
          )}

          {lastLivePayment && (
            <div
              style={{
                padding: "10px 14px",
                marginBottom: "16px",
                background: "#ecfdf5",
                border: "1px solid #a7f3d0",
                color: "#047857",
                borderRadius: "10px",
                fontSize: "13px",
              }}
            >
              ● Live payment received:{" "}
              <strong>
                {lastLivePayment.payment_app}
              </strong>{" "}
              · {lastLivePayment.pump_id} ·{" "}
              {money(
                lastLivePayment.received_amount
              )}
            </div>
          )}

          <div className="kpi-grid">

            <div className="kpi-card">
              <div className="kpi-top">
                <div className="kpi-icon blue">₹</div>
                <span className="growth positive">
                  LIVE
                </span>
              </div>

              <p>Total Received</p>

              <h2>
                {money(totalReceived)}
              </h2>

              <small>
                Across all payment methods
              </small>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <div className="kpi-icon green">✓</div>
                <span className="growth positive">
                  {successRate}%
                </span>
              </div>

              <p>Successful Payments</p>

              <h2>
                {successful.length}
              </h2>

              <small>
                Transactions completed
              </small>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <div className="kpi-icon orange">◷</div>
                <span className="growth warning">
                  ATTENTION
                </span>
              </div>

              <p>Pending Payments</p>

              <h2>
                {pending.length}
              </h2>

              <small>
                Awaiting settlement
              </small>
            </div>

            <div className="kpi-card">
              <div className="kpi-top">
                <div className="kpi-icon red">!</div>
                <span className="growth danger">
                  CHECK
                </span>
              </div>

              <p>Failed Payments</p>

              <h2>
                {failed.length}
              </h2>

              <small>
                Require investigation
              </small>
            </div>

          </div>

          <div className="dashboard-grid" id="analytics-section">

            <div className="panel">

              <div className="panel-header">

                <div>
                  <h3>Daily Sales</h3>
                  <p>
                    Received amount · {range}
                  </p>
                </div>

                <button
                  className="small-button"
                  onClick={exportPayments}
                >
                  Export
                </button>

              </div>

              <SalesChart rows={rows} />

            </div>

            <div className="panel">

              <div className="panel-header">

                <div>
                  <h3>
                    Sales by Payment App
                  </h3>

                  <p>
                    Collection distribution
                  </p>
                </div>

              </div>

              <div className="payment-methods">

                {methods.map((method, index) => (
                  <div key={method.name}>

                    <div className="method">

                      <div className="method-left">

                        <span
                          className={`method-circle ${
                            [
                              "google",
                              "phone",
                              "card",
                              "paytm",
                              "cash",
                            ][index]
                          }`}
                        >
                          {method.name[0]}
                        </span>

                        <span>
                          {method.name}
                        </span>

                      </div>

                      <strong>
                        {money(method.amount)}
                      </strong>

                    </div>

                    <div className="progress">

                      <div
                        style={{
                          width: `${
                            (method.amount /
                              methodTotal) *
                            100
                          }%`,
                        }}
                      />

                    </div>

                  </div>
                ))}

              </div>

            </div>

          </div>

          <div className="dashboard-grid" id="analytics-section">

            <div className="panel">

              <div className="panel-header">

                <div>
                  <h3>Sales by Pump</h3>

                  <p>
                    Performance comparison
                  </p>
                </div>

              </div>

              <div className="pump-list">

                {pumps.map((pump) => (
                  <div
                    className="pump-row"
                    key={pump.name}
                  >

                    <span>{pump.name}</span>

                    <div className="pump-bar">
                      <div
                        style={{
                          width: `${
                            (pump.amount /
                              pumpMax) *
                            100
                          }%`,
                        }}
                      />
                    </div>

                    <strong>
                      {money(pump.amount)}
                    </strong>

                  </div>
                ))}

              </div>

            </div>

            <div className="panel">

              <div className="panel-header">

                <div>
                  <h3 id="settlements-section">Settlement Health</h3>

                  <p>
                    Gross vs received
                  </p>
                </div>

              </div>

              <div className="payment-methods">

                <div className="method">
                  <span>Gross Amount</span>
                  <strong>
                    {money(grossAmount)}
                  </strong>
                </div>

                <div className="method">
                  <span>Received Amount</span>
                  <strong>
                    {money(totalReceived)}
                  </strong>
                </div>

                <div className="method">
                  <span>Settlement Gap</span>
                  <strong>
                    {money(
                      grossAmount -
                      totalReceived
                    )}
                  </strong>
                </div>

                <div className="method">
                  <span>Live Status</span>
                  <strong>
                    {liveConnected
                      ? "LIVE"
                      : "OFFLINE"}
                  </strong>
                </div>

              </div>

            </div>

          </div>

          <div className="panel transactions-panel" id="payments-section">

            <div className="panel-header">

              <div>
                <h3>
                  Recent Payment History
                </h3>

                <p>
                  Live transaction records ·{" "}
                  {filtered.length} shown
                </p>
              </div>

              <button
                className="view-all"
                onClick={() => setSearch("")}
              >
                View all →
              </button>

            </div>

            <div className="table-wrapper">

              <table>

                <thead>

                  <tr>
                    <th>TIME</th>
                    <th>PAYMENT ID</th>
                    <th>PUMP</th>
                    <th>METHOD</th>
                    <th>GROSS</th>
                    <th>RECEIVED</th>
                    <th>STATUS</th>
                    <th>EXCEPTION</th>
                  </tr>

                </thead>

                <tbody>

                  {filtered
                    .slice(0, 12)
                    .map((payment) => (
                      <tr
                        key={
                          payment.payment_id
                        }
                      >

                        <td>
                          {String(
                            payment.transaction_time
                          )
                            .replace(
                              "T",
                              " "
                            )
                            .slice(0, 19)}
                        </td>

                        <td className="payment-id">
                          {payment.external_reference ||
                            payment.payment_id}
                        </td>

                        <td>
                          {payment.pump_id}
                        </td>

                        <td>
                          {payment.payment_app}
                        </td>

                        <td className="amount">
                          {money(
                            payment.gross_amount
                          )}
                        </td>

                        <td className="amount">
                          {money(
                            payment.received_amount
                          )}
                        </td>

                        <td>
                          <span
                            className={`status ${payment.payment_status}`}
                          >
                            {payment.payment_status}
                          </span>
                        </td>

                        <td>
                          {payment.exception_reason ||
                            (payment.payment_status ===
                            "success"
                              ? "Normal"
                              : "Requires review")}
                        </td>

                      </tr>
                    ))}

                </tbody>

              </table>

            </div>

          </div>

        </section>

      </main>

    </div>
  )
}





