"""Εργαλείο 2 – Domino Effect: μετάδοση μιας καθυστέρησης στις εξαρτώμενες εργασίες."""
from collections import deque

import pandas as pd
import streamlit as st

from common import COLS_DOMINO, fmt_dates, footer, load_input, sample_domino, to_excel_bytes

st.title("⏳ Domino Effect καθυστερήσεων")
st.markdown("Επίλεξε μια εργασία που καθυστερεί και δες ποιες εργασίες εξαρτώνται από αυτήν, άμεσα ή "
            "έμμεσα, και πώς μετατοπίζεται το χρονοδιάγραμμα. Αν μια εργασία εξαρτάται από περισσότερες, "
            "γράψε τες στη στήλη «Εξαρτάται από» χωρισμένες με κόμμα.")


def predecessors(value):
    """Λίστα εργασιών από τις οποίες εξαρτάται μια εργασία."""
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [x.strip() for x in str(value).split(",") if x.strip()]


def affected_tasks(task, df):
    """Όλες οι εργασίες που εξαρτώνται (άμεσα ή έμμεσα) από την εργασία.
    Αναζήτηση κατά πλάτος: κάθε εργασία μετράται μία φορά, ακόμη κι αν υπάρχουν κύκλοι."""
    children = {}
    for _, row in df.iterrows():
        for p in predecessors(row["Εξαρτάται από"]):
            children.setdefault(p, []).append(row["Εργασία"])
    found, queue, seen = [], deque([task]), {task}
    while queue:
        current = queue.popleft()
        for child in children.get(current, []):
            if child not in seen:
                seen.add(child)
                found.append(child)
                queue.append(child)
    return found


df = load_input("domino", COLS_DOMINO, sample_domino, "Χρονοδιάγραμμα του έργου (Gantt 27/6/2025)")
if df is not None:
    df["Ημερομηνία Έναρξης"] = pd.to_datetime(df["Ημερομηνία Έναρξης"])
    df["Ημερομηνία Λήξης"] = pd.to_datetime(df["Ημερομηνία Λήξης"])

    unknown = sorted({p for v in df["Εξαρτάται από"] for p in predecessors(v)} - set(df["Εργασία"]))
    if unknown:
        st.warning("Οι εξής εργασίες αναφέρονται στη στήλη «Εξαρτάται από» αλλά δεν υπάρχουν στη λίστα: "
                   + ", ".join(unknown) + ". Έλεγξε την ορθογραφία.")

    c1, c2 = st.columns([3, 1])
    task = c1.selectbox("Εργασία που καθυστερεί", df["Εργασία"].tolist())
    days = c2.number_input("Καθυστέρηση (ημέρες)", min_value=1, step=1, value=5)

    affected = affected_tasks(task, df)
    shifted = [task] + affected
    new = df.copy()
    mask = new["Εργασία"].isin(shifted)
    new.loc[mask, "Ημερομηνία Έναρξης"] += pd.Timedelta(days=int(days))
    new.loc[mask, "Ημερομηνία Λήξης"] += pd.Timedelta(days=int(days))

    m1, m2, m3 = st.columns(3)
    m1.metric("Επηρεαζόμενες εργασίες (Domino)", len(affected))
    m2.metric("Μετατόπιση", f"{int(days)} ημέρες")
    old_end, new_end = df["Ημερομηνία Λήξης"].max(), new["Ημερομηνία Λήξης"].max()
    m3.metric("Λήξη έργου", f"{new_end:%d/%m/%Y}", delta=f"{(new_end - old_end).days} ημέρες",
              delta_color="inverse")

    if affected:
        st.markdown("**Αλυσίδα επιπτώσεων:** " + " → ".join([f"**{task}**"] + affected))
    else:
        st.success("Καμία άλλη εργασία δεν εξαρτάται από αυτήν: η καθυστέρηση δεν μεταδίδεται.")

    view = pd.DataFrame({
        "Εργασία": new["Εργασία"],
        "Εξαρτάται από": new["Εξαρτάται από"].fillna(""),
        "Αρχική έναρξη": df["Ημερομηνία Έναρξης"], "Αρχική λήξη": df["Ημερομηνία Λήξης"],
        "Νέα έναρξη": new["Ημερομηνία Έναρξης"], "Νέα λήξη": new["Ημερομηνία Λήξης"],
        "Μετατοπίστηκε": mask.map({True: "Ναι", False: ""}),
    })
    view = fmt_dates(view, ["Αρχική έναρξη", "Αρχική λήξη", "Νέα έναρξη", "Νέα λήξη"])
    st.dataframe(view.style.apply(
        lambda r: ["background-color: #F5A62333" if r["Μετατοπίστηκε"] else ""] * len(r), axis=1),
        hide_index=True, width="stretch")

    b1, b2 = st.columns(2)
    b1.download_button("📥 Κατέβασε το ενημερωμένο χρονοδιάγραμμα (Excel)",
                       to_excel_bytes({"Χρονοδιάγραμμα": view}), "updated_schedule.xlsx")
    if b2.button("➡️ Στείλε στο DII", type="primary"):
        rows = st.session_state.setdefault("dii_from_domino", [])
        rows[:] = [r for r in rows if r["Εργασία"] != task]
        rows.append({"Εργασία": task, "Καθυστέρηση (ημ)": int(days), "Απόκλιση (€)": 0.0,
                     "Domino (εργασίες)": len(affected), "Νέες Εργασίες (ημ)": 0, "Νέες Εργασίες (€)": 0.0})
        st.success(f"Η εργασία «{task}» προστέθηκε στο DII ({len(rows)} συνολικά). "
                   "Συμπλήρωσε εκεί κόστος και πρόσθετες εργασίες.")
        st.page_link("tools/dii.py", label="Μετάβαση στο DII →")

footer()
