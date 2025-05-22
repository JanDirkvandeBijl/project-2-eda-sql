import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

class UI:
    def __init__(self, df):
        self.original_df = df.copy()
        self.selected_years = []
        self.selected_suppliers = []
        self.filtered_df = df.copy()

    def year_selection(self):
        all_years = sorted(self.original_df['Datum'].dt.year.unique())
        self.selected_years = st.multiselect(
            'Select one or more years (leave empty to include all):',
            options=all_years,
            default=[]
        )

        if self.selected_years:
            self.filtered_df = self.original_df[self.original_df['Datum'].dt.year.isin(self.selected_years)]
        else:
            self.filtered_df = self.original_df.copy()

    def supplier_selection(self):
        if self.filtered_df.empty:
            st.warning("No data available.")
            return

        suppliers = sorted(self.filtered_df['Naam'].dropna().unique())
        self.selected_suppliers = st.multiselect('Select suppliers:', suppliers)

        if self.selected_suppliers:
            self.filtered_df = self.filtered_df[self.filtered_df['Naam'].isin(self.selected_suppliers)]

    def show_date_analysis(self):
        if self.filtered_df.empty:
            st.warning("No data available after filtering.")
            return

        year_label = ", ".join(map(str, self.selected_years)) if self.selected_years else "all years"
        st.subheader(f"Delivery Analysis for {year_label}")

        total_orders = self.filtered_df['OrNu'].nunique() if 'OrNu' in self.filtered_df.columns else 0
        total_order_lines = len(self.filtered_df)
        total_suppliers = self.filtered_df['Naam'].nunique()
        fully_delivered = self.filtered_df[self.filtered_df['FullyDelivered'] == True].shape[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Orders", total_orders)
        col2.metric("Total Order Lines", total_order_lines)
        col3.metric("Total Suppliers", total_suppliers)
        col4.metric("Fully Delivered Lines", fully_delivered)

        tab_groups = st.tabs([
            "Per Order",
            "Per Order Line",
            "Timeliness & Trends"
        ])

        with tab_groups[0]:
            self.plot_order_delivery_summary()

        with tab_groups[1]:
            self.plot_delivery_counts()
            self.plot_missing_delivery_date()
            self.plot_fully_delivered()

        with tab_groups[2]:
            self.plot_performance_over_time()

    def plot_order_delivery_summary(self):
        st.info("Toont per leverancier hoeveel volledige orders te vroeg, op tijd of te laat zijn geleverd. Een order bestaat uit meerdere regels.")

        df = self.filtered_df.copy()
        if 'OrNu' not in df.columns:
            st.warning("Order number (OrNu) not found in data.")
            return

        grouped = df.groupby('OrNu').agg({
            'ExpectedDeliveryDate': 'max',
            'DeliveryDate': 'max',
            'FullyDelivered': 'all',
            'Naam': 'first'
        }).reset_index()

        grouped['DeliveryDelay'] = (grouped['DeliveryDate'] - grouped['ExpectedDeliveryDate']).dt.days
        grouped['Category'] = grouped['DeliveryDelay'].apply(
            lambda x: 'Early' if x < 0 else 'On Time' if x == 0 else 'Late'
        )

        summary = grouped.groupby(['Naam', 'Category']).size().reset_index(name='Count')
        pivot_df = summary.pivot(index='Naam', columns='Category', values='Count').fillna(0)

        if not pivot_df.empty:
            pivot_df['Total'] = pivot_df.sum(axis=1)
            pivot_df = pivot_df.sort_values(by='Total', ascending=False)
            pivot_df = pivot_df.drop(columns='Total')

        pivot_df = pivot_df.reset_index()

        fig = px.bar(
            pivot_df,
            x='Naam',
            y=['Early', 'On Time', 'Late'],
            title="Order-level Delivery Timeliness per Supplier",
            labels={'value': 'Number of Orders', 'variable': 'Category'},
            hover_name='Naam'
        )
        fig.update_layout(barmode='stack', xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_delivery_counts(self):
        st.info("Toont het totaal aantal levermomenten per leverancier, gemeten op regelniveau.")

        grouped = self.filtered_df.groupby('Naam')['DeliveryCount'].sum().reset_index()
        if grouped.empty:
            st.info("No deliveries registered.")
            return

        grouped = grouped.sort_values(by='DeliveryCount', ascending=False)

        fig = px.bar(grouped, x='Naam', y='DeliveryCount',
                     title="Total Deliveries per Supplier (Order Line Level)",
                     hover_data=['Naam', 'DeliveryCount'],
                     color_discrete_sequence=['orange'])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_missing_delivery_date(self):
        st.info("Geeft per leverancier aan hoeveel orderregels nog geen leverdatum hebben.")

        df = self.filtered_df[self.filtered_df['DeliveryDate'].isna()]
        if df.empty:
            st.info("All order lines are delivered.")
            return

        counts = df['Naam'].value_counts().reset_index()
        counts.columns = ['Supplier', 'Count']
        counts = counts.sort_values(by='Count', ascending=False)

        fig = px.bar(counts, x='Supplier', y='Count',
                     title="Order Lines without Actual Delivery Date",
                     hover_data=['Supplier', 'Count'],
                     labels={'Count': 'Number of Order Lines'},
                     height=400)
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_fully_delivered(self):
        st.info("Laat per leverancier het aantal orderregels zien die volledig geleverd zijn.")

        delivered = self.filtered_df[self.filtered_df['FullyDelivered'] == True]
        if delivered.empty:
            st.info("No fully delivered order lines found.")
            return

        counts = delivered['Naam'].value_counts().reset_index()
        counts.columns = ['Supplier', 'Count']
        counts = counts.sort_values(by='Count', ascending=False)

        fig = px.bar(counts, x='Supplier', y='Count',
                     title="Fully Delivered Order Lines",
                     hover_data=['Supplier', 'Count'],
                     color_discrete_sequence=['lightgreen'])
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def plot_performance_over_time(self):
        st.info("Visualiseert de maandelijkse frequentie van leveringen per leverancier.")

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
