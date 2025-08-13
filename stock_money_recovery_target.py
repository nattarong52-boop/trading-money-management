import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
import math

st.set_page_config(page_title="การเดินเงินหุ้น (ชดทุน+เป้ากำไร)", page_icon="📈")

st.title("📈 การเดินเงินหุ้น (พุธ=ซื้อ, คอ=ขาย)")
st.markdown("ระบบคำนวณเดิมพันคืนทุน + ได้กำไรตามเป้าหมาย พร้อมสุ่มรูปแบบการซื้อขาย")

# ===== Input =====
capital = st.number_input("💰 เงินทุนเริ่มต้น (บาท)", min_value=100.0, value=1000.0, step=10.0)
num_trades = st.number_input("🔢 จำนวนไม้สูงสุด", min_value=1, value=10, step=1)
target_profit = st.number_input("🎯 กำไรต่อไม้ (บาท)", min_value=0.1, value=1.0, step=0.1)
odds = st.number_input("⚖️ อัตราจ่าย (1.0 = กำไรเท่าทุน)", min_value=0.1, value=1.0, step=0.1)
first_bet = st.number_input("💵 เดิมพันไม้แรก (บาท)", min_value=0.1, value=30.0, step=1.0)

patterns = ["พุธ", "คอ"]  # พุธ=ซื้อ, คอ=ขาย

# ===== Calculation =====
results = []
balance = capital
bet_amount = first_bet
loss_streak_amount = 0  # ยอดขาดทุนสะสม

for trade in range(1, num_trades + 1):
    pattern = random.choice(patterns)  # สุ่มซื้อ/ขาย
    win = random.choice([True, False])  # สุ่มผลลัพธ์

    if win:
        profit = bet_amount * odds
        balance += profit
        loss_streak_amount = 0  # ล้างขาดทุนสะสม
        bet_amount = first_bet  # กลับไปเริ่มใหม่
        result_text = "ชนะ"
    else:
        balance -= bet_amount
        loss_streak_amount += bet_amount
        bet_amount = math.ceil((loss_streak_amount + target_profit) / odds)
        result_text = "แพ้"

    results.append({
        "ไม้": trade,
        "Pattern": pattern,
        "ผลลัพธ์": result_text,
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
