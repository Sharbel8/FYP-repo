"""Streamlit UI for live traffic data stored in MongoDB."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from config import get_settings
from dashboard import DashboardDataService
from database import AggregateRepository, DetectionRepository, PredictionRepository, SignalStateRepository, get_database


def main() -> None:
    """Render dashboard without starting any camera, detector, or worker."""
    settings = get_settings()
    st.set_page_config(page_title=settings.app.name, page_icon="🚦", layout="wide")
    st.title("🚦 Smart Traffic Light Dashboard")
    st.caption("Read-only live view from MongoDB. Refresh the page to load new data.")
    database = get_database()
    data = DashboardDataService(DetectionRepository(database), SignalStateRepository(database), AggregateRepository(database), PredictionRepository(database))
    snapshot = data.latest_snapshot()
    detection, signal, aggregate, prediction = (snapshot[key] for key in ("detection", "signal", "aggregate", "prediction"))
    features = aggregate.get("features", {}) if aggregate else {}
    columns = st.columns(4)
    columns[0].metric("Vehicles", detection.get("total_vehicles", 0) if detection else 0)
    columns[1].metric("Pedestrians", detection.get("total_pedestrians", 0) if detection else 0)
    columns[2].metric("Signal", signal.get("state", "No data") if signal else "No data")
    columns[3].metric("Predicted congestion", prediction.get("label", "Not trained") if prediction else "Not trained", f"{prediction.get('probability', 0):.0%}" if prediction else None)
    st.subheader("Latest traffic features")
    st.json(features or {"message": "No aggregate data yet. Run the collectors and Step 7 aggregator first."})
    history = data.aggregate_history()
    if not history.empty:
        st.subheader("Traffic trend")
        st.plotly_chart(px.line(history, x="window_end", y=["vehicle_count", "flow_rate_per_min", "congestion_score"], markers=True), use_container_width=True)
    else:
        st.info("No historical aggregates yet.")


if __name__ == "__main__":
    main()
