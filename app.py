import streamlit as st
import pandas as pd
import openpyxl
import re
import datetime
from openpyxl.utils.dataframe import dataframe_to_rows
import os

st.set_page_config(layout="wide")


def get_file_path(date):
    return date.strftime("%d-%m-%Y") + '.xlsx'

def extract_numeric(value):
    # Extract numeric part from the string using regular expression
    match = re.search(r'\d+(\.\d+)?', str(value))
    return float(match.group()) if match else 0.0

def parse_message(message, selected_rider):
    data = {
        "Name": "",
        "Phone": "",
        "Delivery Address": "",
        "Fare": "",
        "Fare paid Online": "",  # New field
        "Cash": "",
        "Online": "",
        "Credit Card": "",
        "last-digits": "",
        "Rider": selected_rider.lower()  # Use the selected rider
    }

    # Split the message by lines and process each line
    lines = message.split('\n')
    for line in lines:
        if "Name:" in line:
            data["Name"] = line.replace("Name:", "").strip().lower()
        elif "Phone:" in line:
            data["Phone"] = line.replace("Phone:", "").strip().replace(" ", "").replace("-", "")
        elif "Delivery Address:" in line:
            data["Delivery Address"] = line.replace("Delivery Address:", "").strip().lower()
        elif "Fare:" in line:
            data["Fare"] = extract_numeric(line.replace("Fare:", "").strip())
        elif "Fare paid Online:" in line:  # Handle Fare paid Online
            data["Fare paid Online"] = line.replace("Fare paid Online:", "").strip().lower()
        elif "Cash:" in line:
            data["Cash"] = extract_numeric(line.replace("Cash:", "").strip())
        elif "Online:" in line:
            data["Online"] = extract_numeric(line.replace("Online:", "").strip())
        elif "Credit Card:" in line:
            data["Credit Card"] = extract_numeric(line.replace("Credit Card:", "").strip())
        elif "last-digits:" in line:  # Handling the last-digits field
            data["last-digits"] = line.replace("last-digits:", "").strip()
        # elif "Rider:" in line:
        #     data["Rider"] = line.replace("Rider:", "").strip().lower()

    return data





def set_column_widths(worksheet, widths):
    for i, column_width in enumerate(widths, start=1):
        worksheet.column_dimensions[openpyxl.utils.get_column_letter(i)].width = column_width


def write_to_spreadsheet(data, file_path):
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=['Name', 'Phone', 'Delivery Address', 'Fare', 'Fare paid Online', 'Cash', 'Online', 'Credit Card', 'Rider'])
        df.to_excel(file_path, index=False)

    try:
        # Read the existing file, ensuring 'Phone' is read as a string
        df = pd.read_excel(file_path, dtype={'Phone': str})

        # Prepare new data ensuring 'Phone' is a string
        new_data_df = pd.DataFrame([data])
        new_data_df['Phone'] = new_data_df['Phone'].astype(str)

        # Concatenate and save
        df = pd.concat([df, new_data_df], ignore_index=True)
        df.to_excel(file_path, index=False)
    except Exception as e:
        st.error(f"Error processing file: {e}")

def display_by_rider(df, rider_name):
    filtered_df = df[df['Rider'] == rider_name]
    if not filtered_df.empty:
        st.markdown(f"<h3 style='color:#5C83F5;'>{rider_name.capitalize()}</h3>", unsafe_allow_html=True)
        st.dataframe(filtered_df)

        # Function to extract numeric part from the string
        def extract_numeric(value):
            match = re.search(r'\d+(\.\d+)?', str(value))
            return float(match.group()) if match else 0.0

        # Calculate sums
        sum_fare = sum(filtered_df['Fare'].apply(extract_numeric))
        sum_cash = sum(filtered_df['Cash'].apply(extract_numeric))
        sum_online = sum(filtered_df['Online'].apply(extract_numeric))
        sum_credit = sum(filtered_df['Credit Card'].apply(extract_numeric))

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Fare", f"{sum_fare}")
        col2.metric("Total Cash", f"{sum_cash}")
        col3.metric("Total Online", f"{sum_online}")
        col4.metric("Total Credit Card", f"{sum_credit}")

        st.markdown("---")

def display_stats_view(df):
    col1, s1, col2, s2, col3, s3, col4 = st.columns([3, 1, 3, 1, 4, 1, 3])

    # Specific table for Pickup
    pickup_df = df[df['Delivery Address'].str.lower().isin(['pickup', 'pick-up'])]
    pickup_cash_total = pickup_df['Cash'].sum()
    pickup_online_total = pickup_df['Online'].sum()
    pickup_credit_card_total = pickup_df['Credit Card'].sum()

    # Append pickup totals to each respective total dataframe
    pickup_totals_entry = pd.DataFrame([{'Rider': 'Pickup', 'Cash': pickup_cash_total, 'Online': pickup_online_total, 'Credit Card': pickup_credit_card_total}])

    # Table for Cash Totals by Rider
    with col1:
        cash_total = df.groupby('Rider')['Cash'].sum().reset_index()
        cash_total = pd.concat([cash_total, pickup_totals_entry[['Rider', 'Cash']]], ignore_index=True)
        st.markdown(f"<h3 style='color:#5C83F5;'>Cash</h3>", unsafe_allow_html=True)
        st.dataframe(cash_total)
        total_cash = cash_total['Cash'].sum()
        st.metric("Total Cash", f"{total_cash} Rs")
        st.markdown("---")

    # Table for Online Totals by Rider
    with col2:
        online_total = df.groupby('Rider')['Online'].sum().reset_index()
        online_total = pd.concat([online_total, pickup_totals_entry[['Rider', 'Online']]], ignore_index=True)
        st.markdown(f"<h3 style='color:#5C83F5;'>Online</h3>", unsafe_allow_html=True)
        st.dataframe(online_total)
        total_online = online_total['Online'].sum()
        st.metric("Total Online", f"{total_online} Rs")
        st.markdown("---")

    # Table for Credit Card Totals by Name, including last-digits as the last column
    with col3:
        card_total = df.groupby(['Name', 'last-digits'])['Credit Card'].sum().reset_index()
        st.markdown(f"<h3 style='color:#5C83F5;'>Card Payments</h3>", unsafe_allow_html=True)
        st.dataframe(card_total)
        total_credit_card = card_total['Credit Card'].sum()
        st.metric("Total Credit Card", f"{total_credit_card} Rs")
        st.markdown("---")

    with col4:
        st.markdown(f"<h3 style='color:#5C83F5;'>Online Payments</h3>", unsafe_allow_html=True)
        online_payments_df = df[df['Online'] > 0][['Name', 'Online']]
        st.dataframe(online_payments_df)
        total_online_transfer = online_payments_df['Online'].sum()
        st.metric("Total Online", f"{total_online_transfer} Rs")
        st.markdown("---")

    # Specific table for Pickup
    # with col5:
    #     st.markdown(f"<h3 style='color:#5C83F5;'>Pickup</h3>", unsafe_allow_html=True)
    #     st.dataframe(pickup_df[['Name', 'Cash', 'Online', 'Credit Card']])
    #     c1, c2, c3 = st.columns(3)
    #     c1.metric("Pickup Cash", f"{pickup_cash_total} Rs")
    #     c2.metric("Pickup Online", f"{pickup_online_total} Rs")
    #     c3.metric("Pickup Credit Card", f"{pickup_credit_card_total} Rs")
    #     st.markdown("---")


def display_daily_balance(df):
    col1, _ = st.columns([1, 1])  # Adjust column sizes as needed
    with col1:
        st.markdown(f"<h3 style='color:#5C83F5;'>Daily Balance</h3>", unsafe_allow_html=True)

        # Initialize the balance DataFrame with opening balance
        balance_data = [{
            "Name": "Opening Balance",
            "Running Balance (Cash)": 7000,
            "Cash In": 0,
            "Cash Out": 0,
            "Online": 0
        }]

        running_balance = 7000  # Initialize the running balance

        for index, row in df.iterrows():
            cash_in = row['Cash'] if row['Cash'] else 0
            cash_out = 0
            online = row['Online'] if row['Online'] else 0
            fare_paid_online = row.get('Fare paid Online', 'no') == 'yes'
            fare_amount = row['Fare'] if row['Fare'] else 0

            name = row['Name'] + " Fare" if fare_paid_online else row['Name']
            if fare_paid_online:
                cash_out = -fare_amount
                running_balance -= fare_amount

            running_balance += cash_in  # Update running balance

            balance_data.append({
                "Name": name,
                "Running Balance (Cash)": running_balance,
                "Cash In": cash_in,
                "Cash Out": cash_out,
                "Online": online
            })

        balance_df = pd.DataFrame(balance_data)

        # Calculate totals without adding them to the DataFrame
        total_running_balance_cash = running_balance
        total_cash_in = sum(balance_df['Cash In'])
        total_cash_out = sum(balance_df['Cash Out'])
        total_online = sum(balance_df['Online'])

        # Display the DataFrame (show all rows)
        st.dataframe(balance_df, height=450)  # Adjust height as needed to display all rows

        # Display totals using metrics
        st.markdown("### Totals")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Running Balance (Cash)", f"{total_running_balance_cash}")
        col2.metric("Total Cash In", f"{total_cash_in}")
        col3.metric("Total Cash Out", f"{total_cash_out}")
        col4.metric("Total Online", f"{total_online}")




default_message = '''Name:
Phone:
Delivery Address:
Fare:
Cash:
Online:
Credit Card:
last-digits:'''



def main_app():
    st.title("Data Entry App")

    today = datetime.datetime.now().strftime("%d-%m-%Y")
    file_path = f'{today}.xlsx'

    # Ensure that 'message_text' is in the session state
    if 'message_text' not in st.session_state or st.session_state.message_text.strip() == "":
        st.session_state.message_text = default_message
    
    # Define the tabs
    tab1, tab2, tab3 = st.tabs(["Data Entry", "Rider Info", "Stats"])

    with tab1:
        col1, spacer, col2 = st.columns([4, 1, 5])
        with col1:
            st.session_state.message_text = st.text_area("Enter the message here:", st.session_state.message_text, height=300)
            selected_rider = st.radio("Select Rider", ["Pickup", "Shazaib", "Zubair", "Indrive"], horizontal=True)
            fare_paid_online_option = st.radio("Fare Paid Online", ["No", "Yes"], horizontal=True)

            if st.button("Process", key='process1'):
                data = parse_message(st.session_state.message_text, selected_rider)
                data['Fare paid Online'] = fare_paid_online_option.lower()

                errors = []

                # Check if exactly one payment method is selected
                payment_methods_filled = sum(bool(data[method]) for method in ['Cash', 'Online', 'Credit Card'])
                if payment_methods_filled != 1:
                    errors.append("Exactly one of Cash, Online, or Credit Card must be selected.")

                # Check if Cash is selected and Fare paid Online is 'yes'
                if data['Cash'] and data['Fare paid Online'] == 'yes':
                    errors.append("If Cash is selected, Fare Paid Online must be 'No'.")

                # Check if Credit Card is selected, then last-digits must be filled
                if data['Credit Card'] and not data['last-digits']:
                    errors.append("Last-digits field is required when Credit Card is selected.")

                # Check numeric fields
                numeric_fields = ['Cash', 'Online', 'Fare', 'Credit Card']
                for field in numeric_fields:
                    if data[field] and not isinstance(data[field], (int, float)):
                        errors.append(f"{field} must be numeric.")

                if errors:
                    st.error("Errors: " + "; ".join(errors))
                else:
                    today = datetime.datetime.now().strftime("%d-%m-%Y")
                    file_path = f'{today}.xlsx'
                    write_to_spreadsheet(data, file_path)
                    st.success("Data added to spreadsheet.")
            delete_record_num = st.number_input("Enter record number to delete", min_value=0, step=1) + 1
            if st.button("Delete Record", key='delete1'):
                if os.path.exists(file_path):
                    try:
                        df = pd.read_excel(file_path)
                        if 1 <= delete_record_num <= len(df):
                            if delete_record_num > len(df) - 10:
                                df = df.drop(df.index[delete_record_num - 1])
                                df.to_excel(file_path, index=False)
                                st.success(f"Record number {delete_record_num - 1} deleted.")
                            else:
                                st.error("Only the last 10 records can be deleted.")
                        else:
                            st.error("Record number out of range.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

        with col2:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path, dtype={'Phone': str})
                df['Phone'] = df['Phone'].astype(str).str.replace(r'\.0$', '', regex=True)
                df['Cash'] = df['Cash'].astype(str)
                df['Online'] = df['Online'].astype(str)
                df['Credit Card'] = df['Credit Card'].astype(str)
                st.write("Last 10 Records:")
                st.dataframe(df.tail(10))

    with tab2:
        col_date, _ = st.columns([1, 14])
        col_err, _ = st.columns([1, 5])
        with col_date:
            selected_date2 = st.date_input("Select Date", datetime.datetime.today(), key="date_input_2")
        file_path_for_date = selected_date2.strftime("%d-%m-%Y") + '.xlsx'
        col1, spacer, col2 = st.columns([4, 1, 4])
        if os.path.exists(file_path_for_date):
            df = pd.read_excel(file_path_for_date, dtype={'Phone': str, 'Fare': float, 'Cash': float, 'Online': float, 'Credit Card': float})
            unique_riders = df['Rider'].unique()
            for i, rider in enumerate(unique_riders):
                with (col1 if i % 2 == 0 else col2):
                    display_by_rider(df, rider)
        else:
            with col_err:
                st.error(f"No records found for {selected_date2.strftime('%d-%m-%Y')}")

    with tab3:
        col_date, _ = st.columns([1, 14])
        col_err, _ = st.columns([1, 5])
        with col_date:
            selected_date3 = st.date_input("Select Date", datetime.datetime.today(), key="date_input_3")  # Unique key
        file_path_for_date = selected_date3.strftime("%d-%m-%Y") + '.xlsx'
        if os.path.exists(file_path_for_date):
            df = pd.read_excel(file_path_for_date)
            display_stats_view(df)
            display_daily_balance(df)
        else:
            with col_err:
                st.error(f"No records found for {selected_date3.strftime('%d-%m-%Y')}")


def login(username, password):
    return username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]



# Check if the user is logged in
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()  # Show the main app if already logged in
else:
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login(username, password):
            st.session_state.logged_in = True
            st.experimental_rerun()  # Rerun the app to display the main app
        else:
            st.sidebar.error("Incorrect username or password.")


css = '''
<style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size:20px;
    font-family:sans-serif;
    font-weight: 600;
    }
</style>
'''

st.markdown(css, unsafe_allow_html=True)