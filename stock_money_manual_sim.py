import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math
import random

st.set_page_config(page_title="การเดินเงินหุ้น", page_icon="📈")

st.title("📈 การเดินเงินหุ้น (พุธ=ซื้อ, คอ=ขาย)")
st.markdown("สุ่มซื้อ/ขาย, กรอกผลเอง, คำนวณจำนวนไม้สูงสุดที่ทุนรองรับได้")

# ===== Input =====
capital = st.number_input("💰 เงินทุนเริ่มต้น (บาท)", min_value=10.0, value=1000.0, step=10.0)
num_trades = st.number_input("🔢 จำนวนไม้ที่ต้องการจำลอง", min_value=1, value=5, step=1)
target_profit = st.number_input("🎯 กำไรที่ต้องการต่อรอบ (บาท)", min_value=0.1, value=1.0, step=0.1)
odds = st.number_input("⚖️ อัตราจ่าย (1.0 = กำไรเท่าทุน)", min_value=0.1, value=1.0, step=0.1)
first_bet = st.number_input("💵 เงินเดิมพันไม้แรก (บาท)", min_value=0.1, value=30.0, step=1.0)

# ===== คำนวณจำนวนไม้สูงสุดที่ทุนรองรับได้ =====
max_bet_amount = first_bet
loss_streak_amount = 0
temp_capital = capital
max_trades_possible = 0

while temp_capital >= max_bet_amount:
    temp_capital -= max_bet_amount
    loss_streak_amount += max_bet_amount
    max_trades_possible += 1
    max_bet_amount = math.ceil((loss_streak_amount + target_profit) / odds)

st.info(f"💡 ถ้าแพ้ติดกันทุกไม้ คุณจะสามารถเล่นได้สูงสุด {max_trades_possible} ไม้ ก่อนที่ทุนจะหมด")

# ===== Logic เดินเงินจริง =====
results = []
balance = capital
bet_amount = first_bet
loss_streak_amount = 0
patterns = ["พุธ", "คอ"]

for trade in range(1, num_trades + 1):
    pattern = random.choice(patterns)  # สุ่มซื้อ/ขาย
    result = st.selectbox(f"ผลลัพธ์ไม้ {trade} ({pattern})", ["-", "ชนะ", "แพ้"], key=f"result_{trade}")

    if result == "ชนะ":
        profit = bet_amount * odds
        balance += profit
        loss_streak_amount = 0
        bet_amount = first_bet
    elif result == "แพ้":
        balance -= bet_amount
        loss_streak_amount += bet_amount
        bet_amount = math.ceil((loss_streak_amount + target_profit) / odds)

    results.append({
        "ไม้": trade,
        "Pattern": pattern,
        "ผลลัพธ์": result,
        "เงินเดิมพัน": bet_amount,
        "พอร์ต": round(balance, 2)
    })

# ===== Show Table =====
df = pd.DataFrame(results)
st.subheader("📊 ตารางการเดินเงิน")
st.dataframe(df)

# ===== Show Chart =====
fig, ax = plt.subplots()
ax.plot(df["ไม้"], df["พอร์ต"], marker="o")
ax.set_xlabel("ไม้ที่")
ax.set_ylabel("มูลค่าพอร์ต (บาท)")
ax.set_title("การเติบโตของพอร์ต")
ax.grid(True)
st.pyplot(fig)

# ===== Summary =====
total_profit = balance - capital
st.success(f"✅ กำไรรวมประมาณ: {total_profit:,.2f} บาท")
