import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import random
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="การเดินเงินหุ้น (เวอร์ชันเสริม)", page_icon="📈")

st.title("📈 การเดินเงินหุ้น (พุธ=ซื้อ, คอ=ขาย) – เวอร์ชันเสริม")
st.markdown("สุ่มซื้อ/ขาย, กรอกผลเอง, ป้องกันเด้งด้วย session_state + เพิ่ม **Undo / ล็อก Pattern / Export-Import CSV**")

# ===================== Session Init =====================
defaults = {
    "results": [],
    "balance": None,
    "bet_amount": None,
    "loss_streak_amount": 0,
    "patterns": [],
    "locked_patterns": False,
    "inputs_snapshot": {},
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===================== Sidebar Controls =====================
st.sidebar.header("⚙️ การตั้งค่า")
locked = st.sidebar.checkbox("🔒 ล็อก Pattern (ไม่สุ่มใหม่เมื่อเปลี่ยนอินพุต)", value=st.session_state.locked_patterns)
st.session_state.locked_patterns = locked

if st.sidebar.button("🎲 สุ่ม Pattern ใหม่", use_container_width=True):
    st.session_state.patterns = []  # จะถูกสร้างใหม่ด้านล่างตาม num_trades

if st.sidebar.button("🧹 ล้างผล (Clear Results)", use_container_width=True):
    st.session_state.results = []
    st.session_state.balance = None
    st.session_state.bet_amount = None
    st.session_state.loss_streak_amount = 0

# ===================== Inputs =====================
capital = st.number_input("💰 เงินทุนเริ่มต้น (บาท)", min_value=10.0, value=1000.0, step=10.0)
num_trades = st.number_input("🔢 จำนวนไม้ที่ต้องการจำลอง", min_value=1, value=5, step=1)
target_profit = st.number_input("🎯 กำไรที่ต้องการต่อรอบ (บาท)", min_value=0.1, value=1.0, step=0.1)
odds = st.number_input("⚖️ อัตราจ่าย (1.0 = กำไรเท่าทุน)", min_value=0.1, value=1.0, step=0.1)
first_bet = st.number_input("💵 เงินเดิมพันไม้แรก (บาท)", min_value=0.1, value=30.0, step=1.0)

# เก็บ snapshot ของอินพุตเพื่อใช้รีคอมพิวต์ (โดยเฉพาะตอน Undo / Import)
st.session_state.inputs_snapshot = dict(
    capital=capital, num_trades=num_trades,
    target_profit=target_profit, odds=odds, first_bet=first_bet
)

# ===================== Maximum Trades Calc =====================
max_bet_amount = first_bet
loss_streak_amount_tmp = 0
temp_capital = capital
max_trades_possible = 0

while temp_capital >= max_bet_amount and max_trades_possible < 100000:
    temp_capital -= max_bet_amount
    loss_streak_amount_tmp += max_bet_amount
    max_trades_possible += 1
    max_bet_amount = math.ceil((loss_streak_amount_tmp + target_profit) / odds) if odds > 0 else float("inf")

st.info(f"💡 ถ้าแพ้ติดกันทุกไม้ จะเล่นได้สูงสุด **{max_trades_possible} ไม้** ก่อนที่ทุนจะหมด")

# ===================== Reset Button =====================
col_reset, col_lock = st.columns([1,1])
with col_reset:
    if st.button("🔄 เริ่มใหม่ (Reset State)"):
        st.session_state.results = []
        st.session_state.balance = capital
        st.session_state.bet_amount = first_bet
        st.session_state.loss_streak_amount = 0
        if not st.session_state.locked_patterns:
            st.session_state.patterns = [random.choice(["พุธ", "คอ"]) for _ in range(num_trades)]

with col_lock:
    st.write(" ")  # spacer
    st.caption("หากล็อก Pattern ไว้ จะไม่สุ่มใหม่เมื่อปรับอินพุต")

# ===================== Pattern Bootstrap =====================
# ถ้ายังไม่มี pattern: สร้างตาม num_trades เว้นแต่ล็อกไว้และมีอยู่แล้ว
if not st.session_state.patterns or (not st.session_state.locked_patterns and len(st.session_state.patterns) != num_trades):
    st.session_state.patterns = [random.choice(["พุธ", "คอ"]) for _ in range(num_trades)]
elif st.session_state.locked_patterns and len(st.session_state.patterns) < num_trades:
    # ถ้าล็อกไว้แล้วเพิ่มจำนวนไม้ ให้เติมต่อจากรายการเดิม
    need = num_trades - len(st.session_state.patterns)
    if need > 0:
        st.session_state.patterns += [random.choice(["พุธ", "คอ"]) for _ in range(need)]
elif st.session_state.locked_patterns and len(st.session_state.patterns) > num_trades:
    # ถ้าล็อกแล้วลดจำนวนไม้ ให้ตัดให้พอดี
    st.session_state.patterns = st.session_state.patterns[:num_trades]

# ===================== Initialize Running State =====================
if st.session_state.balance is None:
    st.session_state.balance = capital
if st.session_state.bet_amount is None:
    st.session_state.bet_amount = first_bet

# ===================== Helper: Recompute from results =====================
def recompute_state_from_results(results):
    bal = capital
    bet = first_bet
    loss_sum = 0
    recomputed_rows = []
    for row in results:
        res = row.get("ผลลัพธ์", "-")
        patt = row.get("Pattern", "พุธ")
        if res == "ชนะ":
            profit = bet * odds
            bal += profit
            loss_sum = 0
            bet = first_bet
        elif res == "แพ้":
            bal -= bet
            loss_sum += bet
            bet = math.ceil((loss_sum + target_profit) / odds) if odds > 0 else bet
        recomputed_rows.append({
            "ไม้": row.get("ไม้"),
            "Pattern": patt,
            "ผลลัพธ์": res,
            "เงินเดิมพัน": bet,
            "พอร์ต": round(bal, 2)
        })
    return bal, bet, loss_sum, recomputed_rows

# ===================== Import / Export =====================
st.subheader("📥📤 นำเข้า / ส่งออก")
exp_col, imp_col = st.columns(2)

with exp_col:
    if st.session_state.results:
        export_df = pd.DataFrame(st.session_state.results)
        csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="⬇️ ดาวน์โหลดผลลัพธ์ (CSV)",
            data=csv_bytes,
            file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.caption("ยังไม่มีผลลัพธ์ให้ดาวน์โหลด")

with imp_col:
    uploaded = st.file_uploader("อัปโหลด CSV เพื่อโหลดผล", type=["csv"])
    if uploaded is not None:
        try:
            df_imp = pd.read_csv(uploaded)
            required_cols = {"ไม้", "Pattern", "ผลลัพธ์"}
            if not required_cols.issubset(set(df_imp.columns)):
                st.error("ไฟล์ต้องมีคอลัมน์: ไม้, Pattern, ผลลัพธ์")
            else:
                # จัดเรียงตาม 'ไม้' และสร้าง list of dict
                df_imp = df_imp.sort_values(by="ไม้").reset_index(drop=True)
                loaded = df_imp[["ไม้", "Pattern", "ผลลัพธ์"]].to_dict(orient="records")
                bal, bet, loss_sum, recomputed = recompute_state_from_results(loaded)
                st.session_state.results = recomputed
                st.session_state.balance = bal
                st.session_state.bet_amount = bet
                st.session_state.loss_streak_amount = loss_sum
                # ถ้าล็อก pattern ให้ใช้จากไฟล์ที่นำเข้า
                st.session_state.patterns = df_imp["Pattern"].tolist() + st.session_state.patterns[len(df_imp):]
                st.success("นำเข้าผลลัพธ์จาก CSV สำเร็จ ✅")
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ได้: {e}")

# ===================== Results Input Loop =====================
st.subheader("🧮 กรอกผลลัพธ์ทีละไม้")
for trade in range(1, int(num_trades) + 1):
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])
    col1.write(f"ไม้ {trade}")
    col2.write(f"({st.session_state.patterns[trade-1]})")
    prior = st.session_state.results[trade-1]["ผลลัพธ์"] if len(st.session_state.results) >= trade else "-"
    result = col3.selectbox("ผลลัพธ์", ["-", "ชนะ", "แพ้"], key=f"res_{trade}", index=["-","ชนะ","แพ้"].index(prior) if prior in ["-","ชนะ","แพ้"] else 0)

    # บันทึกเฉพาะครั้งแรกที่เลือกผลสำหรับไม้ถัดไป
    if result != "-" and trade == len(st.session_state.results) + 1:
        # apply result
        if result == "ชนะ":
            profit = st.session_state.bet_amount * odds
            st.session_state.balance += profit
            st.session_state.loss_streak_amount = 0
            st.session_state.bet_amount = first_bet
        elif result == "แพ้":
            st.session_state.balance -= st.session_state.bet_amount
            st.session_state.loss_streak_amount += st.session_state.bet_amount
            st.session_state.bet_amount = math.ceil((st.session_state.loss_streak_amount + target_profit) / odds) if odds > 0 else st.session_state.bet_amount

        st.session_state.results.append({
            "ไม้": trade,
            "Pattern": st.session_state.patterns[trade-1],
            "ผลลัพธ์": result,
            "เงินเดิมพัน": st.session_state.bet_amount,
            "พอร์ต": round(st.session_state.balance, 2)
        })

# ===================== Undo =====================
st.subheader("↩️ ย้อนกลับ (Undo)")
if st.button("ย้อนกลับ 1 ไม้"):
    if st.session_state.results:
        # ตัดรายการสุดท้ายออก แล้วคำนวณสถานะใหม่ทั้งหมด
        trimmed = st.session_state.results[:-1]
        bal, bet, loss_sum, recomputed = recompute_state_from_results(trimmed)
        st.session_state.results = recomputed
        st.session_state.balance = bal
        st.session_state.bet_amount = bet
        st.session_state.loss_streak_amount = loss_sum
        st.success("ย้อนกลับ 1 ไม้เรียบร้อย")
    else:
        st.warning("ยังไม่มีผลให้ย้อนกลับ")

# ===================== Display =====================
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    st.subheader("📊 ตารางการเดินเงิน")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("📈 Equity Curve")
    fig, ax = plt.subplots()
    ax.plot(df["ไม้"], df["พอร์ต"], marker="o")
    ax.set_xlabel("ไม้ที่")
    ax.set_ylabel("มูลค่าพอร์ต (บาท)")
    ax.set_title("การเติบโตของพอร์ต")
    ax.grid(True)
    st.pyplot(fig)

    total_profit = st.session_state.balance - capital
    st.success(f"✅ กำไรรวมประมาณ: {total_profit:,.2f} บาท")
else:
    st.caption("ยังไม่มีผลลัพธ์ - เลือกผลลัพธ์ของไม้แรกเพื่อเริ่มบันทึก")
