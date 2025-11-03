import re
from pathlib import Path
import json
import streamlit as st

# Paths to source files
DESCRIPTION_PATH = Path("Description.txt")
DESCRIPTION_TH_PATH = Path("Description_th.txt")
TEST_PATH = Path("test.txt")
TH_Q_PATH = Path("questions_th.json")

# Supported UI translations
I18N = {
    "th": {
        "app_title": "RAADS-R แบบทดสอบสำหรับผู้ใหญ่",
        "choose_lang": "เลือกภาษา",
        "start_test": "เริ่มทำแบบทดสอบ",
        "options": [
            "จริงตั้งแต่เด็กจนถึงปัจจุบัน",
            "จริงเฉพาะปัจจุบัน",
            "จริงเฉพาะเมื่ออายุน้อยกว่า 16 ปี",
            "ไม่จริง",
        ],
        "submit": "ส่งคำตอบและคำนวณคะแนน",
        "result_title": "ผลการทดสอบ",
        "total_score": "คะแนนรวม",
        "interpretation": "สรุป",
        "recommendation": "คำแนะนำ",
        "disclaimer": "หมายเหตุ: RAADS-R เป็นเครื่องมือคัดกรองเบื้องต้น ไม่ใช่การวินิจฉัย",
        "normative_label": "หมายเลขข้อที่กลับด้านคะแนน (เช่น 1,6,11)",
        "details_title": "สรุปแบบทดสอบ (ฉบับย่อ)",
        "load_error": "ไม่สามารถอ่านไฟล์ กรุณาตรวจสอบเส้นทาง",
        "no_questions": "ไม่พบคำถามใน test.txt",
    },
    "en": {
        "app_title": "RAADS-R Screening for Adults",
        "choose_lang": "Choose language",
        "start_test": "Start the test",
        "options": [
            "True now and when I was young",
            "True now only",
            "True only when I was younger than 16",
            "Never true",
        ],
        "submit": "Submit answers and compute score",
        "result_title": "Test Result",
        "total_score": "Total Score",
        "interpretation": "Summary",
        "recommendation": "Recommendations",
        "disclaimer": "Note: RAADS-R is a screening tool, not a diagnosis.",
        "normative_label": "Normative items (reversed scoring), e.g. 1,6,11",
        "details_title": "Test Summary (Concise)",
        "load_error": "Failed to read files. Please verify paths.",
    },
}
# ค่าเริ่มต้น: ข้อกลับด้านคะแนน (ตามที่ผู้ใช้ให้มา)
DEFAULT_NORMATIVE = {1, 6, 11, 18, 23, 33, 37, 43, 47, 48, 53, 58, 62, 68, 72, 77}
DEFAULT_NORMATIVE_STR = ",".join(str(n) for n in sorted(DEFAULT_NORMATIVE))


def parse_questions_from_test(file_path: Path):
    lines = file_path.read_text(encoding="utf-8").splitlines()
    questions = []
    i = 0
    q_pattern = re.compile(r"^\s*(\d{1,3})\.\s*(.*)$")

    while i < len(lines):
        m = q_pattern.match(lines[i])
        if m:
            q_id = int(m.group(1))
            q_text = m.group(2).strip()
            i += 5
            questions.append({"id": q_id, "text": q_text})
        else:
            i += 1
        if questions and questions[-1]["id"] >= 80:
            break

    return [q for q in questions if 1 <= q["id"] <= 80]


def parse_normative_input(raw: str):
    if not raw:
        return set()
    parts = re.split(r"[,\s]+", raw.strip())
    nums = set()
    for p in parts:
        if p.isdigit():
            nums.add(int(p))
    return {n for n in nums if 1 <= n <= 80}


def score_item(choice_index: int, is_normative: bool):
    if choice_index is None:
        return 0
    base = [3, 2, 1, 0]
    if is_normative:
        base = list(reversed(base))
    return base[choice_index]


def interpret_score(total: int, lang: str):
    if lang == "th":
        if total < 25:
            return "ไม่เข้าเกณฑ์ออทิสติก"
        elif total < 50:
            return "มีลักษณะบ้าง แต่ไม่น่าจะเป็น"
        elif total < 65:
            return "มีบางลักษณะ โดยรวมยังไม่ถึงเกณฑ์"
        elif total < 90:
            return "ถึงเกณฑ์ขั้นต่ำ (≥65)"
        elif total < 130:
            return "มีสัญญาณค่อนข้างชัดเจน"
        elif total < 160:
            return "ระดับเฉลี่ยกลุ่มออทิสติก"
        else:
            return "หลักฐานเข้มข้นมาก"
    else:
        if total < 25:
            return "Not autistic"
        elif total < 50:
            return "Some traits; likely not autistic"
        elif total < 65:
            return "Traits present; below threshold"
        elif total < 90:
            return "Meets minimum (≥65)"
        elif total < 130:
            return "Strong indications"
        elif total < 160:
            return "Around autistic mean"
        else:
            return "Very strong evidence"


def recommendations_text(lang: str):
    if lang == "th":
        return "หากถึงเกณฑ์ พิจารณาปรึกษาผู้เชี่ยวชาญ หรือทำแบบทดสอบ AQ/EQ/CAT-Q เพิ่ม"
    else:
        return "If at/above threshold, consider professional assessment or AQ/EQ/CAT-Q"


def summary_text(lang: str):
    if lang == "th":
        if DESCRIPTION_TH_PATH.exists():
            try:
                return DESCRIPTION_TH_PATH.read_text(encoding="utf-8")
            except Exception:
                pass
        # fallback short Thai summary
        return (
            "RAADS-R: 80 ข้อ, คำตอบ 4 แบบ, คะแนน 0–240; เกณฑ์ ≥65\n"
            "ข้อนอร์มาทีฟ 17 ข้อกลับด้านคะแนน; มี 4 มิติ (ภาษา/สังคม/ประสาทสัมผัส/ความสนใจจำกัด)\n"
            "เป็นการคัดกรองเบื้องต้น ไม่ใช่การวินิจฉัย"
        )
    else:
        # concise English summary
        return (
            "RAADS-R: 80 items, 4 choices, total 0–240; threshold ≥65\n"
            "17 normative items reverse scoring; 4 subscales (Language/Social/Sensory–motor/Circumscribed interests)\n"
            "Screening tool, not a diagnosis"
        )


# Load translations
TH_QUESTIONS = {}
if TH_Q_PATH.exists():
    try:
        TH_QUESTIONS = json.loads(TH_Q_PATH.read_text(encoding="utf-8"))
    except Exception:
        TH_QUESTIONS = {}

# Sidebar: language selection and normative config
st.set_page_config(page_title="RAADS-R Screening", layout="centered")
lang = st.sidebar.selectbox("Language / ภาษา", options=["ไทย", "English"], index=0)
lang_key = "th" if lang == "ไทย" else "en"
t = I18N[lang_key]

st.title(t["app_title"])

normative_items = DEFAULT_NORMATIVE

# Load files
try:
    description_text = DESCRIPTION_PATH.read_text(encoding="utf-8")
    questions = parse_questions_from_test(TEST_PATH)
except Exception:
    st.error(t["load_error"])
    st.stop()

if not questions:
    st.warning(t["no_questions"])
    st.stop()

# Show concise summary per language
with st.expander(t["details_title"], expanded=False):
    st.text(summary_text(lang_key))

# Test form
st.header(t["start_test"])
opt_labels = t["options"]

if "answers" not in st.session_state:
    st.session_state.answers = {}

with st.form("raads_form", clear_on_submit=False):
    for q in questions:
        q_text = TH_QUESTIONS.get(str(q["id"])) if lang_key == "th" else q["text"]
        label = f"{q['id']}.{q_text if q_text else q['text']}"
        st.session_state.answers[q["id"]] = st.radio(
            label,
            options=opt_labels,
            index=st.session_state.answers.get(q["id"], None),
            key=f"q_{q['id']}",
        )
    submitted = st.form_submit_button(t["submit"])

if submitted:
    total = 0
    for q in questions:
        selected_label = st.session_state.get(f"q_{q['id']}", None)
        choice_index = opt_labels.index(selected_label) if selected_label in opt_labels else None
        is_normative = q["id"] in normative_items
        total += score_item(choice_index, is_normative)

    st.success(t["result_title"])
    st.metric(t["total_score"], total)
    st.write(f"• {t['interpretation']}: {interpret_score(total, lang_key)}")
    st.write(f"• {t['recommendation']}: {recommendations_text(lang_key)}")
    st.info(t["disclaimer"])