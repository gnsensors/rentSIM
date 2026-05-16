# Real Estate Portfolio Simulation Web App — UI & Feature Specification

## 1. Overview
This application is a portfolio-based financial simulation platform. Users manage multiple portfolios containing cash, real estate assets, investments, and loans. Each portfolio is displayed as a vertically stacked card with a three-column internal layout for control, assets, and liabilities.

---

## 2. Global Page Structure

### 2.1 Layout Model
- Vertical list of **Portfolio Cards**
- Each portfolio card is independent and self-contained
- Top-of-page creation controls:
  - Text input: Portfolio name
  - Button: Create portfolio

### 2.2 Interaction Model
- Monthly simulation step system (manual or automated)
- Real-time financial updates per portfolio
- Event-based UI feedback (income, payments, payoff events)

---

## 3. Portfolio Card Architecture

Each portfolio card is divided into three primary columns:


| LEFT: Controls & Stats | CENTER: Houses | RIGHT: Loans |


---

## 4. LEFT COLUMN — Portfolio Controls & Financial Overview

### 4.1 Core Financial Metrics
- Cash balance
- Total asset value (houses + investments)
- Reserve amount (editable numeric input)
- Current invested amount breakdown (visual summary)

### 4.2 Time & Simulation Controls
- “Next Month” button (manual progression)
- Auto-simulation toggle
- Auto-step interval input (time-based execution)
- Life/time remaining indicator (simulation horizon or remaining months)
- “Close Early” button (terminates portfolio simulation)

### 4.3 Investment Controls
- “Invest” action button
- Auto-buy price threshold input:
  - Numeric value or “None”
- Optional: allocation controls for investment distribution

---

## 5. CENTER COLUMN — Houses (Assets)

### 5.1 House List Structure
Each house is displayed as a compact card:

**House Fields**
- Purchase value
- Current monthly rent
- Weighted average rent over time
- House metadata (raw attributes retained but partially hidden or collapsible)

**House Actions**
- Sell button

---

### 5.2 Buying Houses

At the bottom of the house list:
- “Buy House” button

#### Purchase Flow
- Opens modal listing randomly generated available houses:
  - Price
  - Expected rent
  - Basic property stats

#### Constraints
- Down payment fixed at 20%
- Purchase blocked if cash < 20% of price
- Remaining 80% treated as financed liability (implicit system behavior)

---

## 6. RIGHT COLUMN — Loans (Liabilities)

### 6.1 Loan List Ordering
- Loans sorted by total cost (highest → lowest)

### 6.2 Loan Card Structure
Each loan displays:
- Loan amount
- Month originated
- Loan duration (months)
- Required monthly payment
- Average monthly payment
- Estimated payoff month (based on current repayment behavior including extra payments)

---

### 6.3 Loan Repayment Behavior
- Each payment triggers a red floating notification:
  - `-$X,XXX`
- When a loan is fully repaid:
  - Card animates out (fade/collapse)
  - Green confirmation message:
    - `Paid off!`

---

### 6.4 Loan Control Input
At bottom of loan column:
- Repayment rate slider/input:
  - 0% = no repayment
  - 100% = full available repayment allocation

---

## 7. Event Notification System

### 7.1 Income Events
- House rent generates floating green text:
  - `+$X,XXX`

### 7.2 Expense Events
- Loan payments generate floating red text:
  - `-$X,XXX`

### 7.3 Notification Behavior
- Floating popups:
  - Stack briefly without blocking UI
  - Fade out smoothly
  - Position near relevant portfolio card

---

## 8. Styling & Visual Design System

### 8.1 Layout Principles
- Strong separation between functional columns
- Clear hierarchy:
  - Left = control center
  - Center = assets
  - Right = liabilities

### 8.2 Card Design
- Rounded corners (medium radius)
- Subtle shadow elevation
- Soft border or glass-style translucency option
- Consistent spacing using an 8px grid system

### 8.3 Color System
- Income / positive values: green
- Expenses / debt: red
- Neutral UI elements: gray / muted blue
- Primary actions: single accent color (blue or purple recommended)

### 8.4 Typography
- Clean sans-serif (Inter / SF Pro / system UI)
- Tabular numerals for financial alignment
- Clear weight contrast between labels and values

---

## 9. Microinteractions & Animations

- Button hover:
  - slight scale + brightness increase
- Card hover:
  - increased elevation/shadow
- Buying/selling assets:
  - fade + slide animation
- Loan payoff:
  - collapse animation + success highlight
- Income events:
  - upward float + fade
- Payment events:
  - downward fade or pulse red flash

---

## 10. UX Enhancements (Recommended Extensions)

- Portfolio-level performance metrics:
  - ROI
  - cashflow trend
  - debt-to-asset ratio
- House filtering:
  - price range
  - rent yield
- Loan sorting options:
  - interest rate, remaining balance, payoff time
- Timeline chart per portfolio (cash over time)
- Risk indicator per portfolio
- Confirmation modal for high-value transactions

---