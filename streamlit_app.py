"""DII Suite – Σύστημα αξιολόγησης καθυστερήσεων σε εργοτάξιο παθητικού κτιρίου.

Εκκίνηση:  streamlit run streamlit_app.py
"""
import streamlit as st

from common import THESIS, apply_style, footer

st.set_page_config(page_title="DII Suite – Αξιολόγηση Καθυστερήσεων", page_icon="🏗️", layout="wide")
with st.sidebar:
    presentation = st.toggle("🎥 Λειτουργία προβολής", key="presentation",
                             help="Μεγαλύτερα γράμματα και αριθμοί για προβολή σε projector.")
apply_style(presentation)


def home():
    st.title("🏗️ DII Suite")
    st.subheader("Αξιολόγηση καθυστερήσεων σε εργοτάξιο παθητικού κτιρίου")
    st.markdown(
        "Στα παθητικά κτίρια μια μικρή καθυστέρηση σε κρίσιμη εργασία (π.χ. κουφώματα ή αεροστεγανότητα) "
        "μεταδίδεται στις επόμενες φάσεις και επιβαρύνει χρόνο, κόστος και συντονισμό. Οι κλασικοί δείκτες "
        "(SPI, CPI) δεν αποτυπώνουν αυτή την αλυσιδωτή επίδραση. Η εφαρμογή συνδυάζει τρία απλά εργαλεία "
        "που οδηγούν από την εικόνα του εργοταξίου στην αξιολόγηση της κρισιμότητας κάθε καθυστέρησης "
        "μέσω του **Delay Impact Index (DII)**."
    )

    st.markdown("#### Η ροή εργασίας")
    c1, c2, c3 = st.columns(3)
    cards = [
        (c1, "1 · Ενεργές εργασίες", "Τι γίνεται στο εργοτάξιο μια συγκεκριμένη ημέρα; "
             "Ποια συνεργεία δουλεύουν ταυτόχρονα; Χρονοδιάγραμμα Gantt.", "tools/energes.py"),
        (c2, "2 · Domino Effect", "Αν μια εργασία καθυστερήσει, ποιες άλλες επηρεάζονται και πόσο "
             "μετατοπίζονται; Υπολογίζει το πλήθος των επηρεαζόμενων εργασιών.", "tools/domino.py"),
        (c3, "3 · Δείκτης DII", "Πόσο σοβαρή είναι κάθε καθυστέρηση; Συνδυάζει χρόνο, κόστος, domino "
             "και πρόσθετες εργασίες σε μία κατηγορία κρισιμότητας.", "tools/dii.py"),
    ]
    for col, title, text, page in cards:
        with col:
            st.markdown(f"<div class='step-card'><h4>{title}</h4><p>{text}</p></div>", unsafe_allow_html=True)
            st.page_link(page, label="Άνοιγμα →")

    st.markdown("#### Ο δείκτης DII")
    left, right = st.columns([3, 2])
    with left:
        st.latex(r"DII = w_1 f_t + w_2 f_c + w_3 f_d + w_4 f_r")
        st.markdown(
            "όπου $f_t, f_c, f_d, f_r \\in \\{0, 1\\}$ τα flags χρόνου, κόστους, domino effect και πρόσθετων "
            "εργασιών (1 όταν η παράμετρος ξεπερνά το όριό της) και $w_1 \\dots w_4$ οι συντελεστές βαρύτητας. "
            "Στην αρχική εκδοχή όλα τα βάρη είναι 1, οπότε ο DII ισούται με το πλήθος των ενεργών flags."
        )
    with right:
        st.markdown(
            "| DII | Κατηγορία |\n|---|---|\n"
            "| 0 | 🟢 Χαμηλή επίπτωση |\n| 1 | 🟡 Μέτρια επίπτωση |\n| 2 | 🟠 Σοβαρή επίπτωση |\n"
            "| ≥ 3 ή καθυστέρηση > 15 ημ. | 🔴 Κρίσιμη καθυστέρηση |"
        )

    with st.expander("ℹ️ Πώς να τη χρησιμοποιήσω"):
        st.markdown(
            "1. Κάθε εργαλείο έχει έτοιμο **παράδειγμα**, ώστε να το δοκιμάσεις αμέσως χωρίς δικό σου αρχείο.\n"
            "2. Για δικά σου δεδομένα, κατέβασε το παράδειγμα σε Excel, συμπλήρωσέ το και ανέβασέ το.\n"
            "3. Στο **Domino Effect**, μετά τον υπολογισμό, πάτα «Στείλε στο DII» για να μεταφερθεί η "
            "καθυστέρηση και το πλήθος των επηρεαζόμενων εργασιών στο εργαλείο DII.\n"
            "4. Στο **DII**, τα όρια και τα βάρη ρυθμίζονται από την πλευρική στήλη. Τα αποτελέσματα, οι "
            "πίνακες και τα γραφήματα κατεβαίνουν σε Excel και PNG."
        )

    with st.expander("🎓 Σχετικά με την εργασία"):
        st.markdown(
            f"**{THESIS['title']}**  \n{THESIS['author']}  \nΔιπλωματική εργασία · {THESIS['school']}  \n"
            f"Επιβλέπων: {THESIS['supervisor']} · {THESIS['year']}  \n"
            f"Πηγαίος κώδικας: [{THESIS['github']}]({THESIS['github']})"
        )
    footer()


pages = [
    st.Page(home, title="Αρχική", icon="🏠", default=True),
    st.Page("tools/energes.py", title="1 · Ενεργές εργασίες", icon="📅"),
    st.Page("tools/domino.py", title="2 · Domino Effect", icon="⏳"),
    st.Page("tools/dii.py", title="3 · Δείκτης DII", icon="🚧"),
]
st.navigation(pages).run()
