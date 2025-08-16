import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Purchase Manager", layout="centered")

# Session state initialization
def init_session_state():
    if 'purchase_items' not in st.session_state:
        st.session_state['purchase_items'] = []
    if 'batch_inputs' not in st.session_state:
        st.session_state['batch_inputs'] = pd.DataFrame()
    if 'margin_type_selected' not in st.session_state:
        st.session_state['margin_type_selected'] = "Selling Price per kg"

MARGIN_OPTIONS = ["Fixed Amount", "%", "Selling Price per kg"]

# Admin purchase manager page
def purchase_manager():
    st.title("Purchase Manager")
    margin_type_selected = st.selectbox("Select Margin Type for new rows", MARGIN_OPTIONS, index=MARGIN_OPTIONS.index(st.session_state['margin_type_selected']))
    st.session_state['margin_type_selected'] = margin_type_selected

    if margin_type_selected == 'Fixed Amount':
        columns_to_show = ['Item Name', 'Quantity (kg)', 'Purchase Price/kg', 'Margin Value']
    elif margin_type_selected == '%':
        columns_to_show = ['Item Name', 'Quantity (kg)', 'Purchase Price/kg', 'Margin %']
    else:
        columns_to_show = ['Item Name', 'Quantity (kg)', 'Purchase Price/kg', 'Selling Price/kg']

    if st.session_state.batch_inputs.empty or not all(col in st.session_state.batch_inputs.columns for col in columns_to_show):
        st.session_state.batch_inputs = pd.DataFrame(columns=columns_to_show)

    edited_df = st.data_editor(st.session_state.batch_inputs[columns_to_show], num_rows='dynamic', use_container_width=True)
    edited_df = edited_df.fillna(0)

    for idx in edited_df.index:
        buy_price = float(edited_df.at[idx, 'Purchase Price/kg'])
        qty = float(edited_df.at[idx, 'Quantity (kg)'])
        if margin_type_selected == 'Fixed Amount':
            margin_value = float(edited_df.at[idx, 'Margin Value'])
            edited_df.at[idx, 'Selling Price/kg'] = buy_price + margin_value
        elif margin_type_selected == '%':
            margin_pct = float(edited_df.at[idx, 'Margin %'])
            edited_df.at[idx, 'Selling Price/kg'] = buy_price * (1 + margin_pct / 100)
            edited_df.at[idx, 'Margin Value'] = edited_df.at[idx, 'Selling Price/kg'] - buy_price
        else:
            sell_price = float(edited_df.at[idx, 'Selling Price/kg'])
            edited_df.at[idx, 'Margin Value'] = sell_price - buy_price

    st.warning("🔔 Review items before clicking 'Add All Items'.")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Add All Items"):
            add_items_to_orders(edited_df, columns_to_show, margin_type_selected)
    with col2:
        if st.button("Clear Grid"):
            st.session_state.batch_inputs = pd.DataFrame(columns=columns_to_show)
            st.rerun()

    display_purchase_summary()
    
def display_purchase_summary():
    if st.session_state.purchase_items:
        total_buy_all, total_sell_all, total_profit_all = 0, 0, 0
        summary_text = "Purchase Summary\n\n"
        
        # Build summary text only (no markdown display)
        for order in st.session_state.purchase_items:
            for entry in order['items']:
                summary_text += f"Item Name: {entry['item']} | Qty: {entry['quantity']:.2f} kg | Buying Price/kg: {entry['purchase_price']:.2f} | Selling Price/kg: {entry['selling_price']:.2f} | Profit: {entry['profit']:.2f}\n"
            summary_text += "---\n"
        
        summary_text += f"\nTotal Buying Price: {sum(entry['total_buy'] for order in st.session_state.purchase_items for entry in order['items']):.2f}\n"
        summary_text += f"Total Selling Price: {sum(entry['total_sell'] for order in st.session_state.purchase_items for entry in order['items']):.2f}\n"
        summary_text += f"Total Profit: {sum(entry['profit'] for order in st.session_state.purchase_items for entry in order['items']):.2f}"

        # Text area for sharing summary
        st.text_area("Summary to share", value=summary_text, height=300, key="summary_area")

        # Copy to clipboard button
        components.html(f"""
            <button onclick="navigator.clipboard.writeText(`{summary_text.replace('`','\\`')}`).then(() => alert('Summary copied to clipboard!'))">
                Copy Summary to Clipboard
            </button>
        """, height=50)

        # Clear all entries button
        if st.button("Clear All Entries"):
            st.session_state.purchase_items = []
            st.session_state.batch_inputs = pd.DataFrame()
            st.rerun()


def add_items_to_orders(df, columns, margin_type):
    order_items = []
    for _, row in df.iterrows():
        item_name = str(row['Item Name']).strip()
        if item_name:
            quantity = float(row['Quantity (kg)'])
            purchase_price = float(row['Purchase Price/kg'])
            selling_price = float(row['Selling Price/kg']) if 'Selling Price/kg' in row else purchase_price + float(row.get('Margin Value', 0))
            margin_value = float(row['Margin Value'])
            total_buy = quantity * purchase_price
            total_sell = quantity * selling_price
            profit = total_sell - total_buy
            order_items.append({
                'item': item_name, 
                'quantity': quantity, 
                'purchase_price': purchase_price, 
                'margin_type': margin_type, 
                'margin_value': margin_value, 
                'selling_price': selling_price, 
                'total_buy': total_buy, 
                'total_sell': total_sell, 
                'profit': profit
            })
    if order_items:
        st.session_state.purchase_items.append({'items': order_items})
        st.success(f"Added {len(order_items)} items successfully!")
        st.session_state.batch_inputs = pd.DataFrame(columns=columns)

# Main function
def main():
    init_session_state()
    purchase_manager()

if __name__ == "__main__":
    main()
