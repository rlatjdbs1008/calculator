import streamlit as st
import math

# ── 페이지 설정 ────────────────────────────────────────────────────
st.set_page_config(page_title="공학용 계산기", page_icon="🧮", layout="centered")

# ── 세션 상태 초기화 ───────────────────────────────────────────────
for k, v in {
    "display": "0",
    "expr": "",
    "op": None,
    "prev": None,
    "fresh": False,
    "mode": "DEG",
    "inv": False,
    "error": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── 유틸 함수 ──────────────────────────────────────────────────────
def to_rad(x: float) -> float:
    return x * math.pi / 180 if st.session_state.mode == "DEG" else x


def from_rad(x: float) -> float:
    return x * 180 / math.pi if st.session_state.mode == "DEG" else x


def fmt(v) -> str:
    if not math.isfinite(v):
        return "∞" if v > 0 else ("오류" if math.isnan(v) else "-∞")
    if abs(v) >= 1e14 or (abs(v) < 1e-10 and v != 0):
        return f"{v:.6e}"
    return f"{v:.10g}"


def factorial(n: int) -> float:
    n = round(n)
    if n < 0:
        return float("nan")
    if n > 170:
        return float("inf")
    r = 1
    for i in range(2, n + 1):
        r *= i
    return float(r)


def set_error(msg: str):
    st.session_state.error = msg


def clear_error():
    st.session_state.error = ""


# ── 버튼 핸들러 ───────────────────────────────────────────────────
def press(label: str):
    s = st.session_state
    clear_error()
    try:
        v = float(s.display)
    except ValueError:
        v = 0.0

    inv_map = {
        "sin": "sin⁻¹", "cos": "cos⁻¹", "tan": "tan⁻¹",
        "ln": "eˣ", "log": "10ˣ", "sqrtx": "x²", "xpowy": "xrty",
    }

    # 숫자 입력
    if label in "0123456789":
        if s.display == "0" or s.fresh:
            s.display = label
            s.fresh = False
        else:
            if len(s.display) < 16:
                s.display += label
        return

    if label == ".":
        if s.fresh:
            s.display = "0."
            s.fresh = False
        elif "." not in s.display:
            s.display += "."
        return

    if label == "pi":
        s.display = fmt(math.pi)
        s.fresh = True
        return

    if label == "euler":
        s.display = fmt(math.e)
        s.fresh = True
        return

    if label == "AC":
        s.display = "0"; s.expr = ""; s.op = None; s.prev = None; s.fresh = False
        return

    if label == "DEL":
        if len(s.display) > 1 and not s.fresh:
            s.display = s.display[:-1]
        else:
            s.display = "0"
        return

    if label == "pm":
        s.display = fmt(-v); s.fresh = True; return

    if label == "pct":
        s.display = fmt(v / 100); s.fresh = True; return

    # 단항 함수 매핑 (label: function)
    unary = {
        "sin":    lambda x: math.sin(to_rad(x)),
        "cos":    lambda x: math.cos(to_rad(x)),
        "tan":    lambda x: math.tan(to_rad(x)),
        "asin":   lambda x: from_rad(math.asin(x)),
        "acos":   lambda x: from_rad(math.acos(x)),
        "atan":   lambda x: from_rad(math.atan(x)),
        "ln":     lambda x: math.log(x),
        "log10":  lambda x: math.log10(x),
        "exp":    lambda x: math.exp(x),
        "pow10":  lambda x: 10 ** x,
        "sqrtx":  lambda x: math.sqrt(x),
        "sq":     lambda x: x ** 2,
        "cube":   lambda x: x ** 3,
        "inv":    lambda x: 1 / x,
        "fact":   lambda x: factorial(x),
        "sinh":   lambda x: math.sinh(x),
        "cosh":   lambda x: math.cosh(x),
        "tanh":   lambda x: math.tanh(x),
        "absx":   lambda x: abs(x),
        "ceil":   lambda x: float(math.ceil(x)),
        "floor":  lambda x: float(math.floor(x)),
    }

    if label in unary:
        try:
            r = unary[label](v)
            if math.isnan(r):
                set_error("정의역 오류")
                return
            s.expr = f"f({s.display})"
            s.display = fmt(r)
            s.fresh = True
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            set_error(f"오류: {exc}")
        return

    binary_ops = {"div", "mul", "sub", "add", "mod", "xpowy", "xrty", "ee", "logy"}
    if label in binary_ops:
        s.prev = v
        s.op = label
        symbol_map = {
            "div":"÷","mul":"×","sub":"−","add":"+",
            "mod":"mod","xpowy":"xʸ","xrty":"ˣ√y","ee":"EE","logy":"logᵧ"
        }
        s.expr = f"{s.display}  {symbol_map.get(label, label)}"
        s.fresh = True
        return

    if label == "eq":
        if s.op is None or s.prev is None:
            return
        a, b = s.prev, v
        op = s.op
        symbol_map = {
            "div":"÷","mul":"×","sub":"−","add":"+",
            "mod":"mod","xpowy":"xʸ","xrty":"ˣ√y","ee":"EE","logy":"logᵧ"
        }
        try:
            if op == "div":
                if b == 0: set_error("0으로 나눌 수 없습니다"); return
                r = a / b
            elif op == "mul": r = a * b
            elif op == "sub": r = a - b
            elif op == "add": r = a + b
            elif op == "mod":
                if b == 0: set_error("모듈러 제수가 0입니다"); return
                r = a % b
            elif op == "xpowy": r = a ** b
            elif op == "xrty": r = b ** (1 / a)
            elif op == "ee": r = a * (10 ** b)
            elif op == "logy":
                if a <= 0 or b <= 0 or b == 1: set_error("로그 정의역 오류"); return
                r = math.log(a, b)
            else:
                set_error("알 수 없는 연산"); return
        except (OverflowError, ValueError, ZeroDivisionError) as exc:
            set_error(f"오류: {exc}"); return

        s.expr = f"{s.prev}  {symbol_map.get(op, op)}  {v}  ="
        s.display = fmt(r)
        s.op = None; s.prev = None; s.fresh = True
        return

    if label == "mode_toggle":
        s.mode = "RAD" if s.mode == "DEG" else "DEG"
        return

    if label == "inv_toggle":
        s.inv = not s.inv
        return


# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');

.stApp { background: #111118; }
section[data-testid="stMain"] > div { padding-top: 1.5rem; }

.calc-display {
    background: #1c1c2a;
    border: 1px solid #ffffff12;
    border-radius: 14px;
    padding: 16px 20px 12px;
    margin-bottom: 12px;
}
.calc-expr {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px; color: #555; text-align: right;
    min-height: 18px; overflow: hidden; white-space: nowrap;
    text-overflow: ellipsis;
}
.calc-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 36px; font-weight: 600; color: #e8e8ff;
    text-align: right; overflow: hidden; white-space: nowrap;
}
.calc-err {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px; color: #ff6b6b; text-align: right; min-height: 16px;
}
.mode-badge {
    display:inline-block; font-family:'JetBrains Mono',monospace;
    font-size:11px; padding:2px 8px; border-radius:4px; margin-right:4px;
    background:#1e3a5f; color:#7ec8ff; border:1px solid #7ec8ff44;
}
.inv-badge {
    display:inline-block; font-family:'JetBrains Mono',monospace;
    font-size:11px; padding:2px 8px; border-radius:4px;
    background:#3a1e5f; color:#c87eff; border:1px solid #c87eff44;
}

div[data-testid="stButton"] > button {
    width: 100% !important;
    min-height: 50px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    border-radius: 8px !important;
    border: 1px solid #ffffff15 !important;
    background: #1e1e2e !important;
    color: #c8c8e8 !important;
    transition: all 0.1s !important;
    padding: 4px 2px !important;
    white-space: nowrap !important;
}
div[data-testid="stButton"] > button:hover {
    background: #2a2a42 !important;
    border-color: #ffffff30 !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ── 디스플레이 ────────────────────────────────────────────────────
s = st.session_state
mode_html = f'<span class="mode-badge">{s.mode}</span>'
if s.inv:
    mode_html += '<span class="inv-badge">INV ON</span>'

st.markdown(f"""
<div class="calc-display">
  <div style="margin-bottom:6px">{mode_html}</div>
  <div class="calc-expr">{s.expr or "&nbsp;"}</div>
  <div class="calc-val">{s.display}</div>
  <div class="calc-err">{s.error or "&nbsp;"}</div>
</div>
""", unsafe_allow_html=True)

# ── 버튼 레이아웃 ─────────────────────────────────────────────────
# (내부 label, 표시 텍스트)
ROWS = [
    [("mode_toggle","DEG/RAD"), ("inv_toggle","INV"),  ("AC","AC"),     ("DEL","⌫"),      ("div","÷")],
    [("sin",  "sin"),           ("cos",  "cos"),       ("tan",  "tan"), ("ln","ln"),       ("mul","×")],
    [("asin", "sin⁻¹"),         ("acos", "cos⁻¹"),    ("atan", "tan⁻¹"),("log10","log"), ("sub","−")],
    [("xpowy","xʸ"),            ("sqrtx","√x"),        ("xrty", "ˣ√y"), ("sq","x²"),      ("add","+")],
    [("cube", "x³"),            ("fact", "x!"),        ("inv",  "1/x"), ("mod","mod"),     ("eq","=")],
    [("pi",   "π"),             ("euler","e"),         ("exp",  "eˣ"),  ("pow10","10ˣ"),  ("ee","EE")],
    [("absx","|x|"),            ("ceil","⌈x⌉"),        ("floor","⌊x⌋"), ("logy","logᵧ"),  ("pct","%")],
    [("sinh", "sinh"),          ("cosh", "cosh"),      ("tanh", "tanh"),("pm","±"),        ("7","7")],
    [("8",    "8"),             ("9",    "9"),         ("4",    "4"),   ("5","5"),         ("6","6")],
    [("1",    "1"),             ("2",    "2"),         ("3",    "3"),   ("0","0"),         (".",".")],
]

for row in ROWS:
    cols = st.columns(len(row))
    for col, (lbl, disp_txt) in zip(cols, row):
        with col:
            if st.button(disp_txt, key=f"k_{lbl}_{disp_txt}"):
                press(lbl)
                st.rerun()
