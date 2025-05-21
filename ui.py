import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
st.set_page_config(layout="wide")
class UI:
    def __init__(self, df):
        self.original_df = df.copy()
        self.selected_year = None
        self.selected_suppliers = None
        self.filtered_df = df.copy()

    def year_selection(self):
        years = sorted(self.original_df['Datum'].dt.year.unique())
        self.selected_year = st.selectbox('Selecteer een jaar voor de analyse:', years)
        self.filtered_df = self.original_df[self.original_df['Datum'].dt.year == self.selected_year]

    def supplier_selection(self):
        if self.filtered_df.empty:
            st.warning("Geen data beschikbaar voor het geselecteerde jaar.")
            return

        suppliers = sorted(self.filtered_df['Naam'].dropna().unique())
        self.selected_suppliers = st.multiselect('Selecteer leveranciers:', suppliers)

        if self.selected_suppliers:
            self.filtered_df = self.filtered_df[self.filtered_df['Naam'].isin(self.selected_suppliers)]

    def show_date_analysis(self):
        if self.filtered_df.empty:
            st.warning("Geen data beschikbaar na filtering.")
            return

        st.subheader(f"Analyse voor jaar {self.selected_year}")
        tabs = st.tabs([
            "Geen Leverdatum", 
            "Volledig Geleverd", 
            "Aantal Leveringen", 
            "Tijdsprestatie"
        ])

        with tabs[0]:
            self.plot_missing_delivery_date()

        with tabs[1]:
            self.plot_fully_delivered()

        with tabs[2]:
            self.plot_delivery_counts()

        with tabs[3]:
            self.plot_performance_over_time()

    def plot_missing_delivery_date(self):
        df = self.filtered_df[self.filtered_df['DeliveryDate'].isna()]
        if df.empty:
            st.info("Alle bestellingen zijn geleverd of hebben een leverdatum.")
            return

        counts = df['Naam'].value_counts()
        plt.figure(figsize=(20, 6))  # Verbreden
        sns.barplot(x=counts.index, y=counts.values, color='salmon')
        plt.xticks(rotation=45, ha='right')
        plt.title("Bestellingen zonder daadwerkelijke leverdatum")
        plt.xlabel("Leverancier")
        plt.ylabel("Aantal")
        st.pyplot(plt.gcf(), use_container_width=True)

    def plot_fully_delivered(self):
        delivered = self.filtered_df[self.filtered_df['FullyDelivered'] == True]
        if delivered.empty:
            st.info("Geen volledig geleverde bestellingen gevonden.")
            return

        counts = delivered['Naam'].value_counts()
        plt.figure(figsize=(20, 6))  # Verbreden
        sns.barplot(x=counts.index, y=counts.values, color='lightgreen')
        plt.xticks(rotation=45, ha='right')
        plt.title("Volledig Geleverde Bestellingen")
        plt.xlabel("Leverancier")
        plt.ylabel("Aantal")
        st.pyplot(plt.gcf(), use_container_width=True)

    def plot_delivery_counts(self):
        grouped = self.filtered_df.groupby('Naam')['DeliveryCount'].sum()
        if grouped.empty:
            st.info("Geen leveringen geregistreerd.")
            return

        plt.figure(figsize=(20, 6))  # Verbreden
        sns.barplot(x=grouped.index, y=grouped.values, color='orange')
        plt.xticks(rotation=45, ha='right')
        plt.title("Totaal aantal leveringen per leverancier")
        plt.xlabel("Leverancier")
        plt.ylabel("Aantal leveringen")
        st.pyplot(plt.gcf(), use_container_width=True)

    def plot_performance_over_time(self):
        df = self.filtered_df.copy()
        df['YearMonth'] = df['Datum'].dt.to_period('M').astype(str)
        timeseries = df.groupby(['YearMonth', 'Naam'])['DeliveryCount'].sum().unstack()
        if timeseries.empty:
            st.info("Geen tijdsgebonden leveringsdata beschikbaar.")
            return

        timeseries.plot(figsize=(20, 6))  # Verbreden
        plt.title("Leverfrequentie per maand")
        plt.xlabel("Maand")
        plt.ylabel("Aantal Leveringen")
        plt.xticks(rotation=45)
        st.pyplot(plt.gcf(), use_container_width=True)
