import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

class UI:
    def __init__(self, df):
        self.original_df = df.copy()
        self.selected_year = None
        self.selected_suppliers = None
        self.filtered_df = df.copy()

    def year_selection(self):
        years = sorted(self.original_df['Datum'].dt.year.unique())
        self.selected_year = st.selectbox('Select a year for analysis:', years)
        self.filtered_df = self.original_df[self.original_df['Datum'].dt.year == self.selected_year]

    def supplier_selection(self):
        if self.filtered_df.empty:
            st.warning("No data available for the selected year.")
            return

        suppliers = sorted(self.filtered_df['Naam'].dropna().unique())
        self.selected_suppliers = st.multiselect('Select suppliers:', suppliers)

        if self.selected_suppliers:
            self.filtered_df = self.filtered_df[self.filtered_df['Naam'].isin(self.selected_suppliers)]

    def show_date_analysis(self):
        if self.filtered_df.empty:
            st.warning("No data available after filtering.")
            return

        st.subheader(f"Analysis for year {self.selected_year}")
        tabs = st.tabs([
            "Number of Deliveries",
            "No Delivery Date",
            "Fully Delivered",
            "Delivery Performance Over Time",
            "Delivery Delay by Supplier"
        ])

        with tabs[0]:
            self.plot_delivery_counts()
        with tabs[1]:
            self.plot_missing_delivery_date()
        with tabs[2]:
            self.plot_fully_delivered()
        with tabs[3]:
            self.plot_performance_over_time()
        with tabs[4]:
            self.plot_delivery_delay_categories()

    def plot_missing_delivery_date(self):
        df = self.filtered_df[self.filtered_df['DeliveryDate'].isna()]
        if df.empty:
            st.info("All orders are delivered.")
            return

        counts = df['Naam'].value_counts().reset_index()
        counts.columns = ['Supplier', 'Count']

        fig = px.bar(counts, x='Supplier', y='Count',
                     title="Orders without actual delivery date",
                     hover_data=['Supplier', 'Count'],
                     labels={'Count': 'Number of Orders'},
                     height=400)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_fully_delivered(self):
        delivered = self.filtered_df[self.filtered_df['FullyDelivered'] == True]
        if delivered.empty:
            st.info("No fully delivered orders found.")
            return

        counts = delivered['Naam'].value_counts().reset_index()
        counts.columns = ['Supplier', 'Count']

        fig = px.bar(counts, x='Supplier', y='Count',
                     title="Fully Delivered Orders",
                     hover_data=['Supplier', 'Count'],
                     color_discrete_sequence=['lightgreen'])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_delivery_counts(self):
        grouped = self.filtered_df.groupby('Naam')['DeliveryCount'].sum().reset_index()
        if grouped.empty:
            st.info("No deliveries registered.")
            return

        fig = px.bar(grouped, x='Naam', y='DeliveryCount',
                     title="Total Deliveries per Supplier",
                     hover_data=['Naam', 'DeliveryCount'],
                     color_discrete_sequence=['orange'])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_performance_over_time(self):
        df = self.filtered_df.copy()
        df['YearMonth'] = df['Datum'].dt.to_period('M').astype(str)
        timeseries = df.groupby(['YearMonth', 'Naam'])['DeliveryCount'].sum().reset_index()
        if timeseries.empty:
            st.info("No time-based delivery data available.")
            return

        fig = px.line(timeseries, x='YearMonth', y='DeliveryCount', color='Naam',
                      title="Monthly Delivery Frequency",
                      hover_data=['Naam', 'DeliveryCount'],
                      markers=True)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_delivery_delay_categories(self):
        df = self.filtered_df.copy()

        # Ensure datetime conversion
        df['DeliveryDate'] = pd.to_datetime(df['DeliveryDate'], errors='coerce')
        df['ExpectedDeliveryDate'] = pd.to_datetime(df['ExpectedDeliveryDate'], errors='coerce')

        # Filter valid date pairs
        df = df.dropna(subset=['DeliveryDate', 'ExpectedDeliveryDate'])
        if df.empty:
            st.info("No orders with both delivery and expected date.")
            return

        # Calculate delay
        df['DeliveryDelay'] = (df['DeliveryDate'] - df['ExpectedDeliveryDate']).dt.days

        # Categorize delay
        def categorize(row):
            if row < 0:
                return "Early"
            elif row == 0:
                return "On Time"
            else:
                return "Late"

        df['Category'] = df['DeliveryDelay'].apply(categorize)

        # Group by supplier and category
        summary = df.groupby(['Naam', 'Category']).size().reset_index(name='Count')

        # Pivot to wide format
        pivot_df = summary.pivot(index='Naam', columns='Category', values='Count').fillna(0)

        # Ensure column order
        pivot_df = pivot_df[['Early', 'On Time', 'Late']] if all(c in pivot_df.columns for c in ['Early', 'On Time', 'Late']) else pivot_df

        # Reset index for plotting
        pivot_df = pivot_df.reset_index()

        # Stacked bar plot
        fig = px.bar(pivot_df, x='Naam', y=['Early', 'On Time', 'Late'],
                        title="Delivery Timeliness per Supplier (Early / On Time / Late)",
                        labels={'value': 'Number of Orders', 'variable': 'Category'},
                        hover_name='Naam')

        fig.update_layout(barmode='stack', xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
