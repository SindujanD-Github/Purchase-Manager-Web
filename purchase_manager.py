import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Purchase Manager", layout="centered")

if 'purchase_items' not in st.session_state:
    st.session_state['purchase_items'] = []

st.title("Purchase Manager")

with st.form("purchase_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        item_name = st.text_input("Item Name")
        quantity = st.number_input("Quantity (kg)", min_value=0)
    with col2:
        purchase_price = st.number_input("Purchase Price per kg", min_value=0)
        margin_type = st.selectbox("Profit Margin Type", ["Fixed Amount", "%"])
        margin_value = st.number_input("Profit Margin Value", min_value=0)

    submitted = st.form_submit_button("Add Purchase")

if submitted:
    if not item_name.strip():
        st.warning("Please enter an item name.")
    else:
        if margin_type == "%":
            selling_price = purchase_price * (1 + margin_value / 100)
        else:
            selling_price = purchase_price + margin_value

        total_buy = quantity * purchase_price
        total_sell = quantity * selling_price
        profit = total_sell - total_buy
        date_str = datetime.now().strftime("%Y-%m-%d")

        st.session_state.purchase_items.append({
            "date": date_str,
            "item": item_name.strip(),
            "quantity": quantity,
            "purchase_price": purchase_price,
            "margin_type": margin_type,
            "margin_value": margin_value,
            "selling_price": selling_price,
            "total_buy": total_buy,
            "total_sell": total_sell,
            "profit": profit
        })

        st.success(f"Added {item_name} ({quantity} kg) successfully!")

if st.session_state.purchase_items:
    st.markdown("### 📋 Purchase Summary")

    total_buy_all = sum(i['total_buy'] for i in st.session_state.purchase_items)
    total_sell_all = sum(i['total_sell'] for i in st.session_state.purchase_items)
    total_profit_all = sum(i['profit'] for i in st.session_state.purchase_items)

    for i, entry in enumerate(st.session_state.purchase_items, start=1):
        st.write(
            f"{i}. 📅 {entry['date']} | 🥬 {entry['item']} | Qty: {entry['quantity']:.2f} kg | "
            f"Buy: {entry['purchase_price']:.2f}/kg | Sell: {entry['selling_price']:.2f}/kg | "
            f"Profit: {entry['profit']:.2f}"
        )

    st.markdown("---")
    st.write(f"**Total Buying Price:** {total_buy_all:.2f}")
    st.write(f"**Total Selling Price:** {total_sell_all:.2f}")
    st.write(f"**Total Profit:** {total_profit_all:.2f}")

    summary_lines = [
        f"Purchase Manager Summary ({datetime.now().strftime('%Y-%m-%d')}):"
    ]
    for entry in st.session_state.purchase_items:
        summary_lines.append(
            f"{entry['item']} - {entry['quantity']:.2f} kg - Buy: {entry['purchase_price']:.2f}/kg - "
            f"Sell: {entry['selling_price']:.2f}/kg - Profit: {entry['profit']:.2f}"
        )
    summary_lines.append("")
    summary_lines.append(f"Total Buying Price: {total_buy_all:.2f}")
    summary_lines.append(f"Total Selling Price: {total_sell_all:.2f}")
    summary_lines.append(f"Total Profit: {total_profit_all:.2f}")

    summary_text = "\n".join(summary_lines)

    st.text_area("Summary to share (copy & paste)", value=summary_text, height=250)

    if st.button("Clear All Entries"):
        st.session_state.purchase_items = []
        st.experimental_rerun()
