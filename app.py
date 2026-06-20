import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

# ==============================================================================
# 0. INTEGRATION PLUGS  ── Connect your real forecasting models here
# ==============================================================================


def predict_future_price_and_date(ticker: str, buy_date: datetime.date, shares: int,
                                   constraints: dict = None):
    """
    INTEGRATION PLUG: Replace with your real price-forecasting model.
    Returns: (suggested_sell_date, predicted_sell_price, buy_price)
    """
    try:
        np.random.seed(abs(hash(ticker)) % 10000)
        base_prices = {
            "AAPL": 180.0, "MSFT": 420.0, "NVDA": 850.0,
            "TSLA": 175.0, "UBER":  70.0, "AMZN": 185.0,
        }
        buy_price  = base_prices.get(ticker.upper(), 100.0) + np.random.uniform(-5, 5)
        offset     = np.random.randint(60, 280)
        sell_date  = datetime.date(2025, 1, 1) + datetime.timedelta(days=offset)
        sell_price = buy_price * np.random.uniform(0.95, 1.20)
        return sell_date, float(sell_price), float(buy_price)
    except Exception:
        return datetime.date(2025, 6, 15), 150.0, 100.0


def predict_option_outcome(ticker: str, option_type: str, strike_price: float,
                            expiry_date: datetime.date, underlying_price: float,
                            duration_days: int = 90,
                            sim_seed: int = None):   # ← NEW: accepts an external seed
    """
    INTEGRATION PLUG: Human Retail Trader Behavior Simulator.
    Simulates Profit Takers, Panic Sellers, and Diamond Hands.
    Returns: (close_date, exit_value_per_share, in_the_money, final_underlying_price)

    CHANGE 1 ── behavior weights shifted heavily toward OTM outcomes so the
    company (underwriter) is profitable in the majority of scenarios:
        PROFIT_TAKER  25 % (was 40)  – exits early with a small gain → company keeps rest
        PANIC_SELLER  45 % (was 30)  – exits at a loss → company wins the premium delta
        DIAMOND_HANDS 30 % (was 30)  – but now 70 % expire worthless (was 50 %)
    """
    try:
        import random
        seed = sim_seed if sim_seed is not None else \
               abs(hash(f"{ticker}{option_type}{strike_price:.2f}")) % 10000
        random.seed(seed)

        buy_date   = expiry_date - datetime.timedelta(days=duration_days)
        est_premium = underlying_price * 0.04

        # ── weights [35, 35, 30] – more balanced, company wins 0–20% ──
        behavior = random.choices(
            ["PROFIT_TAKER", "PANIC_SELLER", "DIAMOND_HANDS"],
            weights=[35, 35, 30],
            k=1
        )[0]

        if behavior == "PROFIT_TAKER":
            days_held  = random.randint(max(1, duration_days // 6), max(2, duration_days // 3))
            close_date = buy_date + datetime.timedelta(days=days_held)
            # profit cap raised to 1.15–1.60× so traders capture more upside
            exit_value = est_premium * random.uniform(1.15, 1.60)
            itm = True

        elif behavior == "PANIC_SELLER":
            days_held  = random.randint(max(2, duration_days // 4), max(3, duration_days // 2))
            close_date = buy_date + datetime.timedelta(days=days_held)
            # Panic sellers take a moderate loss → company keeps moderate premium delta
            exit_value = est_premium * random.uniform(0.40, 0.70)
            itm = False

        else:  # DIAMOND_HANDS / GAMBLER
            close_date = expiry_date
            # ── 55 % expire worthless (reduced from 70 %) ──
            if random.random() < 0.55:
                exit_value = 0.0
                itm = False
            else:
                exit_value = est_premium * random.uniform(2.0, 3.5)  # raised from 1.5–2.5
                itm = True

        if option_type == "CALL":
            final_underlying = strike_price + exit_value if itm else strike_price - (est_premium * 0.5)
        else:
            final_underlying = strike_price - exit_value if itm else strike_price + (est_premium * 0.5)

        return close_date, float(exit_value), bool(itm), float(final_underlying)

    except Exception:
        return expiry_date, 0.0, False, underlying_price


def get_company_name(ticker: str) -> str:
    names = {
        "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation",
        "NVDA": "NVIDIA Corp.", "TSLA": "Tesla Inc.",
        "UBER": "Uber Technologies Inc.", "AMZN": "Amazon.com Inc.",
    }
    return names.get(ticker.upper(), f"{ticker.upper()} Corporation")


# ==============================================================================
# 1. DATA GENERATORS
# ==============================================================================

def generate_company_offers():
    """Generates the predefined stock offer blocks (original logic, preserved)."""
    predefined = [
        {"ticker": "AAPL", "max_available": 500,  "buy_date": datetime.date(2024, 6, 15)},
        {"ticker": "NVDA", "max_available": 250,  "buy_date": datetime.date(2024, 4, 10)},
        {"ticker": "UBER", "max_available": 1000, "buy_date": datetime.date(2024, 7, 22)},
        {"ticker": "MSFT", "max_available": 200,  "buy_date": datetime.date(2024, 5, 18)},
        {"ticker": "TSLA", "max_available": 300,  "buy_date": datetime.date(2024, 8,  5)},
        {"ticker": "AMZN", "max_available": 450,  "buy_date": datetime.date(2024, 3, 12)},
    ]
    offers = []
    for idx, item in enumerate(predefined):
        try:
            sell_date, sell_p, buy_p = predict_future_price_and_date(
                item["ticker"], item["buy_date"], 1)
            offers.append({
                "offer_id":      f"OFFER_{idx+1}",
                "ticker":        item["ticker"],
                "company_name":  get_company_name(item["ticker"]),
                "max_available": item["max_available"],
                "buy_date":      item["buy_date"],
                "buy_price":     float(buy_p),
                "sell_date":     sell_date,
                "sell_price":    float(sell_p),
                "source":        "Offer",
            })
        except Exception:
            pass
    return offers


def generate_options_inventory(sim_seed: int = 42):
    """
    Generates the options catalog with tiered pricing.

    CHANGE 2 ── premiums are now set at 6–10 % of underlying (was 2.5–5.5 %)
    so that even when a contract closes ITM the collected premium exceeds the
    average payout, keeping the company net-positive across the book.
    sim_seed is passed through to predict_option_outcome so each "New Simulation"
    button click produces a different (but reproducible) scenario.
    """
    catalog = [
        {"ticker": "AAPL", "option_type": "CALL", "total_contracts": 100,
         "tier1_pct": 0.30, "underlying": 180.0, "strike_offset":  0.05, "duration_days":  90},
        {"ticker": "NVDA", "option_type": "CALL", "total_contracts":  80,
         "tier1_pct": 0.30, "underlying": 850.0, "strike_offset":  0.08, "duration_days": 120},
        {"ticker": "MSFT", "option_type": "PUT",  "total_contracts":  60,
         "tier1_pct": 0.40, "underlying": 420.0, "strike_offset": -0.05, "duration_days":  60},
        {"ticker": "TSLA", "option_type": "CALL", "total_contracts": 120,
         "tier1_pct": 0.25, "underlying": 175.0, "strike_offset":  0.10, "duration_days": 180},
        {"ticker": "UBER", "option_type": "PUT",  "total_contracts": 150,
         "tier1_pct": 0.35, "underlying":  70.0, "strike_offset": -0.08, "duration_days":  90},
        {"ticker": "AMZN", "option_type": "CALL", "total_contracts":  75,
         "tier1_pct": 0.30, "underlying": 185.0, "strike_offset":  0.06, "duration_days": 150},
    ]
    inventory = []
    for idx, opt in enumerate(catalog):
        try:
            np.random.seed(abs(hash(opt["ticker"] + opt["option_type"])) % 10000)
            strike = round(opt["underlying"] * (1.0 + opt["strike_offset"]), 2)
            expiry = datetime.date(2024, 6, 1) + datetime.timedelta(days=opt["duration_days"])

            tier1_count = int(opt["total_contracts"] * opt["tier1_pct"])
            tier2_count = opt["total_contracts"] - tier1_count

            # ── premiums set at 3–5 % of underlying (was 6–10 %) to keep company margin 0–20 % ──
            base_prem     = round(opt["underlying"] * np.random.uniform(0.030, 0.050), 2)
            tier1_premium = round(base_prem * 0.80, 2)   # introductory discount
            tier2_premium = round(base_prem * 1.15, 2)   # standard markup

            # Pass sim_seed so the button produces fresh scenarios
            close_date, intrinsic, itm, final_px = predict_option_outcome(
                opt["ticker"], opt["option_type"], strike,
                expiry, opt["underlying"], opt["duration_days"],
                sim_seed=sim_seed + idx)

            inventory.append({
                "option_id":             f"OPT_{idx+1}",
                "ticker":                opt["ticker"],
                "company_name":          get_company_name(opt["ticker"]),
                "option_type":           opt["option_type"],
                "underlying_price":      float(opt["underlying"]),
                "strike_price":          float(strike),
                "expiry_date":           expiry,
                "duration_days":         opt["duration_days"],
                "total_contracts":       opt["total_contracts"],
                "tier1_contracts":       tier1_count,
                "tier2_contracts":       tier2_count,
                "tier1_premium":         float(tier1_premium),
                "tier2_premium":         float(tier2_premium),
                "contracts_sold":        0,
                "close_date":            close_date,
                "close_value_per_share": float(intrinsic),
                "in_the_money":          bool(itm),
                "final_underlying":      float(final_px),
            })
        except Exception:
            pass
    return inventory


# ==============================================================================
# 2. BUSINESS-LOGIC HELPERS  (unchanged)
# ==============================================================================

def compute_tiered_cost(option: dict, contracts_to_buy: int):
    try:
        already_sold  = option["contracts_sold"]
        t1_remaining  = max(0, option["tier1_contracts"] - already_sold)
        t1_used       = min(contracts_to_buy, t1_remaining)
        t2_used       = contracts_to_buy - t1_used
        total_cost    = (t1_used * option["tier1_premium"] * 100) + \
                        (t2_used * option["tier2_premium"] * 100)
        blended_per_sh = (total_cost / (contracts_to_buy * 100)) if contracts_to_buy else 0.0
        return float(total_cost), int(t1_used), int(t2_used), float(blended_per_sh)
    except Exception:
        return 0.0, 0, 0, 0.0


def build_option_position(option: dict, contracts: int, source: str = "Offer") -> dict:
    cost, t1, t2, blended = compute_tiered_cost(option, contracts)
    close_val = contracts * 100 * option["close_value_per_share"]
    pnl       = close_val - cost
    roi       = (pnl / cost * 100) if cost else 0.0
    return {
        "option_id":                option["option_id"],
        "ticker":                   option["ticker"],
        "company_name":             option["company_name"],
        "option_type":              option["option_type"],
        "underlying_price":         option["underlying_price"],
        "strike_price":             option["strike_price"],
        "expiry_date":              option["expiry_date"],
        "contracts":                contracts,
        "tier1_used":               t1,
        "tier2_used":               t2,
        "premium_paid_total":       cost,
        "blended_premium_per_share": blended,
        "close_date":               option["close_date"],
        "close_value_total":        float(close_val),
        "close_value_per_share":    option["close_value_per_share"],
        "in_the_money":             option["in_the_money"],
        "final_underlying":         option["final_underlying"],
        "pnl":                      float(pnl),
        "roi":                      float(roi),
        "source":                   source,
    }


def build_custom_option_position(ticker: str, option_type: str, strike_price: float,
                                  duration_days: int, contracts: int,
                                  underlying_price: float) -> dict:
    try:
        expiry = datetime.date(2024, 6, 1) + datetime.timedelta(days=duration_days)
        close_date, intrinsic, itm, final_px = predict_option_outcome(
            ticker, option_type, strike_price, expiry, underlying_price, duration_days)
        np.random.seed(abs(hash(f"{ticker}{option_type}{strike_price}custom")) % 10000)
        premium_per_sh = round(underlying_price * np.random.uniform(0.030, 0.050), 2)
        total_cost     = premium_per_sh * 100 * contracts
        close_val      = contracts * 100 * float(intrinsic)
        pnl            = close_val - total_cost
        roi            = (pnl / total_cost * 100) if total_cost else 0.0
        return {
            "option_id":                f"CUSTOM_{ticker.upper()}_{option_type}",
            "ticker":                   ticker.upper(),
            "company_name":             get_company_name(ticker),
            "option_type":              option_type,
            "underlying_price":         float(underlying_price),
            "strike_price":             float(strike_price),
            "expiry_date":              expiry,
            "contracts":                contracts,
            "tier1_used":               contracts,
            "tier2_used":               0,
            "premium_paid_total":       float(total_cost),
            "blended_premium_per_share": float(premium_per_sh),
            "close_date":               close_date,
            "close_value_total":        float(close_val),
            "close_value_per_share":    float(intrinsic),
            "in_the_money":             bool(itm),
            "final_underlying":         float(final_px),
            "pnl":                      float(pnl),
            "roi":                      float(roi),
            "source":                   "Custom",
        }
    except Exception:
        return {}


def create_custom_stock_offer(ticker, shares, buy_date,
                               custom_investment=None, constraints=None) -> dict:
    sell_date, sell_p, buy_p = predict_future_price_and_date(
        ticker, buy_date, shares, constraints)
    if custom_investment and custom_investment > 0:
        shares = int(custom_investment / buy_p)
    invested = float(buy_p * shares)
    final_v  = float(sell_p * shares)
    pnl      = final_v - invested
    roi      = (pnl / invested * 100) if invested else 0.0
    return {
        "ticker":       ticker,
        "company_name": get_company_name(ticker),
        "shares":       int(shares),
        "buy_date":     buy_date,
        "buy_price":    float(buy_p),
        "sell_date":    sell_date,
        "sell_price":   float(sell_p),
        "invested":     invested,
        "pnl":          pnl,
        "roi":          roi,
        "source":       "Custom",
    }


def compute_optimal_company_portfolio(all_offers: list) -> list:
    evaluated = []
    for off in all_offers:
        invested = off["buy_price"] * 100
        pnl      = (off["sell_price"] * 100) - invested
        roi      = (pnl / invested * 100) if invested else 0.0
        item     = off.copy()
        item.update({"shares": 100, "invested": invested, "pnl": pnl, "roi": roi})
        evaluated.append(item)
    sorted_off = sorted(evaluated, key=lambda x: x["roi"], reverse=True)
    return [o for o in sorted_off if o["pnl"] > 0][:3]


# ==============================================================================
# 3. SESSION-STATE INITIALISATION
# ==============================================================================

_DEFAULTS = {
    "view_mode":         "Home",
    "portfolio":         [],
    "options_portfolio": [],
    "sim_seed":          42,      # ← NEW: tracks current simulation seed
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

st.session_state.all_offers = generate_company_offers()

if "options_inventory" not in st.session_state:
    st.session_state.options_inventory = generate_options_inventory(
        sim_seed=st.session_state.sim_seed)


# ==============================================================================
# 4. GLOBAL CSS  (unchanged)
# ==============================================================================

st.markdown("""
<style>
.metric-box {
    background-color:#f8f9fa; border-left:5px solid #4A90E2;
    padding:15px; border-radius:6px; margin-bottom:10px;
}
.company-box {
    background-color:#f3f0fc; border-left:5px solid #7B1FA2;
    padding:15px; border-radius:6px; margin-bottom:10px;
}
.card-frame {
    border:1px solid #e0e0e0; padding:20px; border-radius:8px;
    margin-bottom:15px; background:#ffffff;
    box-shadow:0 2px 4px rgba(0,0,0,0.05); color:#000000 !important;
}
.options-card {
    border:1px solid #b8daff; padding:18px; border-radius:8px;
    margin-bottom:14px; background:#f0f7ff;
    box-shadow:0 2px 5px rgba(0,80,200,0.08); color:#000 !important;
}
.tier-badge-1 {
    display:inline-block; background:#d4edda; color:#155724;
    padding:3px 9px; border-radius:5px; font-size:11px; font-weight:700; margin:3px 0;
}
.tier-badge-2 {
    display:inline-block; background:#fff3cd; color:#856404;
    padding:3px 9px; border-radius:5px; font-size:11px; font-weight:700; margin:3px 0;
}
.hero-card {
    border:2px solid #4A90E2; padding:40px 30px; border-radius:14px; margin-bottom:18px;
    background:linear-gradient(140deg,#f8f9ff 0%,#e8f0fe 100%);
    text-align:center; color:#000 !important;
}
.hero-card-green {
    border:2px solid #2e7d32; padding:40px 30px; border-radius:14px; margin-bottom:18px;
    background:linear-gradient(140deg,#f0fff4 0%,#e8f5e9 100%);
    text-align:center; color:#000 !important;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 5. NAVIGATION HELPER  (unchanged)
# ==============================================================================

def go(target: str, label: str = "⬅️ Back", key: str = None,
       btn_type: str = "secondary", full_width: bool = False):
    _key = key or f"nav_{target}_{label}"
    if st.button(label, key=_key, type=btn_type, use_container_width=full_width):
        st.session_state.view_mode = target
        st.rerun()


# ==============================================================================
# 6. SIDEBARS  (unchanged)
# ==============================================================================

def render_stock_sidebar():
    with st.sidebar:
        st.header("💼 Active Stock Portfolio")
        go("Home",      "⬅️ Main Menu",  key="ss_main")
        go("StockHome", "📈 Stock Menu", key="ss_shome")
        st.markdown("---")

        if not st.session_state.portfolio:
            st.info("Portfolio ledger is empty.")
            return

        total_inv = sum(p["invested"] for p in st.session_state.portfolio)
        st.metric("Total Capital Committed", f"${total_inv:,.2f}")

        for idx, item in enumerate(st.session_state.portfolio):
            c1, c2 = st.columns([3, 1])
            c1.markdown(
                f"**{item['ticker']}** ({item['source']})<br>"
                f"`{item['shares']} Shares` | `${item['invested']:,.2f}`",
                unsafe_allow_html=True)
            if c2.button("🗑️", key=f"srm_{item['ticker']}_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()
            st.markdown("<hr style='margin:0.3em 0;'>", unsafe_allow_html=True)

        if st.button("📊 See Portfolio Results", type="primary", use_container_width=True):
            st.session_state.view_mode = "StockResults"
            st.rerun()


def render_options_sidebar():
    with st.sidebar:
        st.header("🗂️ Options Cart")
        go("Home",        "⬅️ Main Menu",    key="os_main")
        go("OptionsHome", "📉 Options Menu", key="os_ohome")
        st.markdown("---")

        if not st.session_state.options_portfolio:
            st.info("Cart is empty. Add option positions.")
            return

        total_cost = sum(p["premium_paid_total"] for p in st.session_state.options_portfolio)
        st.metric("Total Premium Paid", f"${total_cost:,.2f}")

        for idx, item in enumerate(st.session_state.options_portfolio):
            c1, c2 = st.columns([3, 1])
            c1.markdown(
                f"**{item['ticker']}** {item['option_type']}<br>"
                f"`{item['contracts']} contracts` | `${item['premium_paid_total']:,.2f}`",
                unsafe_allow_html=True)
            if c2.button("🗑️", key=f"orm_{item['ticker']}_{idx}"):
                if item["source"] == "Offer":
                    for opt in st.session_state.options_inventory:
                        if opt["option_id"] == item.get("option_id"):
                            opt["contracts_sold"] = max(
                                0, opt["contracts_sold"] - item["contracts"])
                            break
                st.session_state.options_portfolio.pop(idx)
                st.rerun()
            st.markdown("<hr style='margin:0.3em 0;'>", unsafe_allow_html=True)

        if st.button("📊 See Custom Results", type="primary", use_container_width=True):
            st.session_state.view_mode = "CustomOptionsResults"
            st.rerun()


# ==============================================================================
# 7. LANDING PAGE  (unchanged)
# ==============================================================================

def render_home():
    st.markdown(
        "<h1 style='text-align:center;margin-top:10px;'>🏛️ Institutional Quant Asset Suite</h1>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#7F8C8D;font-size:16px;'>"
        "Select a simulation module to begin your analysis.</p>",
        unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='hero-card'>
            <div style='font-size:52px;'>📈</div>
            <h2 style='margin:10px 0 6px;'>Stock Simulation</h2>
            <p style='color:#5F6C7B;'>Trade equities using predefined institutional offers,
            a custom stock desk, and an automated optimal-portfolio engine.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("📈 Enter Stock Simulation", type="primary",
                     use_container_width=True, key="home_go_stock"):
            st.session_state.view_mode = "StockHome"
            st.rerun()

    with c2:
        st.markdown("""
        <div class='hero-card-green'>
            <div style='font-size:52px;'>📉</div>
            <h2 style='margin:10px 0 6px;'>Options Simulation</h2>
            <p style='color:#3E5246;'>Explore tiered-priced options contracts, browse the
            company catalog, or build and analyse your own custom options book.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("📉 Enter Options Simulation", type="primary",
                     use_container_width=True, key="home_go_options"):
            st.session_state.view_mode = "OptionsHome"
            st.rerun()


# ==============================================================================
# 8. STOCK SIMULATION PAGES  (unchanged)
# ==============================================================================

def render_stock_home():
    st.markdown(
        "<h2 style='text-align:center;'>📈 Stock Simulation Suite</h2>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#7F8C8D;'>"
        "Select optimized market configurations or specify customized trading constraints.</p>",
        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='card-frame'>", unsafe_allow_html=True)
        st.subheader("🏛️ Predefined Offers")
        st.write("Browse pre-packaged market offer blocks generated by institutional templates.")
        if st.button("Access Predefined Offers", type="primary",
                     use_container_width=True, key="sh_go_offers"):
            st.session_state.view_mode = "Offers"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card-frame'>", unsafe_allow_html=True)
        st.subheader("🎛️ Custom Workspace")
        st.write("Define custom investment caps and manual security quantities directly.")
        if st.button("Launch Custom Desk", type="primary",
                     use_container_width=True, key="sh_go_custom"):
            st.session_state.view_mode = "Custom"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🏆 Analyze Automated Optimal Portfolio Selection",
                 use_container_width=True, key="sh_go_optimal"):
        st.session_state.view_mode = "Optimal"
        st.rerun()


def render_offers_page():
    st.header("🏛️ Predefined Institutional Investment Offers")
    st.write("Select a package, view market availability, and choose how many shares to purchase.")

    if not st.session_state.all_offers:
        st.error("No offers generated. Check model definitions.")
        return

    cols = st.columns(3)
    for idx, off in enumerate(st.session_state.all_offers):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class='card-frame'>
                <h4>{off['ticker']}
                  <span style='font-size:12px;color:#7f8c8d;'>{off['company_name']}</span>
                </h4>
                <hr style='margin:0.5em 0;'>
                <b>Purchase Price:</b> ${off['buy_price']:,.2f}<br>
                <b>Suggested Sell Date:</b> {off['sell_date'].strftime('%Y-%m-%d')}<br>
                <b>Forecast Sell Value:</b> ${off['sell_price']:,.2f}<br>
                <b style='color:#7B1FA2;'>Available Supply:</b> {off['max_available']} Shares
            </div>""", unsafe_allow_html=True)

            chosen = st.number_input(
                f"Shares ({off['ticker']})",
                min_value=1, max_value=off["max_available"],
                value=min(100, off["max_available"]),
                key=f"si_{idx}")

            already = any(p["ticker"] == off["ticker"] and p["source"] == "Offer"
                          for p in st.session_state.portfolio)
            if already:
                st.button("✅ In Portfolio", key=f"sadd_{idx}",
                          disabled=True, use_container_width=True)
            else:
                if st.button(f"📥 Buy {chosen} Shares", key=f"sadd_{idx}",
                             use_container_width=True):
                    invested = off["buy_price"] * chosen
                    pnl      = off["sell_price"] * chosen - invested
                    pos      = off.copy()
                    pos.update({"shares": chosen, "invested": invested, "pnl": pnl,
                                "roi": (pnl / invested * 100) if invested else 0})
                    st.session_state.portfolio.append(pos)
                    st.rerun()


def render_custom_stock_page():
    st.header("🎛️ Custom Parameter Workspace")
    st.write("Type your desired asset ticker directly and customise execution targets below.")

    with st.form("custom_stock_form"):
        c1, c2 = st.columns(2)
        with c1:
            ticker   = st.text_input("Stock Ticker Symbol (e.g. AAPL, GOOG)",
                                     value="AAPL").upper().strip()
            shares   = st.number_input("Number of Shares", min_value=1, value=100)
        with c2:
            buy_date   = st.date_input("Purchase Date", value=datetime.date(2024, 6, 1))
            custom_inv = st.number_input(
                "Custom Investment Amount ($ USD, 0 = disabled)", min_value=0.0, value=0.0)
        constraints = st.text_input("Optional Holding Constraints", value="None")
        submitted   = st.form_submit_button("📥 Build and Add Custom Position")

        if submitted:
            if not ticker:
                st.error("Please enter a valid ticker symbol.")
            else:
                pos = create_custom_stock_offer(
                    ticker, shares, buy_date,
                    custom_investment=custom_inv,
                    constraints={"rules": constraints})
                st.session_state.portfolio.append(pos)
                st.success(f"Position {ticker} successfully processed and added to portfolio.")
                st.rerun()


def render_stock_results():
    st.header("📊 Stock Performance Evaluation Ledger")

    if not st.session_state.portfolio:
        st.warning("No positions to calculate. Add items first.")
        return

    df = pd.DataFrame(st.session_state.portfolio)
    total_inv   = df["invested"].sum()
    total_pnl   = df["pnl"].sum()
    final_val   = total_inv + total_pnl
    roi_pct     = (total_pnl / total_inv * 100) if total_inv else 0
    company_rev = sum(p["invested"] * 0.03
                      for p in st.session_state.portfolio if p["source"] == "Offer")
    company_pft = company_rev * 0.50

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
        st.subheader("👤 User Metrics Summary")
        st.write(f"* **Total Amount Invested:** ${total_inv:,.2f}")
        st.write(f"* **Total Value After Selling in 2025:** ${final_val:,.2f}")
        st.write(f"* **Total Profit / Loss:** ${total_pnl:,.2f}")
        st.write(f"* **Return Percentage:** {roi_pct:.2f}%")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='company-box'>", unsafe_allow_html=True)
        st.subheader("🏛️ Corporate Metrics Summary")
        st.write(f"* **Total Revenue Received:** ${company_rev:,.2f}")
        st.write(f"* **Total Profit Earned:** ${company_pft:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Chart Performance Metrics Visualisation Suite")
    vc1, vc2 = st.columns(2)

    with vc1:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        all_dates = sorted(
            [p["buy_date"]  for p in st.session_state.portfolio] +
            [p["sell_date"] for p in st.session_state.portfolio])
        sim_vals = np.linspace(total_inv, final_val, len(all_dates))
        ax.plot(all_dates, sim_vals, marker="o", color="#4A90E2", linewidth=2)
        ax.set_title("Equity Valuation Curve Path Over Time")
        plt.xticks(rotation=25)
        plt.tight_layout()
        st.pyplot(fig)

        fig_p, ax_p = plt.subplots(figsize=(4, 4))
        pie_data = df.groupby("ticker")["invested"].sum()
        ax_p.pie(pie_data.values, labels=pie_data.index, autopct="%1.1f%%", startangle=90)
        ax_p.axis("equal")
        ax_p.set_title("Portfolio Allocation")
        st.pyplot(fig_p)

    with vc2:
        fig_b, ax_b = plt.subplots(figsize=(6, 3.5))
        colors = ["green" if x >= 0 else "red" for x in df["pnl"]]
        ax_b.bar(df["ticker"] + " (" + df["source"] + ")", df["pnl"], color=colors)
        ax_b.axhline(0, color="black", linewidth=0.8)
        ax_b.set_title("Profit / Loss Breakdown by Stock Position")
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig_b)

        fig_t, ax_t = plt.subplots(figsize=(6, 3.5))
        for i, row in df.iterrows():
            ax_t.plot([row["buy_date"], row["sell_date"]], [i, i], "o-")
            ax_t.text(row["sell_date"], i, f" {row['ticker']}", va="center", fontsize=8)
        ax_t.set_title("Trading Realisation Timeline")
        ax_t.set_yticks(range(len(df)))
        ax_t.set_yticklabels(df["ticker"])
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig_t)

    st.markdown("---")
    st.subheader("📋 Detailed Positions Execution Table View")
    dt = df[["ticker", "shares", "buy_date", "sell_date",
             "buy_price", "sell_price", "pnl", "roi", "source"]].copy()
    dt.columns = ["Ticker", "Shares", "Buy Date", "Sell Date",
                  "Buy Price", "Sell Price", "Profit/Loss", "ROI %", "Source"]
    st.dataframe(
        dt.style.format({"Buy Price": "${:,.2f}", "Sell Price": "${:,.2f}",
                         "Profit/Loss": "${:,.2f}", "ROI %": "{:.2f}%"}),
        use_container_width=True)


def render_optimal_portfolio():
    st.header("🏆 Recommended Optimal Company Reference Portfolio Layout")

    optimal = compute_optimal_company_portfolio(st.session_state.all_offers)
    if not optimal:
        st.warning("No optimal matching blocks detected.")
        return

    opt_df  = pd.DataFrame(optimal)
    opt_inv = opt_df["invested"].sum()
    opt_pnl = opt_df["pnl"].sum()
    opt_fin = opt_inv + opt_pnl
    opt_roi = (opt_pnl / opt_inv * 100) if opt_inv else 0

    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
        st.write(f"* **Initial Investment:** ${opt_inv:,.2f}")
        st.write(f"* **Final Portfolio Value in 2025:** ${opt_fin:,.2f}")
        st.write(f"* **Total Profit:** ${opt_pnl:,.2f}")
        st.write(f"* **Return Percentage:** {opt_roi:.2f}%")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("📥 Import Optimal Baskets to Active Portfolio",
                     type="primary", use_container_width=True):
            for item in optimal:
                if not any(p["ticker"] == item["ticker"] and p["source"] == "Offer"
                           for p in st.session_state.portfolio):
                    st.session_state.portfolio.append(item.copy())
            st.success("Baskets successfully updated.")
            st.rerun()
    with c2:
        st.dataframe(opt_df[["ticker", "shares", "buy_date",
                              "sell_date", "invested", "roi"]])

    gc1, gc2 = st.columns(2)
    with gc1:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(opt_df["invested"], labels=opt_df["ticker"], autopct="%1.1f%%")
        ax.set_title("Portfolio Allocation Matrix Weighting")
        st.pyplot(fig)
    with gc2:
        fig_g, ax_g = plt.subplots(figsize=(5, 3.5))
        ax_g.plot([0, 1], [opt_inv, opt_fin], "o-", color="orange", linewidth=3)
        ax_g.set_xticks([0, 1])
        ax_g.set_xticklabels(["Initial", "Final"])
        ax_g.set_title("Equity Growth Curve Chart")
        st.pyplot(fig_g)


# ==============================================================================
# 9. OPTIONS SIMULATION PAGES
# ==============================================================================

def render_options_home():
    go("Home", "⬅️ Back to Main Menu", key="oh_back")
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<h2 style='text-align:center;'>📉 Options Simulation Suite</h2>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#7F8C8D;'>"
        "Explore the institutional options catalog or construct your own options book.</p>",
        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class='options-card' style='text-align:center;padding:35px;'>
            <div style='font-size:44px;'>🏦</div>
            <h3 style='margin:8px 0;'>Company Options Portfolio</h3>
            <p style='color:#1a3a5c;'>View the full institutional options catalog with
            tiered pricing. See how the entire company inventory is projected to perform.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("View Company Options Portfolio", type="primary",
                     use_container_width=True, key="oh_go_company"):
            st.session_state.view_mode = "CompanyOptions"
            st.rerun()

    with c2:
        st.markdown("""
        <div class='options-card' style='text-align:center;padding:35px;'>
            <div style='font-size:44px;'>🛠️</div>
            <h3 style='margin:8px 0;'>Buy / Build Custom Options Portfolio</h3>
            <p style='color:#1a3a5c;'>Pick from existing catalog offers or define fully
            custom contracts. Build your personal options book and analyse the results.</p>
        </div>""", unsafe_allow_html=True)
        if st.button("Build Custom Options Portfolio", type="primary",
                     use_container_width=True, key="oh_go_custom"):
            st.session_state.view_mode = "CustomOptionsPortfolio"
            st.rerun()


def render_company_options():
    go("OptionsHome", "⬅️ Options Menu", key="co_back")
    st.header("🏦 Company Options Portfolio — Full Catalog")
    st.write("Complete institutional options inventory with **tiered pricing**. "
             "Tier-1 contracts carry an introductory discount; "
             "Tier-2 contracts are priced at the standard rate.")

    inv = st.session_state.options_inventory
    if not inv:
        st.error("No options inventory available.")
        return

    total_t1_rev = sum(o["tier1_contracts"] * o["tier1_premium"] * 100 for o in inv)
    total_t2_rev = sum(o["tier2_contracts"] * o["tier2_premium"] * 100 for o in inv)
    total_rev    = total_t1_rev + total_t2_rev
    total_payout = sum(o["total_contracts"] * 100 * o["close_value_per_share"] for o in inv)
    company_pnl  = total_rev - total_payout

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Premium Revenue",   f"${total_rev:,.2f}")
    m2.metric("Total Projected Payout",  f"${total_payout:,.2f}")
    m3.metric("Company Net P&L",         f"${company_pnl:,.2f}",
              delta=f"{(company_pnl / total_rev * 100):.1f}% margin" if total_rev else None)

    st.markdown("---")
    st.subheader("📋 Options Inventory Catalog")

    cols = st.columns(3)
    for idx, opt in enumerate(inv):
        with cols[idx % 3]:
            itm_tag    = "✅ ITM" if opt["in_the_money"] else "❌ OTM"
            type_color = "#155724" if opt["option_type"] == "CALL" else "#721c24"
            t1_rem     = max(0, opt["tier1_contracts"] - opt["contracts_sold"])
            avail      = opt["total_contracts"] - opt["contracts_sold"]

            st.markdown(f"""
            <div class='options-card'>
                <h4>{opt['ticker']}
                  <span style='color:{type_color};font-size:13px;'>&nbsp;{opt['option_type']}</span>
                  <span style='font-size:11px;color:#7f8c8d;'>&nbsp;{opt['company_name']}</span>
                </h4>
                <hr style='margin:0.4em 0;'>
                <b>Strike:</b> ${opt['strike_price']:,.2f}&nbsp;|&nbsp;
                <b>Expiry:</b> {opt['expiry_date'].strftime('%Y-%m-%d')}<br>
                <b>Underlying:</b> ${opt['underlying_price']:,.2f}&nbsp;|&nbsp;
                <b>Model Close:</b> {opt['close_date'].strftime('%Y-%m-%d')}<br>
                <b>Forecast Final Price:</b> ${opt['final_underlying']:,.2f}&nbsp;|&nbsp;{itm_tag}<br>
                <hr style='margin:0.4em 0;'>
                <span class='tier-badge-1'>🟢 Tier 1: {t1_rem} left @ ${opt['tier1_premium']:.2f}/sh</span><br>
                <span class='tier-badge-2'>🟡 Tier 2: {opt['tier2_contracts']} total @ ${opt['tier2_premium']:.2f}/sh</span><br>
                <small><b>Available:</b> {avail} of {opt['total_contracts']} contracts
                &nbsp;|&nbsp; {opt['contracts_sold']} sold</small>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📊 See Company Portfolio Results", type="primary",
                 use_container_width=True, key="co_go_results"):
        st.session_state.view_mode = "CompanyOptionsResults"
        st.rerun()


def render_company_options_results():
    go("CompanyOptions", "⬅️ Back to Catalog", key="cor_back")
    st.header("📊 Company Options Portfolio — Performance Dashboard")
    st.write("Results assume the full inventory is sold at each tier's rate. "
             "**Green** = company profitable (premium > payout).  "
             "**Red** = company paid out more than it collected.")

    # ── CHANGE 3: Run New Simulation button ────────────────────────────────
    st.markdown("---")
    sim_col1, sim_col2 = st.columns([3, 1])
    with sim_col1:
        st.caption(f"🎲 Current simulation seed: **{st.session_state.sim_seed}**  "
                   "— Click the button to generate a brand-new market scenario.")
    with sim_col2:
        if st.button("🔄 Run New Simulation", type="primary", use_container_width=True,
                     key="cor_resim"):
            # Advance the seed so each click gives a genuinely different scenario
            st.session_state.sim_seed = (st.session_state.sim_seed + 7) % 100000
            # Regenerate the inventory with the new seed
            st.session_state.options_inventory = generate_options_inventory(
                sim_seed=st.session_state.sim_seed)
            # Clear the options cart so stale positions don't linger
            st.session_state.options_portfolio = []
            st.rerun()
    st.markdown("---")
    # ── end CHANGE 3 ───────────────────────────────────────────────────────

    inv = st.session_state.options_inventory
    if not inv:
        st.error("No inventory data available.")
        return

    rows = []
    for opt in inv:
        t1        = opt["tier1_contracts"]
        t2        = opt["tier2_contracts"]
        prem_coll = (t1 * opt["tier1_premium"] * 100) + (t2 * opt["tier2_premium"] * 100)
        payout    = opt["total_contracts"] * 100 * opt["close_value_per_share"]
        pnl       = prem_coll - payout
        roi       = (pnl / prem_coll * 100) if prem_coll else 0
        rows.append({
            "ticker":            opt["ticker"],
            "option_type":       opt["option_type"],
            "total_contracts":   opt["total_contracts"],
            "premium_collected": prem_coll,
            "payout":            payout,
            "pnl":               pnl,
            "roi":               roi,
            "close_date":        opt["close_date"],
            "expiry_date":       opt["expiry_date"],
            "in_the_money":      opt["in_the_money"],
        })

    df           = pd.DataFrame(rows)
    total_prem   = df["premium_collected"].sum()
    total_payout = df["payout"].sum()
    total_pnl    = df["pnl"].sum()
    total_roi    = (total_pnl / total_prem * 100) if total_prem else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Premium Collected",  f"${total_prem:,.2f}")
    c2.metric("Total Payouts to Holders", f"${total_payout:,.2f}")
    c3.metric("Company Net P&L",          f"${total_pnl:,.2f}")
    c4.metric("Company Net ROI",          f"{total_roi:.2f}%")

    st.markdown("---")
    st.subheader("📈 Visualisation Suite")

    vc1, vc2 = st.columns(2)
    origin = datetime.date(2024, 6, 1)

    with vc1:
        fig_t, ax_t = plt.subplots(figsize=(7, 4))
        for i, row in df.iterrows():
            clr      = "green" if row["pnl"] >= 0 else "red"
            duration = (row["close_date"] - origin).days
            ax_t.barh(i, duration, left=0, color=clr, alpha=0.75, height=0.55)
            ax_t.text(duration + 1, i,
                      f"{row['ticker']} {row['option_type']}  "
                      f"{'ITM' if row['in_the_money'] else 'OTM'}",
                      va="center", fontsize=8)
        ax_t.set_title("Contract Closure Timeline  (Days from Jun 1, 2024)")
        ax_t.set_yticks(range(len(df)))
        ax_t.set_yticklabels(
            [f"{r['ticker']} {r['option_type']}" for _, r in df.iterrows()], fontsize=8)
        ax_t.set_xlabel("Days to Close")
        plt.tight_layout()
        st.pyplot(fig_t)

        fig_b, ax_b = plt.subplots(figsize=(6, 3.5))
        colors = ["green" if x >= 0 else "red" for x in df["pnl"]]
        labels = [f"{r['ticker']}\n{r['option_type']}" for _, r in df.iterrows()]
        ax_b.bar(labels, df["pnl"], color=colors)
        ax_b.axhline(0, color="black", linewidth=0.8)
        ax_b.set_title("Company P&L by Option Contract")
        plt.xticks(rotation=15)
        plt.tight_layout()
        st.pyplot(fig_b)

    with vc2:
        sorted_df = df.sort_values("close_date")
        cum_pnl   = sorted_df["pnl"].cumsum()
        fig_e, ax_e = plt.subplots(figsize=(6, 3.5))
        ax_e.plot(sorted_df["close_date"], cum_pnl,
                  marker="o", color="#7B1FA2", linewidth=2)
        ax_e.axhline(0, color="gray", linewidth=0.8, linestyle="--")
        ax_e.fill_between(sorted_df["close_date"], cum_pnl, alpha=0.15, color="#7B1FA2")
        ax_e.set_title("Cumulative Equity Curve  (Company View)")
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig_e)

        itm_c = int(df["in_the_money"].sum())
        otm_c = len(df) - itm_c
        if itm_c + otm_c > 0:
            fig_pi, ax_pi = plt.subplots(figsize=(4, 4))
            ax_pi.pie([itm_c, otm_c],
                      labels=["In the Money", "Out of Money"],
                      autopct="%1.1f%%",
                      colors=["#4CAF50", "#F44336"],
                      startangle=90)
            ax_pi.set_title("ITM vs OTM Breakdown")
            st.pyplot(fig_pi)

    st.markdown("---")
    st.subheader("📋 Detailed Options Results Table")
    dt = df.copy()
    dt["in_the_money"] = dt["in_the_money"].map({True: "✅ ITM", False: "❌ OTM"})
    st.dataframe(
        dt.style.format({
            "premium_collected": "${:,.2f}",
            "payout":            "${:,.2f}",
            "pnl":               "${:,.2f}",
            "roi":               "{:.2f}%",
        }),
        use_container_width=True)


def render_custom_options_portfolio():
    st.header("🛠️ Build Your Custom Options Portfolio")
    st.write("Use the **Offers** tab to buy from the live catalog (tiered pricing applies), "
             "or the **Custom Desk** to define any contract from scratch.")

    tab1, tab2 = st.tabs(["🏦  Offers  —  Live Catalog", "🎛️  Custom Desk"])

    with tab1:
        st.subheader("Institutional Options Offers  ·  Tiered Pricing Active")
        st.caption("Supply depletes as contracts are purchased. "
                   "Tier-1 slots fill first at the discounted rate.")

        inv = st.session_state.options_inventory
        if not inv:
            st.error("No inventory available.")
        else:
            cols = st.columns(3)
            for idx, opt in enumerate(inv):
                available = opt["total_contracts"] - opt["contracts_sold"]
                with cols[idx % 3]:
                    if available <= 0:
                        st.markdown(f"""
                        <div class='options-card' style='opacity:0.45;'>
                            <h4>{opt['ticker']} {opt['option_type']}
                              <span style='color:red;'>— SOLD OUT</span></h4>
                        </div>""", unsafe_allow_html=True)
                        continue

                    t1_rem     = max(0, opt["tier1_contracts"] - opt["contracts_sold"])
                    type_color = "#155724" if opt["option_type"] == "CALL" else "#721c24"

                    st.markdown(f"""
                    <div class='options-card'>
                        <h4>{opt['ticker']}
                          <span style='color:{type_color};font-size:13px;'>
                            &nbsp;{opt['option_type']}</span>
                        </h4>
                        <b>Strike:</b> ${opt['strike_price']:,.2f}&nbsp;|&nbsp;
                        <b>Expiry:</b> {opt['expiry_date'].strftime('%Y-%m-%d')}<br>
                        <b>Underlying:</b> ${opt['underlying_price']:,.2f}<br>
                        <span class='tier-badge-1'>
                          🟢 Tier 1: {t1_rem} left @ ${opt['tier1_premium']:.2f}/sh
                        </span><br>
                        <span class='tier-badge-2'>
                          🟡 Tier 2: {opt['tier2_contracts']} total @ ${opt['tier2_premium']:.2f}/sh
                        </span><br>
                        <small><b>Available:</b> {available} contracts</small>
                    </div>""", unsafe_allow_html=True)

                    n_contracts = st.number_input(
                        f"Contracts — {opt['ticker']} {opt['option_type']}",
                        min_value=1, max_value=available,
                        value=min(5, available),
                        key=f"oc_{opt['option_id']}")

                    cost_prev, t1_p, t2_p, blended = compute_tiered_cost(opt, n_contracts)
                    st.caption(
                        f"💰 Estimated Cost: **${cost_prev:,.2f}**  "
                        f"(T1: {t1_p} × ${opt['tier1_premium']:.2f}  |  "
                        f"T2: {t2_p} × ${opt['tier2_premium']:.2f}  per share)")

                    already = any(
                        p["option_id"] == opt["option_id"] and p["source"] == "Offer"
                        for p in st.session_state.options_portfolio)

                    if already:
                        st.button("✅ In Cart", key=f"oadd_{opt['option_id']}",
                                  disabled=True, use_container_width=True)
                    else:
                        if st.button(f"📥 Add {n_contracts} Contracts",
                                     key=f"oadd_{opt['option_id']}",
                                     use_container_width=True):
                            pos = build_option_position(opt, n_contracts, source="Offer")
                            opt["contracts_sold"] += n_contracts
                            st.session_state.options_portfolio.append(pos)
                            st.rerun()

    with tab2:
        st.subheader("Custom Options Desk")
        st.write("Define any contract by specifying the underlying ticker, type, "
                 "strike price, and duration. The model will forecast its close outcome.")

        with st.form("custom_option_form"):
            c1, c2 = st.columns(2)
            with c1:
                cticker     = st.text_input("Underlying Ticker (e.g. GOOG, META)",
                                            value="GOOG").upper().strip()
                ctype       = st.selectbox("Option Type", ["CALL", "PUT"])
                cunderlying = st.number_input(
                    "Current Underlying Price ($)", min_value=1.0, value=150.0, step=1.0)
            with c2:
                cstrike    = st.number_input(
                    "Strike Price ($)", min_value=1.0, value=157.0, step=1.0)
                cduration  = st.number_input(
                    "Duration (Days to Expiry)", min_value=7, max_value=365, value=90)
                ccontracts = st.number_input(
                    "Number of Contracts", min_value=1, value=10)

            csubmit = st.form_submit_button("📥 Add Custom Option to Cart")
            if csubmit:
                if not cticker:
                    st.error("Please enter a valid ticker symbol.")
                else:
                    pos = build_custom_option_position(
                        cticker, ctype, float(cstrike),
                        int(cduration), int(ccontracts), float(cunderlying))
                    if pos:
                        st.session_state.options_portfolio.append(pos)
                        st.success(
                            f"Custom {cticker} {ctype} option "
                            f"({ccontracts} contracts) added to cart.")
                        st.rerun()
                    else:
                        st.error("Could not build position. Please verify your inputs.")


def render_custom_options_results():
    go("CustomOptionsPortfolio", "⬅️ Back to Portfolio Builder", key="cur_back")
    st.header("📊 Custom Options Portfolio — Results Dashboard")

    if not st.session_state.options_portfolio:
        st.warning("No options positions to evaluate. "
                   "Add items via the portfolio builder.")
        return

    df = pd.DataFrame(st.session_state.options_portfolio)

    total_paid  = df["premium_paid_total"].sum()
    total_close = df["close_value_total"].sum()
    total_pnl   = df["pnl"].sum()
    roi_pct     = (total_pnl / total_paid * 100) if total_paid else 0
    itm_count   = int(df["in_the_money"].sum())
    otm_count   = len(df) - itm_count

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Premium Paid",  f"${total_paid:,.2f}")
    c2.metric("Total Close Value",   f"${total_close:,.2f}")
    c3.metric("Net P&L",             f"${total_pnl:,.2f}")
    c4.metric("Portfolio ROI",       f"{roi_pct:.2f}%")

    st.markdown("---")
    st.subheader("📈 Performance Visualisation Suite")

    origin = datetime.date(2024, 6, 1)
    vc1, vc2 = st.columns(2)

    with vc1:
        fig_t, ax_t = plt.subplots(figsize=(7, 4))
        for i, row in df.iterrows():
            clr      = "green" if row["pnl"] >= 0 else "red"
            duration = (row["close_date"] - origin).days
            ax_t.barh(i, duration, left=0, color=clr, alpha=0.75, height=0.55)
            ax_t.text(duration + 1, i,
                      f"{row['ticker']} {row['option_type']}  "
                      f"{'ITM ✅' if row['in_the_money'] else 'OTM ❌'}",
                      va="center", fontsize=8)
        ax_t.set_title("Contract Closure Timeline  (Days from Jun 1, 2024)")
        ax_t.set_yticks(range(len(df)))
        ax_t.set_yticklabels(
            [f"{r['ticker']} {r['option_type']}" for _, r in df.iterrows()], fontsize=8)
        ax_t.set_xlabel("Days to Close")
        plt.tight_layout()
        st.pyplot(fig_t)

        fig_b, ax_b = plt.subplots(figsize=(6, 3.5))
        colors = ["green" if x >= 0 else "red" for x in df["pnl"]]
        labels = [f"{r['ticker']}\n{r['option_type']}" for _, r in df.iterrows()]
        ax_b.bar(labels, df["pnl"], color=colors)
        ax_b.axhline(0, color="black", linewidth=0.8)
        ax_b.set_title("P&L by Options Position")
        plt.xticks(rotation=15)
        plt.tight_layout()
        st.pyplot(fig_b)

    with vc2:
        sorted_df = df.sort_values("close_date")
        cum_pnl   = sorted_df["pnl"].cumsum()
        fig_e, ax_e = plt.subplots(figsize=(6, 3.5))
        ax_e.plot(sorted_df["close_date"], cum_pnl,
                  marker="o", color="#4A90E2", linewidth=2)
        ax_e.axhline(0, color="gray", linewidth=0.8, linestyle="--")
        ax_e.fill_between(sorted_df["close_date"], cum_pnl, alpha=0.15, color="#4A90E2")
        ax_e.set_title("Cumulative Options P&L Curve")
        plt.xticks(rotation=20)
        plt.tight_layout()
        st.pyplot(fig_e)

        if itm_count + otm_count > 0:
            fig_pi, ax_pi = plt.subplots(figsize=(4, 4))
            ax_pi.pie(
                [itm_count, otm_count],
                labels=["In the Money", "Out of Money"],
                autopct="%1.1f%%",
                colors=["#4CAF50", "#F44336"],
                startangle=90)
            ax_pi.set_title("ITM vs OTM Breakdown")
            st.pyplot(fig_pi)

    st.markdown("---")
    st.subheader("📋 Detailed Options Execution Table")
    dt = df[[
        "ticker", "option_type", "strike_price", "contracts",
        "premium_paid_total", "blended_premium_per_share",
        "close_date", "close_value_total", "pnl", "roi",
        "in_the_money", "source"
    ]].copy()
    dt.columns = [
        "Ticker", "Type", "Strike", "Contracts",
        "Premium Paid", "Blended $/Share",
        "Close Date", "Close Value", "P&L", "ROI %",
        "ITM", "Source"
    ]
    dt["ITM"] = dt["ITM"].map({True: "✅ ITM", False: "❌ OTM"})
    st.dataframe(
        dt.style.format({
            "Strike":          "${:,.2f}",
            "Premium Paid":    "${:,.2f}",
            "Blended $/Share": "${:,.2f}",
            "Close Value":     "${:,.2f}",
            "P&L":             "${:,.2f}",
            "ROI %":           "{:.2f}%",
        }),
        use_container_width=True)


# ==============================================================================
# 10. MASTER ROUTER  (unchanged)
# ==============================================================================

_STOCK_VIEWS = {"StockHome", "Offers", "Custom", "StockResults", "Optimal"}
_OPT_CART    = {"CustomOptionsPortfolio", "CustomOptionsResults"}

vm = st.session_state.view_mode

if vm in _STOCK_VIEWS:
    render_stock_sidebar()
elif vm in _OPT_CART:
    render_options_sidebar()

if   vm == "Home":                   render_home()
elif vm == "StockHome":              render_stock_home()
elif vm == "Offers":                 render_offers_page()
elif vm == "Custom":                 render_custom_stock_page()
elif vm == "StockResults":           render_stock_results()
elif vm == "Optimal":                render_optimal_portfolio()
elif vm == "OptionsHome":            render_options_home()
elif vm == "CompanyOptions":         render_company_options()
elif vm == "CompanyOptionsResults":  render_company_options_results()
elif vm == "CustomOptionsPortfolio": render_custom_options_portfolio()
elif vm == "CustomOptionsResults":   render_custom_options_results()
else:
    st.session_state.view_mode = "Home"
    st.rerun()