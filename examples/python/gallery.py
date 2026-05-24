"""Streamlit gallery for CEvNS Monte Carlo simulation outputs.

Scans the directory this file lives in for groups of files written by
mc_simulation.py — `{prefix}_spectrum.png`, `{prefix}_flux.png`,
`{prefix}_xsec.png`, `{prefix}_summary.txt` and `{prefix}_events.csv` —
and lets the user browse them.

Run from inside the container:
    streamlit run gallery.py --server.address=0.0.0.0
"""

from pathlib import Path

import streamlit as st

GALLERY_DIR = Path(__file__).resolve().parent
PLOT_KINDS = ("spectrum", "flux", "xsec")

st.set_page_config(page_title="CEvNS Gallery", layout="wide")
st.title("CEvNS Simulation Gallery")
st.caption(f"Reading outputs from `{GALLERY_DIR}`")

prefixes = sorted(
    {p.name.removesuffix("_summary.txt") for p in GALLERY_DIR.glob("*_summary.txt")}
)

if not prefixes:
    st.warning(
        "No simulation outputs found. Generate some with:\n\n"
        "```\npython3 mc_simulation.py --detector Ge --output demo --seed 42\n```"
    )
    st.stop()

selected = st.sidebar.selectbox("Run", prefixes)

summary_path = GALLERY_DIR / f"{selected}_summary.txt"
if summary_path.exists():
    st.sidebar.subheader("Summary")
    st.sidebar.code(summary_path.read_text(), language="text")

cols = st.columns(len(PLOT_KINDS))
captions = {
    "spectrum": "Detected recoil spectrum",
    "flux": "Reactor antineutrino flux",
    "xsec": "CEvNS cross section vs E_ν",
}
for col, kind in zip(cols, PLOT_KINDS):
    plot_path = GALLERY_DIR / f"{selected}_{kind}.png"
    if plot_path.exists():
        col.image(str(plot_path), caption=captions[kind], use_container_width=True)
    else:
        col.info(f"`{plot_path.name}` not found")

events_path = GALLERY_DIR / f"{selected}_events.csv"
if events_path.exists():
    with st.expander(f"Events ({events_path.name})"):
        rows = events_path.read_text().splitlines()
        st.write(f"{len(rows) - 1} events")
        st.code("\n".join(rows[:21]), language="text")
