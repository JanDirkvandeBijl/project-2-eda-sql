import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

class UI:
    def __init__(self, df_inkooporderregels):
        self.df_inkooporderregels = df_inkooporderregels
        self.selected_year = None
        self.selected_suppliers = None
        self.filtered_df = None

    def year_selection(self):
        # Year input via Streamlit
        self.selected_year = st.selectbox('Selecteer een jaar voor de analyse:', self.df_inkooporderregels['Datum'].dt.year.unique())

        # Filter the data for the selected year
        self.filtered_df = self.df_inkooporderregels[self.df_inkooporderregels['Datum'].dt.year == self.selected_year]

    def supplier_selection(self):
        # Multiselect filter for suppliers
        supplier_options = self.df_inkooporderregels['Naam'].unique()
        self.selected_suppliers = st.multiselect('Selecteer leveranciers voor de analyse:', supplier_options)

        # Filter the data for the selected suppliers
        if self.selected_suppliers:
            self.filtered_df = self.filtered_df[self.filtered_df['Naam'].isin(self.selected_suppliers)]

    def show_date_analysis(self):
        if self.selected_year is None or self.filtered_df is None:
            return

        # Date-related plots
        st.subheader('Date Analysis for Troubleshooting Suppliers')

        # ** Missing Deliveries per Supplier **
        st.write(f"""
        Deze grafiek toont het aantal bestellingen die niet geleverd zijn per leverancier voor het jaar {self.selected_year}. 
        Dit helpt bij het identificeren van leveranciers die niet voldoen aan de afgesproken leveringen.
        """)

        # Grouping by Supplier ('Naam') and counting missing deliveries (TotalDeliveries == 0)
        missing_deliveries = self.filtered_df[self.filtered_df['TotalDeliveries'] == 0].groupby('Naam').size()

        plt.figure(figsize=(12, 6))
        sns.barplot(x=missing_deliveries.index, y=missing_deliveries.values, color='salmon')
        plt.title(f'Missing Deliveries per Supplier voor {self.selected_year}')
        plt.xlabel('Leverancier')
        plt.ylabel('Aantal Ontbrekende Leveringen')
        plt.xticks(rotation=90)
        st.pyplot(fig=plt.gcf())

        # ** Late Deliveries per Supplier **
        st.write(f"""
        Deze grafiek toont het aantal vertraagde leveringen per leverancier voor het jaar {self.selected_year}. 
        Een vertraging in de levering wordt gedefinieerd als een afwijking van de afgesproken leverdatum.
        """)

        # Identifying late deliveries based on AfwijkendeAfleverdatum
        late_deliveries = self.filtered_df[self.filtered_df['AfwijkendeAfleverdatum'].notna()]
        late_deliveries_count = late_deliveries.groupby('Naam').size()

        plt.figure(figsize=(12, 6))
        sns.barplot(x=late_deliveries_count.index, y=late_deliveries_count.values, color='orange')
        plt.title(f'Vertraagde Leveringen per Supplier voor {self.selected_year}')
        plt.xlabel('Leverancier')
        plt.ylabel('Aantal Vertraagde Leveringen')
        plt.xticks(rotation=90)
        st.pyplot(fig=plt.gcf())

        # ** Deliveries per Supplier **
        st.write(f"""
        Deze grafiek toont het aantal leveringen per leverancier voor het jaar {self.selected_year}. 
        Dit helpt bij het identificeren van leveranciers die mogelijk niet genoeg leveren.
        """)

        deliveries_per_supplier = self.filtered_df.groupby('Naam')['TotalDeliveries'].sum()

        plt.figure(figsize=(12, 6))
        sns.barplot(x=deliveries_per_supplier.index, y=deliveries_per_supplier.values, color='lightgreen')
        plt.title(f'Aantal Leveringen per Leverancier voor {self.selected_year}')
        plt.xlabel('Leverancier')
        plt.ylabel('Aantal Leveringen')
        plt.xticks(rotation=90)
        st.pyplot(fig=plt.gcf())

        # ** Supplier Delivery Frequency vs Order Volume **
        st.write(f"""
        Deze grafiek toont de verhouding tussen de frequentie van leveringen en het ordervolume per leverancier voor het jaar {self.selected_year}. 
        Leveranciers met een lage leverfrequentie kunnen mogelijk problemen hebben.
        """)

        # Delivery frequency vs. order volume (TotalOrders per Supplier)
        delivery_frequency = self.filtered_df.groupby('Naam').size()
        order_volume = self.filtered_df.groupby('Naam')['GuLiIOR'].count()  # Number of orders per supplier

        # Merging delivery frequency and order volume
        delivery_data = pd.DataFrame({
            'DeliveryFrequency': delivery_frequency,
            'OrderVolume': order_volume
        })

        plt.figure(figsize=(12, 6))
        sns.scatterplot(x='OrderVolume', y='DeliveryFrequency', data=delivery_data, hue='DeliveryFrequency', palette='viridis')
        plt.title(f'Leverancier Leverfrequentie vs Ordervolume voor {self.selected_year}')
        plt.xlabel('Ordervolume')
        plt.ylabel('Leverfrequentie')
        st.pyplot(fig=plt.gcf())

        # ** Performance Over Time **
        st.write(f"""
        Deze grafiek toont de prestaties van de leveranciers over de tijd voor het jaar {self.selected_year}. 
        Door de prestaties over de tijd te bekijken, kunnen we zien of leveranciers steeds minder goed presteren.
        """)

        # Group by Year and Month and calculate total deliveries over time for each supplier
        self.filtered_df['YearMonth'] = self.filtered_df['Datum'].dt.to_period('M')
        supplier_performance = self.filtered_df.groupby(['YearMonth', 'Naam'])['TotalDeliveries'].sum().unstack()

        supplier_performance.plot(figsize=(12, 6))
        plt.title(f'Leverancier Prestatie Over Tijd voor {self.selected_year}')
        plt.xlabel('Maand')
        plt.ylabel('Aantal Leveringen')
        st.pyplot(fig=plt.gcf())
