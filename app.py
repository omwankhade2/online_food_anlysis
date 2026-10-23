import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Online Food Delivery Analytics",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background-color: #F5F7FB; }
.block-container { padding-top: 1.5rem; }
.hero {
    padding: 1.4rem 1.6rem; border-radius: 18px;
    background: linear-gradient(120deg, #172554, #2563EB);
    color: white; margin-bottom: 1.2rem;
}
.hero h1 { color: white; margin: 0; }
.hero p { color: #E0E7FF; margin: .35rem 0 0 0; }
div[data-testid="stMetric"] {
    background: white; border: 1px solid #E2E8F0;
    padding: 16px; border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🍔 Online Food Delivery Analytics</h1>
  <p>Explore customer demographics, ordering patterns, and feedback.</p>
</div>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    data = pd.read_csv(file)
    # Clean column names and text values
    data.columns = [str(c).strip() for c in data.columns]
    for col in data.select_dtypes(include=["object", "string"]).columns:
        data[col] = data[col].astype("string").str.strip()
    # The provided CSV has a column with no proper header. Keep its values,
    # but give it a clearer label rather than silently deleting it.
    if "Unnamed: 13" in data.columns:
        data = data.rename(columns={"Unnamed: 13": "Extra Field (originally Unnamed: 13)"})
    return data

uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data("online food delivery dataset.csv")
    except FileNotFoundError:
        st.info("Upload **online food delivery dataset.csv** using the sidebar, or keep it in the same folder as app.py.")
        st.stop()

required = ["Age", "Gender", "Occupation", "Family size", "Feedback", "Output"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"These expected columns are missing: {missing}")
    st.write("Columns found in your file:", df.columns.tolist())
    st.stop()

# Ensure numeric values are numeric
for col in ["Age", "Family size", "latitude", "longitude", "Pin code"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Sidebar filters
st.sidebar.header("🎛️ Filters")
filtered = df.copy()

filter_columns = [
    "Gender", "Occupation", "Marital Status", "Monthly Income",
    "Educational Qualifications", "Customer Type", "Feedback", "Output"
]
if "Extra Field (originally Unnamed: 13)" in filtered.columns:
    filter_columns.append("Extra Field (originally Unnamed: 13)")

for col in filter_columns:
    if col in filtered.columns:
        values = sorted(filtered[col].dropna().astype(str).unique().tolist())
        chosen = st.sidebar.multiselect(
            col,
            options=values,
            default=values,
            key=f"filter_{col}"
        )
        filtered = filtered[filtered[col].astype(str).isin(chosen)]

st.sidebar.caption(f"Showing {len(filtered):,} of {len(df):,} records")

# KPIs
st.subheader("📌 Key Metrics")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Customers", f"{len(filtered):,}")
avg_age = filtered["Age"].mean()
avg_family = filtered["Family size"].mean()
positive_pct = (
    filtered["Feedback"].astype(str).str.lower().eq("positive").mean() * 100
    if len(filtered) else 0
)
k2.metric("Average Age", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A")
k3.metric("Average Family Size", f"{avg_family:.1f}" if pd.notna(avg_family) else "N/A")
k4.metric("Positive Feedback", f"{positive_pct:.1f}%")

st.divider()

if filtered.empty:
    st.warning("No records match the selected filters. Change one or more filters in the sidebar.")
    st.stop()

# Prepare occupation summary
occupation_summary = (
    filtered.groupby("Occupation", as_index=False)
    .agg(
        Average_Age=("Age", "mean"),
        Average_Family_Size=("Family size", "mean"),
        Customers=("Occupation", "size")
    )
)

left, right = st.columns(2)
with left:
    st.subheader("👔 Customers by Occupation")
    counts = filtered["Occupation"].value_counts().rename_axis("Occupation").reset_index(name="Customers")
    fig = px.bar(
        counts, x="Occupation", y="Customers", color="Occupation",
        text="Customers", template="plotly_white",
        title="Customer Count by Occupation"
    )
    fig.update_layout(showlegend=False, title_x=0.02, height=400)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🎂 Average Age by Occupation")
    fig = px.bar(
        occupation_summary.sort_values("Average_Age", ascending=False),
        x="Occupation", y="Average_Age", color="Average_Age",
        color_continuous_scale="Blues", text_auto=".1f",
        hover_data=["Customers", "Average_Family_Size"],
        template="plotly_white", title="Average Age"
    )
    fig.update_layout(coloraxis_showscale=False, title_x=0.02, height=400)
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("🏠 Average Family Size by Occupation")
    fig = px.bar(
        occupation_summary.sort_values("Average_Family_Size", ascending=False),
        x="Occupation", y="Average_Family_Size", color="Occupation",
        text_auto=".2f", template="plotly_white",
        title="Average Family Size"
    )
    fig.update_layout(showlegend=False, title_x=0.02, height=400)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("💬 Customer Feedback")
    feedback_counts = filtered["Feedback"].value_counts().rename_axis("Feedback").reset_index(name="Customers")
    fig = px.pie(
        feedback_counts, names="Feedback", values="Customers",
        hole=0.52, color="Feedback", template="plotly_white",
        title="Positive vs Negative Feedback"
    )
    fig.update_layout(title_x=0.02, height=400)
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("🛍️ Order Output")
    output_counts = filtered["Output"].value_counts().rename_axis("Output").reset_index(name="Customers")
    fig = px.pie(
        output_counts, names="Output", values="Customers",
        hole=0.5, template="plotly_white", title="Output Distribution"
    )
    fig.update_layout(title_x=0.02, height=360)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📊 Age Distribution")
    fig = px.histogram(
        filtered.dropna(subset=["Age"]), x="Age", color="Gender",
        nbins=20, barmode="overlay", opacity=0.78,
        template="plotly_white", title="Customer Age Distribution"
    )
    fig.update_layout(title_x=0.02, height=360)
    st.plotly_chart(fig, use_container_width=True)

# Optional map if coordinates are available
if {"latitude", "longitude"}.issubset(filtered.columns):
    map_df = filtered.dropna(subset=["latitude", "longitude"])
    if not map_df.empty:
        with st.expander("📍 View customer locations"):
            st.map(map_df[["latitude", "longitude"]], latitude="latitude", longitude="longitude")

st.divider()
st.subheader("📋 Filtered Customer Data")
search = st.text_input("🔎 Search records", placeholder="Search any text in the table...")
table_df = filtered.copy()
if search:
    mask = table_df.astype(str).apply(
        lambda col: col.str.contains(search, case=False, na=False, regex=False)
    ).any(axis=1)
    table_df = table_df[mask]

st.caption(f"{len(table_df):,} records shown")
st.dataframe(table_df, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download filtered data as CSV",
    data=table_df.to_csv(index=False).encode("utf-8"),
    file_name="filtered_online_food_delivery_data.csv",
    mime="text/csv"
)

st.markdown(
    "<p style='text-align:center;color:#64748B;'>Built with Python · Pandas · Streamlit · Plotly</p>",
    unsafe_allow_html=True
)
