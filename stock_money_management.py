import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="การเดินเงินหุ้น", page_icon="📊", layout="centered", initial_sidebar_state="collapsed")

st.title("📊 การเดินเงินหุ้น")
st.markdown("แอปคำนวณขนาดการซื้อ บันทึกการเทรด และดูสถิติพอร์ต")

# เก็บข้อมูลใน session
if "trades" not in st.session_state:
    st.session_state.trades = []
if "capital" not in st.session_state:
    st.session_state.capital = 100000.0

# ฟอร์มคำนวณ
with st.form("trade_form"):
    capital = st.number_input("💰 ทุนปัจจุบัน (บาท)", value=st.session_state.capital, step=1000.0, format="%.2f")
    risk_percent = st.number_input("⚠️ ความเสี่ยงต่อการเทรด (%)", min_value=0.0, value=2.0, step=0.1)
    entry = st.number_input("📈 ราคาซื้อ (บาท)", min_value=0.0, value=50.0, step=0.1)
    stop_loss = st.number_input("📉 ราคาตัดขาดทุน (บาท)", min_value=0.0, value=48.0, step=0.1)
    target = st.number_input("🎯 ราคาเป้ากำไร (บาท)", min_value=0.0, value=55.0, step=0.1)
    result = st.selectbox("ผลการเทรด", ["-", "ชนะ", "แพ้"])
    note = st.text_input("🗒 หมายเหตุ", value="")
    submitted = st.form_submit_button("คำนวณและบันทึก")

if submitted:
    if entry == stop_loss:
        st.error("ราคาซื้อและ Stop Loss ต้องไม่เท่ากัน!")
    else:
        risk_per_trade = capital * (risk_percent / 100)
        risk_per_share = abs(entry - stop_loss)
        position_size = risk_per_trade / risk_per_share
        rr_ratio = abs(target - entry) / risk_per_share
        profit_loss = 0

        if result == "ชนะ":
            profit_loss = (target - entry) * position_size
        elif result == "แพ้":
            profit_loss = (stop_loss - entry) * position_size

        new_capital = capital + profit_loss
        st.session_state.capital = new_capital

        st.success(f"📌 ขนาดการซื้อ: {position_size:.2f} หุ้น")
        st.info(f"📊 R:R = {rr_ratio:.2f}")
        if result != "-":
            st.write(f"💹 กำไร/ขาดทุน: {profit_loss:.2f} บาท | ทุนใหม่: {new_capital:.2f} บาท")

        st.session_state.trades.append({
            "วันที่-เวลา": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ทุนก่อนหน้า": capital,
            "Entry": entry,
            "Stop Loss": stop_loss,
            "Target": target,
            "ขนาดซื้อ": position_size,
            "R:R": rr_ratio,
            "ผลลัพธ์": result,
            "กำไร/ขาดทุน": profit_loss,
            "ทุนหลังเทรด": new_capital,
            "หมายเหตุ": note
        })

# แสดงตารางบันทึก
if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    st.subheader("📜 ประวัติการเทรด")
    st.dataframe(df)

    # คำนวณสถิติ
    wins = df[df["ผลลัพธ์"] == "ชนะ"].shape[0]
    losses = df[df["ผลลัพธ์"] == "แพ้"].shape[0]
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    avg_return = df["กำไร/ขาดทุน"].mean() if total_trades > 0 else 0

    st.subheader("📈 สถิติพอร์ต")
    st.write(f"Win Rate: {win_rate:.2f}%")
    st.write(f"Average Return ต่อเทรด: {avg_return:.2f} บาท")

    # กราฟ Equity Curve
    st.subheader("📊 Equity Curve")
    plt.plot(df["ทุนหลังเทรด"])
    plt.xlabel("จำนวนการเทรด")
    plt.ylabel("มูลค่าพอร์ต (บาท)")
    plt.grid(True)
    st.pyplot(plt)
