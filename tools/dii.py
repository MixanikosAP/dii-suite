"""Εργαλείο 3 – Υπολογισμός του Delay Impact Index (DII)."""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from common import (CAT_COLORS, CATEGORIES, COLS_DII, footer, missing_columns, sample_dii,
                    to_excel_bytes, to_png_bytes)

NUMERIC = COLS_DII[1:]

st.title("🚧 Delay Impact Index (DII)")
st.markdown("Για κάθε καθυστέρηση ελέγχονται τέσσερις παράμετροι. Όταν μια παράμετρος ξεπερνά το όριό "
            "της ενεργοποιείται ένα **flag**. Ο DII είναι το σταθμισμένο άθροισμα των flags και καθορίζει "
            "την κατηγορία κρισιμότητας.")

# ---------------------------------------------------------------- Ρυθμίσεις
with st.sidebar:
    st.header("⚙️ Όρια ενεργοποίησης")
    T = {
        "delay": st.number_input("Καθυστέρηση χρόνου > (ημέρες)", 0, 365, 5),
        "cost": st.number_input("Απόκλιση κόστους > (€)", 0, 1_000_000, 1000, step=100),
        "domino": st.number_input("Domino effect > (εργασίες)", 0, 100, 2),
        "rw_days": st.number_input("Πρόσθετες εργασίες – χρόνος > (ημέρες)", 0, 365, 2),
        "rw_cost": st.number_input("Πρόσθετες εργασίες – κόστος > (€)", 0, 1_000_000, 500, step=100),
        "critical": st.number_input("Κρίσιμη όταν καθυστέρηση > (ημέρες)", 0, 365, 15),
    }
    with st.expander("⚖️ Συντελεστές βαρύτητας"):
        st.caption("Στην αρχική εκδοχή του δείκτη όλα τα βάρη είναι 1.")
        W = {
            "t": st.number_input("w₁ – Χρόνος", 0.0, 5.0, 1.0, 0.1),
            "c": st.number_input("w₂ – Κόστος", 0.0, 5.0, 1.0, 0.1),
            "d": st.number_input("w₃ – Domino effect", 0.0, 5.0, 1.0, 0.1),
            "r": st.number_input("w₄ – Πρόσθετες εργασίες", 0.0, 5.0, 1.0, 0.1),
        }
    defaults = T == {"delay": 5, "cost": 1000, "domino": 2, "rw_days": 2, "rw_cost": 500, "critical": 15} \
        and all(v == 1.0 for v in W.values())
    if not defaults:
        st.info("Χρησιμοποιείς διαφορετικές ρυθμίσεις από τις αρχικές του δείκτη (ανάλυση ευαισθησίας).")


def category(value):
    if value >= 3:
        return "Κρίσιμη Καθυστέρηση"
    if value >= 2:
        return "Σοβαρή Επίπτωση"
    if value >= 1:
        return "Μέτρια Επίπτωση"
    return "Χαμηλή Επίπτωση"


def compute(df):
    """Υπολογίζει flags, DII και κατηγορία για κάθε εργασία."""
    df = df[COLS_DII].copy()
    numeric = df[NUMERIC].apply(pd.to_numeric, errors="coerce")
    incomplete = numeric.isna().any(axis=1)
    df[NUMERIC] = numeric.fillna(0)

    df["f_t"] = (df["Καθυστέρηση (ημ)"] > T["delay"]).astype(int)
    df["f_c"] = (df["Απόκλιση (€)"] > T["cost"]).astype(int)
    df["f_d"] = (df["Domino (εργασίες)"] > T["domino"]).astype(int)
    df["f_r"] = ((df["Νέες Εργασίες (ημ)"] > T["rw_days"]) |
                 (df["Νέες Εργασίες (€)"] > T["rw_cost"])).astype(int)
    df["Flags"] = df[["f_t", "f_c", "f_d", "f_r"]].sum(axis=1)
    # DII = w1·ft + w2·fc + w3·fd + w4·fr
    df["DII"] = (W["t"] * df["f_t"] + W["c"] * df["f_c"] + W["d"] * df["f_d"] + W["r"] * df["f_r"]).round(2)
    df["Κατηγορία DII"] = [
        "Κρίσιμη Καθυστέρηση" if delay > T["critical"] else category(v)
        for delay, v in zip(df["Καθυστέρηση (ημ)"], df["DII"])
    ]
    df["Αιτία"] = [
        ", ".join([n for n, f in zip(["χρόνος", "κόστος", "domino", "πρόσθετες εργασίες"], flags) if f])
        + (" · καθυστέρηση > %d ημ." % T["critical"] if delay > T["critical"] else "")
        for flags, delay in zip(df[["f_t", "f_c", "f_d", "f_r"]].values, df["Καθυστέρηση (ημ)"])
    ]
    return df, incomplete


def summary(res):
    n = len(res)
    rows = [("Πλήθος εργασιών", str(n)), ("Μέσος DII", f"{res['DII'].mean():.2f}".replace(".", ","))]
    for c in CATEGORIES:
        k = int((res["Κατηγορία DII"] == c).sum())
        rows.append((c, f"{k} ({100 * k / n:.1f}%)".replace(".", ",")))
    rows.append(("Συνολική κρισιμότητα έργου (μέσος DII)", category(res["DII"].mean())))
    return pd.DataFrame(rows, columns=["Δείκτης", "Τιμή"])


def charts(res):
    counts = [int((res["Κατηγορία DII"] == c).sum()) for c in CATEGORIES]
    labels = [c.split()[0] for c in CATEGORIES]
    colors = [CAT_COLORS[c] for c in CATEGORIES]

    pie, ax = plt.subplots(figsize=(5.5, 4))
    nz = [(l, v, c) for l, v, c in zip(labels, counts, colors) if v]
    ax.pie([v for _, v, _ in nz], labels=[f"{l} ({v})" for l, v, _ in nz], colors=[c for *_, c in nz],
           autopct=lambda p: f"{p:.1f}%".replace(".", ","), startangle=90, counterclock=False,
           wedgeprops=dict(edgecolor="white", linewidth=2), textprops=dict(fontsize=10))
    ax.set_title("Κατανομή κατηγοριών DII")
    ax.axis("equal")

    bar, ax = plt.subplots(figsize=(5.5, 4))
    bars = ax.bar(labels, counts, color=colors, width=0.6)
    for b, v in zip(bars, counts):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, str(v), ha="center", va="bottom")
    ax.set_ylabel("Αριθμός εργασιών")
    ax.set_xlabel("Κατηγορία DII")
    ax.set_ylim(0, max(counts + [1]) * 1.2)
    ax.set_title("Αριθμός εργασιών ανά κατηγορία DII")
    return pie, bar


# ---------------------------------------------------------------- Εισαγωγή δεδομένων
from_domino = st.session_state.get("dii_from_domino", [])
options = ["📎 Παράδειγμα (Πίνακας 4 της εργασίας)", "📎 Εκτεταμένο παράδειγμα",
           "📂 Δικό μου αρχείο Excel", "✏️ Συμπλήρωση πίνακα"]
if from_domino:
    options.insert(0, f"🔗 Από το Domino Effect ({len(from_domino)})")
source = st.radio("Δεδομένα", options, horizontal=True)

data = None
if source.startswith("🔗"):
    st.caption("Οι καθυστερήσεις που έστειλες από το Domino Effect. Συμπλήρωσε κόστος και πρόσθετες εργασίες.")
    data = st.data_editor(pd.DataFrame(from_domino, columns=COLS_DII), num_rows="dynamic",
                          hide_index=True, width="stretch", key="ed_domino")
    if st.button("🗑️ Άδειασε τη λίστα από το Domino"):
        st.session_state["dii_from_domino"] = []
        st.rerun()
elif source.startswith("📎 Παράδειγμα"):
    data = sample_dii()
elif source.startswith("📎 Εκτεταμένο"):
    data = sample_dii(extended=True)
    st.caption("Δοκιμαστικά δεδομένα για εξοικείωση με όλες τις κατηγορίες. Δεν είναι δεδομένα της εργασίας.")
elif source.startswith("📂"):
    uploaded = st.file_uploader("Ανέβασε αρχείο Excel (.xlsx)", type=["xlsx"])
    st.caption("Απαιτούμενες στήλες: " + " · ".join(COLS_DII))
    st.download_button("⬇️ Κατέβασε πρότυπο Excel", to_excel_bytes({"Δεδομένα": sample_dii()}), "DII_πρότυπο.xlsx")
    if uploaded:
        try:
            data = pd.read_excel(uploaded)
            miss = missing_columns(data, COLS_DII)
            if miss:
                st.error("Λείπουν οι στήλες: " + ", ".join(miss))
                data = None
        except Exception as e:
            st.error(f"Δεν ήταν δυνατή η ανάγνωση του αρχείου: {e}")
else:
    st.caption("Πρόσθεσε γραμμές με το «+» κάτω από τον πίνακα.")
    empty = pd.DataFrame([{"Εργασία": "", "Καθυστέρηση (ημ)": 0, "Απόκλιση (€)": 0.0, "Domino (εργασίες)": 0,
                           "Νέες Εργασίες (ημ)": 0, "Νέες Εργασίες (€)": 0.0}])
    data = st.data_editor(empty, num_rows="dynamic", hide_index=True, width="stretch", key="ed_manual")
    data = data[data["Εργασία"].astype(str).str.strip() != ""]

# ---------------------------------------------------------------- Αποτελέσματα
if data is not None and len(data):
    res, incomplete = compute(data)
    if incomplete.any():
        st.warning("Κενές ή μη αριθμητικές τιμές μετρήθηκαν ως 0 στις εργασίες: "
                   + ", ".join(res.loc[incomplete, "Εργασία"].astype(str)))

    st.subheader("Αποτελέσματα ανά εργασία")
    show = res[COLS_DII + ["Flags", "DII", "Κατηγορία DII", "Αιτία"]]
    st.dataframe(show.style.apply(
        lambda r: [f"background-color: {CAT_COLORS[r['Κατηγορία DII']]}2B"] * len(r), axis=1),
        hide_index=True, width="stretch")

    st.subheader("Σύνοψη έργου")
    summ = summary(res)
    k = st.columns(4)
    for col, c in zip(k, CATEGORIES):
        col.metric(c, int((res["Κατηγορία DII"] == c).sum()))
    st.table(summ.set_index("Δείκτης"))

    st.subheader("Γραφήματα")
    pie, bar = charts(res)
    g1, g2 = st.columns(2)
    with g1:
        st.pyplot(pie)
        st.download_button("🖼️ Πίτα (PNG)", to_png_bytes(pie), "DII_pie.png", "image/png")
    with g2:
        st.pyplot(bar)
        st.download_button("🖼️ Ραβδόγραμμα (PNG)", to_png_bytes(bar), "DII_bar.png", "image/png")

    settings = pd.DataFrame({"Παράμετρος": list(T) + ["w1", "w2", "w3", "w4"],
                             "Τιμή": list(T.values()) + list(W.values())})
    st.download_button("📥 Κατέβασε όλα τα αποτελέσματα (Excel)",
                       to_excel_bytes({"Αποτελέσματα": show, "Σύνοψη": summ, "Ρυθμίσεις": settings}),
                       "DII_αποτελέσματα.xlsx", type="primary")
elif data is not None:
    st.info("Πρόσθεσε τουλάχιστον μία εργασία για να υπολογιστεί ο δείκτης.")

footer()
