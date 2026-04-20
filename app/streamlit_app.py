import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from io import StringIO

st.set_page_config(
    page_title="Glow25 Conversion Benchmarker",
    page_icon="✦",
    layout="wide",
)

DATA_PATH = "data/processed/events_clean.csv"

COUNTRIES = ["DE", "NL", "BE", "FR"]
DEVICES = ["mobile", "desktop", "tablet"]
CHANNELS = ["organic_search", "paid_social", "email", "direct", "paid_search", "influencer"]

# avg collagen product price assumption for the CRO simulator
AVG_ORDER_VALUE = 39.90
AVG_MONTHLY_SESSIONS = None  # derived from data


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["event_time"])
    return df


@st.cache_data
def compute_funnel(df):
    user_events = (
        df.groupby("user_id")["event_type"]
        .apply(lambda x: set(x))
        .reset_index()
    )
    viewers = user_events["user_id"].nunique()
    carted = user_events[user_events["event_type"].apply(lambda s: "cart" in s)]["user_id"].nunique()
    purchasers = user_events[user_events["event_type"].apply(lambda s: "purchase" in s)]["user_id"].nunique()
    return viewers, carted, purchasers


@st.cache_data
def compute_country_funnel(df):
    rows = []
    for country in df["country"].unique():
        sub = df[df["country"] == country]
        users = sub.groupby("user_id")["event_type"].apply(set)
        viewers = len(users)
        carted = users.apply(lambda s: "cart" in s).sum()
        purchasers = users.apply(lambda s: "purchase" in s).sum()
        rows.append({
            "country": country,
            "viewers": viewers,
            "carted": int(carted),
            "purchasers": int(purchasers),
            "view_to_cart_pct": round(100 * carted / viewers, 2) if viewers else 0,
            "cart_to_purchase_pct": round(100 * purchasers / carted, 2) if carted else 0,
            "overall_cvr_pct": round(100 * purchasers / viewers, 2) if viewers else 0,
        })
    return pd.DataFrame(rows).sort_values("overall_cvr_pct", ascending=False)


@st.cache_data
def compute_channel_cvr(df):
    rows = []
    for channel in df["channel"].unique():
        sub = df[df["channel"] == channel]
        users = sub.groupby("user_id")["event_type"].apply(set)
        viewers = len(users)
        purchasers = users.apply(lambda s: "purchase" in s).sum()
        rows.append({
            "channel": channel,
            "sessions": viewers,
            "purchases": int(purchasers),
            "cvr_pct": round(100 * purchasers / viewers, 2) if viewers else 0,
        })
    return pd.DataFrame(rows).sort_values("cvr_pct", ascending=False)


# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.markdown("## ✦ Glow25")
st.sidebar.markdown("**Conversion Benchmarker**")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Funnel Overview", "Country Deep-Dive", "Channel Performance", "CRO Simulator"],
)

st.sidebar.divider()
st.sidebar.markdown("**Filters**")

selected_countries = st.sidebar.multiselect(
    "Countries", COUNTRIES, default=COUNTRIES, key="countries"
)
selected_devices = st.sidebar.multiselect(
    "Devices", DEVICES, default=DEVICES, key="devices"
)

if st.sidebar.button("Reset filters"):
    st.session_state["countries"] = COUNTRIES
    st.session_state["devices"] = DEVICES
    st.rerun()

# ── Load & filter data ────────────────────────────────────────────────────────

try:
    raw_df = load_data()
except FileNotFoundError:
    st.error(
        "Could not find `data/processed/events_clean.csv`. "
        "Run `python data/ingest.py` first to generate the processed data file."
    )
    st.stop()

if not selected_countries or not selected_devices:
    st.warning("No data to show — select at least one country and one device.")
    st.stop()

df = raw_df[
    raw_df["country"].isin(selected_countries) &
    raw_df["device"].isin(selected_devices)
].copy()

if df.empty:
    st.warning("Filter combination returned no rows. Try a broader selection.")
    st.stop()


# ── Page 1: Funnel Overview ───────────────────────────────────────────────────

if page == "Funnel Overview":
    st.title("Funnel Overview")
    st.markdown("Overall purchase funnel health across selected markets and devices.")

    viewers, carted, purchasers = compute_funnel(df)
    total_events = len(df)
    cart_abandon_rate = round(100 * (1 - purchasers / carted), 1) if carted else 0
    overall_cvr = round(100 * purchasers / viewers, 2) if viewers else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall CVR (view → purchase)", f"{overall_cvr}%")
    col2.metric("Cart Abandonment Rate", f"{cart_abandon_rate}%")
    col3.metric("Total Sessions (unique users)", f"{viewers:,}")
    col4.metric("Total Purchases", f"{purchasers:,}")

    st.divider()

    # Plotly funnel chart
    funnel_fig = go.Figure(go.Funnel(
        y=["Viewed", "Added to Cart", "Purchased"],
        x=[viewers, carted, purchasers],
        textinfo="value+percent initial",
        marker=dict(color=["#D4537E", "#a83460", "#7a2445"]),
    ))
    funnel_fig.update_layout(
        title="Purchase Funnel — Volume by Stage",
        paper_bgcolor="#1a1a1a",
        plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(funnel_fig, use_container_width=True)
    st.caption(
        f"The biggest drop happens at the view → cart step "
        f"({round(100*carted/viewers,1)}% make it through). "
        "Cart abandonment is where checkout friction typically sits — worth A/B testing payment methods."
    )

    st.divider()

    # device breakdown bar
    device_cvr = []
    for dev in df["device"].unique():
        sub = df[df["device"] == dev]
        u = sub.groupby("user_id")["event_type"].apply(set)
        v = len(u)
        p = u.apply(lambda s: "purchase" in s).sum()
        device_cvr.append({"device": dev, "cvr_pct": round(100 * p / v, 2) if v else 0})
    device_df = pd.DataFrame(device_cvr).sort_values("cvr_pct", ascending=False)

    fig_dev = px.bar(
        device_df, x="device", y="cvr_pct",
        title="CVR by Device",
        labels={"cvr_pct": "CVR (%)", "device": "Device"},
        color="device",
        color_discrete_sequence=["#D4537E", "#a83460", "#7a2445"],
    )
    fig_dev.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5", showlegend=False,
    )
    st.plotly_chart(fig_dev, use_container_width=True)
    st.caption("Mobile typically converts lower — if desktop CVR is 2× mobile, there's a UX problem on the mobile checkout.")


# ── Page 2: Country Deep-Dive ─────────────────────────────────────────────────

elif page == "Country Deep-Dive":
    st.title("Country Deep-Dive")
    st.markdown("Where does each market lose users — and by how much?")

    country_df = compute_country_funnel(df)

    if country_df.empty:
        st.warning("No country data for current filter selection.")
        st.stop()

    worst = country_df.iloc[-1]["country"]
    st.info(f"Worst-performing market: **{worst}** — lowest overall CVR in current filter.")

    # CVR bar chart
    fig_cvr = px.bar(
        country_df.sort_values("overall_cvr_pct"),
        x="overall_cvr_pct", y="country",
        orientation="h",
        title="Overall CVR by Country (view → purchase)",
        labels={"overall_cvr_pct": "CVR (%)", "country": "Country"},
        color="overall_cvr_pct",
        color_continuous_scale=["#7a2445", "#D4537E"],
    )
    fig_cvr.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_cvr, use_container_width=True)
    st.caption(f"{worst} has the lowest CVR — check localised checkout experience and payment methods for that market.")

    st.divider()

    # Funnel stage table
    st.markdown("**Funnel stage rates per country**")
    display_cols = ["country", "viewers", "carted", "purchasers", "view_to_cart_pct", "cart_to_purchase_pct", "overall_cvr_pct"]
    st.dataframe(
        country_df[display_cols].rename(columns={
            "view_to_cart_pct": "View→Cart %",
            "cart_to_purchase_pct": "Cart→Purchase %",
            "overall_cvr_pct": "Overall CVR %",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # cart-to-purchase comparison
    fig_c2p = px.bar(
        country_df.sort_values("cart_to_purchase_pct"),
        x="cart_to_purchase_pct", y="country",
        orientation="h",
        title="Cart → Purchase Rate by Country",
        labels={"cart_to_purchase_pct": "Cart→Purchase %", "country": "Country"},
        color="cart_to_purchase_pct",
        color_continuous_scale=["#7a2445", "#D4537E"],
    )
    fig_c2p.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_c2p, use_container_width=True)
    st.caption("A low cart→purchase rate (vs high view→cart) points to checkout friction, not product-page problems.")


# ── Page 3: Channel Performance ───────────────────────────────────────────────

elif page == "Channel Performance":
    st.title("Channel Performance")
    st.markdown("Which acquisition channels actually convert — and which ones just bring traffic?")

    channel_df = compute_channel_cvr(df)

    # CVR ranking bar
    fig_ch = px.bar(
        channel_df,
        x="channel", y="cvr_pct",
        title="Purchase CVR by Channel",
        labels={"cvr_pct": "CVR (%)", "channel": "Channel"},
        color="cvr_pct",
        color_continuous_scale=["#7a2445", "#D4537E"],
    )
    fig_ch.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_ch, use_container_width=True)
    st.caption("Email typically punches above its weight on CVR — it's talking to people who already know the brand.")

    st.divider()

    # Scatter: sessions vs CVR, sized by purchases
    fig_scatter = px.scatter(
        channel_df,
        x="sessions", y="cvr_pct",
        size="purchases", color="channel",
        title="Sessions vs CVR — bubble size = purchase volume",
        labels={"sessions": "Sessions (unique users)", "cvr_pct": "CVR (%)", "channel": "Channel"},
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_scatter.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(
        "Channels in the top-right quadrant (high sessions + high CVR) are the most efficient. "
        "High sessions + low CVR means you're paying for unqualified traffic."
    )

    st.divider()

    st.markdown("**Channel summary table**")
    st.dataframe(
        channel_df.rename(columns={"cvr_pct": "CVR %", "sessions": "Sessions", "purchases": "Purchases"}),
        use_container_width=True,
        hide_index=True,
    )


# ── Page 4: CRO Simulator ─────────────────────────────────────────────────────

elif page == "CRO Simulator":
    st.title("CRO Impact Simulator")
    st.markdown(
        "Estimate the revenue impact of improving a specific funnel step. "
        "Useful for building a business case before committing to an A/B test."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        funnel_stage = st.selectbox(
            "Funnel stage to improve",
            ["View → Cart", "Cart → Purchase"],
        )
        improvement_pct = st.slider(
            "CVR improvement (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5
        )

    with col_b:
        aov = st.number_input(
            "Average Order Value (€)", min_value=10.0, max_value=200.0,
            value=AVG_ORDER_VALUE, step=1.0
        )

    st.divider()

    # compute baseline numbers from filtered data
    viewers, carted, purchasers = compute_funnel(df)
    # assume 30-day window = monthly
    monthly_viewers = viewers
    monthly_carted = carted
    monthly_purchases = purchasers

    baseline_cvr = purchasers / viewers if viewers else 0

    if funnel_stage == "View → Cart":
        # improving view→cart rate
        current_v2c = carted / viewers if viewers else 0
        new_v2c = current_v2c * (1 + improvement_pct / 100)
        new_carted = int(viewers * new_v2c)
        c2p_rate = purchasers / carted if carted else 0
        new_purchases = int(new_carted * c2p_rate)
    else:
        # improving cart→purchase rate
        c2p_rate = purchasers / carted if carted else 0
        new_c2p = c2p_rate * (1 + improvement_pct / 100)
        new_purchases = int(carted * new_c2p)

    additional_purchases = max(0, new_purchases - monthly_purchases)
    additional_revenue = additional_purchases * aov

    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline monthly purchases", f"{monthly_purchases:,}")
    col2.metric("Estimated new monthly purchases", f"{new_purchases:,}", delta=f"+{additional_purchases:,}")
    col3.metric("Estimated additional monthly revenue", f"€{additional_revenue:,.0f}")

    st.divider()

    # which country benefits most?
    st.markdown("**Which market benefits most from this improvement?**")

    country_impact = []
    country_funnel_df = compute_country_funnel(df)

    for _, row in country_funnel_df.iterrows():
        v = row["viewers"]
        ca = row["carted"]
        p = row["purchasers"]

        if funnel_stage == "View → Cart":
            v2c = ca / v if v else 0
            new_v2c_c = v2c * (1 + improvement_pct / 100)
            new_ca = int(v * new_v2c_c)
            c2p = p / ca if ca else 0
            new_p = int(new_ca * c2p)
        else:
            c2p = p / ca if ca else 0
            new_c2p_c = c2p * (1 + improvement_pct / 100)
            new_p = int(ca * new_c2p_c)

        add_p = max(0, new_p - p)
        country_impact.append({
            "country": row["country"],
            "baseline_purchases": int(p),
            "new_purchases": new_p,
            "additional_purchases": add_p,
            "additional_revenue_eur": round(add_p * aov, 2),
        })

    impact_df = pd.DataFrame(country_impact).sort_values("additional_revenue_eur", ascending=False)

    fig_impact = px.bar(
        impact_df,
        x="country", y="additional_revenue_eur",
        title=f"Additional Revenue by Country — {improvement_pct}% improvement on {funnel_stage}",
        labels={"additional_revenue_eur": "Additional Revenue (€)", "country": "Country"},
        color="additional_revenue_eur",
        color_continuous_scale=["#7a2445", "#D4537E"],
    )
    fig_impact.update_layout(
        paper_bgcolor="#1a1a1a", plot_bgcolor="#1a1a1a",
        font_color="#f5f5f5", coloraxis_showscale=False,
    )
    st.plotly_chart(fig_impact, use_container_width=True)

    st.markdown("**Scenario breakdown by country**")
    st.dataframe(
        impact_df.rename(columns={
            "baseline_purchases": "Baseline Purchases",
            "new_purchases": "New Purchases",
            "additional_purchases": "Additional Purchases",
            "additional_revenue_eur": "Additional Revenue (€)",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # download button
    csv_buffer = StringIO()
    impact_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download scenarios as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"cro_scenario_{funnel_stage.replace(' ', '_').lower()}_{improvement_pct}pct.csv",
        mime="text/csv",
    )
