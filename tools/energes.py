"""Εργαλείο 1 – Έλεγχος ενεργών εργασιών εργοταξίου."""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from common import BLUE, COLS_TASKS, fmt_dates, footer, load_input, sample_tasks, to_png_bytes

st.title("📅 Ενεργές εργασίες εργοταξίου")
st.markdown("Επίλεξε μια ημερομηνία για να δεις ποιες εργασίες και ποια συνεργεία βρίσκονται "
            "ταυτόχρονα στο εργοτάξιο.")


def gantt(df, day, active_mask):
    """Διάγραμμα Gantt: μπλε οι ενεργές εργασίες, κόκκινη γραμμή η επιλεγμένη ημερομηνία."""
    d = df.assign(active=active_mask).sort_values("Ημερομηνία Έναρξης").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 0.36 * len(d) + 1.3))
    for i, row in d.iterrows():
        start = mdates.date2num(row["Ημερομηνία Έναρξης"])
        width = mdates.date2num(row["Ημερομηνία Λήξης"]) - start + 1
        ax.barh(i, width, left=start, height=0.6, color=BLUE if row["active"] else "#C9D3DD")
    ax.axvline(mdates.date2num(day), color="#E4572E", lw=2)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d["Εργασία"], fontsize=8)
    ax.invert_yaxis()
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.grid(axis="x", alpha=0.3)
    ax.set_title(f"Χρονοδιάγραμμα εργασιών – ενεργές στις {day:%d/%m/%Y}", fontsize=11)
    fig.tight_layout()
    return fig


df = load_input("energes", COLS_TASKS, sample_tasks, "Παράδειγμα (Πίνακας 1 της εργασίας)")
if df is not None:
    try:
        df["Ημερομηνία Έναρξης"] = pd.to_datetime(df["Ημερομηνία Έναρξης"])
        df["Ημερομηνία Λήξης"] = pd.to_datetime(df["Ημερομηνία Λήξης"])
    except Exception as e:
        st.error(f"Οι ημερομηνίες δεν διαβάστηκαν σωστά: {e}")
        st.stop()

    start, end = df["Ημερομηνία Έναρξης"].min(), df["Ημερομηνία Λήξης"].max()
    c1, c2 = st.columns([1, 2])
    with c1:
        day = pd.to_datetime(st.date_input("Ημερομηνία ελέγχου", value=pd.Timestamp(2025, 5, 11).date()
                                           if start <= pd.Timestamp(2025, 5, 11) <= end else start.date(),
                                           min_value=start.date(), max_value=end.date(), format="DD/MM/YYYY"))
    with c2:
        st.markdown(f"<br>Διάρκεια έργου στο αρχείο: **{start:%d/%m/%Y} – {end:%d/%m/%Y}**",
                    unsafe_allow_html=True)

    mask = (df["Ημερομηνία Έναρξης"] <= day) & (df["Ημερομηνία Λήξης"] >= day)
    active = df[mask]

    m1, m2, m3 = st.columns(3)
    m1.metric("Ενεργές εργασίες", len(active))
    m2.metric("Συνεργεία στο εργοτάξιο", active["Συνεργείο"].nunique())
    m3.metric("Σύνολο εργασιών", len(df))

    if active.empty:
        st.warning(f"Δεν υπάρχουν ενεργές εργασίες στις {day:%d/%m/%Y}.")
    else:
        st.dataframe(fmt_dates(active[COLS_TASKS], COLS_TASKS[2:]), hide_index=True, width="stretch")
        per_crew = active.groupby("Συνεργείο").size().sort_values(ascending=False)
        if (per_crew > 1).any():
            busy = ", ".join(f"{k} ({v})" for k, v in per_crew[per_crew > 1].items())
            st.info(f"Συνεργεία με περισσότερες από μία ενεργές εργασίες: {busy}. "
                    "Εδώ υπάρχει κίνδυνος συμφόρησης αν κάποια από αυτές καθυστερήσει.")

    fig = gantt(df, day, mask)
    st.pyplot(fig)
    st.download_button("🖼️ Κατέβασε το διάγραμμα (PNG)", to_png_bytes(fig), "gantt.png", "image/png")

footer()
