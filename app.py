import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="Purchase Manager", layout="centered")

# Predefined users for authentication
USERS = {
    'Admin': {'password': 'admin123'},
    'guest1': {'password': 'guest1pass'},
    'guest2': {'password': 'guest2pass'},
    # Add more guest accounts here
}

# Session state initialization
def init_session_state():
    if 'purchase_items' not in st.session_state:
        st.session_state['purchase_items'] = []
    if 'guest_orders' not in st.session_state:
        st.session_state['guest_orders'] = []
    if 'batch_inputs' not in st.session_state:
        st.session_state['batch_inputs'] = pd.DataFrame()
    if 'guest_inputs' not in st.session_state:
        st.session_state['guest_inputs'] = pd.DataFrame(columns=['Item Name', 'Quantity (kg)'])
    if 'guest_note' not in st.session_state:
        st.session_state['guest_note'] = ''
    if 'margin_type_selected' not in st.session_state:
        st.session_state['margin_type_selected'] = "Fixed Amount"
    if 'user' not in st.session_state:
        st.session_state['user'] = None

MARGIN_OPTIONS = ["Fixed Amount", "%", "Selling Price per kg"]

# Authentication function
def authenticate_user():
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type='password')
    if st.sidebar.button("Login"):
        user_info = USERS.get(username)
        if user_info and user_info['password'] == password:
            st.session_state['user'] = username
            st.success(f"Logged in as {username}")
        else:
            st.error("Invalid username or password")

# Admin purchase manager page
def purchase_manager():
    st.title("Purchase Manager - Admin")
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

    if st.button("Add All Items"):
        add_items_to_orders(edited_df, columns_to_show, margin_type_selected)

    display_purchase_summary()

# Guest new order page
def new_order_grid():
    edited_df = st.data_editor(st.session_state.guest_inputs, num_rows='dynamic', use_container_width=True)
    edited_df = edited_df.fillna('')
    st.session_state.guest_note = st.text_area("Add Note for this order")
    st.warning("🔔 Review all items before placing your order.")
    if st.button("Place Order"):
        place_guest_order(edited_df, st.session_state.guest_note)

def place_guest_order(df, note):
    order_items = []
    whatsapp_text = []
    for _, row in df.iterrows():
        item_name = str(row['Item Name']).strip()
        if item_name:
            qty = row['Quantity (kg)']
            order_items.append({'item': item_name, 'quantity': qty})
            whatsapp_text.append(f"{item_name} - {qty} kg")
    if order_items:
        st.session_state.guest_orders.append({'date': datetime.now().strftime('%Y-%m-%d'), 'items': order_items, 'note': note})
    if whatsapp_text:
        message = urllib.parse.quote(', '.join(whatsapp_text) + f"\nNote: {note}")
        st.markdown(f"[Send via WhatsApp](https://api.whatsapp.com/send?text={message})")
        st.success("Order placed successfully!")
        st.session_state.guest_inputs = pd.DataFrame(columns=['Item Name', 'Quantity (kg)'])
        st.session_state.guest_note = ''

def display_guest_orders():
    if st.session_state.guest_orders:
        for i, order in enumerate(st.session_state.guest_orders, start=1):
            with st.expander(f"Order #{i} - {order['date']}"):
                items_summary = ', '.join([f"{entry['item']}: {entry['quantity']} kg" for entry in order['items']])
                st.markdown(items_summary)
                if order.get('note'):
                    st.markdown(f"**Note:** {order['note']}")
                st.markdown("---")
    else:
        st.info("No past orders yet.")

def display_purchase_summary():
    if st.session_state.purchase_items:
        summary_lines = ["📋 Purchase Summary"]
        for i, order in enumerate(st.session_state.purchase_items, start=1):
            summary_lines.append(f"\nOrder #{i} - {order['date']}")
            item_summary = ', '.join([f"{entry['item']}: {entry['quantity']:.2f} kg" for entry in order['items']])
            summary_lines.append(item_summary)
        total_buy_all = sum(e['total_buy'] for o in st.session_state.purchase_items for e in o['items'])
        total_sell_all = sum(e['total_sell'] for o in st.session_state.purchase_items for e in o['items'])
        total_profit_all = sum(e['profit'] for o in st.session_state.purchase_items for e in o['items'])
        summary_lines.append(f"\nTotal Buying Price: {total_buy_all:.2f}")
        summary_lines.append(f"Total Selling Price: {total_sell_all:.2f}")
        summary_lines.append(f"Total Profit: {total_profit_all:.2f}")
        summary_text = '\n'.join(summary_lines)
        st.text_area("Summary to share (copy & paste)", value=summary_text, height=250)
        if st.button("Clear All Entries"):
            st.session_state.purchase_items = []
            st.experimental_rerun()

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
            order_items.append({'item': item_name, 'quantity': quantity, 'purchase_price': purchase_price, 'margin_type': margin_type, 'margin_value': margin_value, 'selling_price': selling_price, 'total_buy': total_buy, 'total_sell': total_sell, 'profit': profit})
    if order_items:
        st.session_state.purchase_items.append({'date': datetime.now().strftime('%Y-%m-%d'), 'items': order_items})
        st.success(f"Added {len(order_items)} items successfully!")
        st.session_state.batch_inputs = pd.DataFrame(columns=columns)

def show_orders_inbox():
    st.title("Orders Inbox")
    display_guest_orders()

# Guest page function
def guest_page():
    st.title("Guest Page")
    tabs = st.tabs(["New Order", "Past Orders"])
    with tabs[0]:
        new_order_grid()
    with tabs[1]:
        display_guest_orders()

# Main function
def main():
    init_session_state()
    if st.session_state['user'] is None:
        authenticate_user()
        return

    user_role = 'Admin' if st.session_state['user'] == 'Admin' else 'Guest'

    if user_role == 'Admin':
        page = st.sidebar.radio("Go to", ["Manager", "Orders Inbox"])
        if page == "Manager":
            purchase_manager()
        else:
            show_orders_inbox()
    else:
        guest_page()

if __name__ == "__main__":
    main()
