import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

class UI:
    def __init__(self, df_inkooporderregels):
        self.df_inkooporderregels = df_inkooporderregels
        self.selected_year = None
        self.filtered_df = None

    def year_selection(self):
        # Year input via Streamlit
        self.selected_year = st.selectbox('Selecteer een jaar voor de analyse:', self.df_inkooporderregels['Datum'].dt.year.unique())

        # Filter the data for the selected year
        self.filtered_df = self.df_inkooporderregels[self.df_inkooporderregels['Datum'].dt.year == self.selected_year]

    def show_date_analysis(self):
        if self.selected_year is None or self.filtered_df is None:
            return

        # Date-related plots
        st.subheader('Date Analysis')

        # Plotting the 'Datum' (Order Date) over time, showing orders per month
        st.write(f"""
        Deze grafiek toont het aantal bestellingen per maand in de dataset voor het jaar {self.selected_year}. 
        De **orderdatum** vertegenwoordigt de datum waarop de inkooporder is aangemaakt of geregistreerd. 
        In de grafiek worden de aantallen bestellingen per maand weergegeven.

        Door de **trends** in de maandelijkse bestellingen te bekijken, kunnen we bijvoorbeeld seizoensgebonden schommelingen, 
        promotieperiodes of andere invloeden op de bestelactiviteit herkennen.

        De **kde (kernel density estimate)** geeft een geschatte verdeling van de orderdatums weer, wat helpt bij het identificeren van 
        gebieden met een hoge concentratie van bestellingen, zelfs als de gegevens op bepaalde dagen relatief laag zijn.

        Let op de x-as (de **maanden**) en de y-as (de **frequentie van bestellingen per maand**).
        """)

        # Extracting year and month from the 'Datum' column
        self.filtered_df['YearMonth'] = self.filtered_df['Datum'].dt.to_period('M')

        # Grouping by the Year-Month period and counting orders
        monthly_orders = self.filtered_df.groupby('YearMonth').size()

        # Convert 'YearMonth' period to datetime and extract month names
        month_names = monthly_orders.index.to_timestamp().month_name().str[:3]  # Get abbreviated month names

        # Plotting the orders per month
        plt.figure(figsize=(12, 6))
        sns.barplot(x=month_names, y=monthly_orders.values, color='skyblue')

        plt.title(f'Aantal Bestellingen per Maand voor {self.selected_year}')
        plt.xlabel('Maand')
        plt.ylabel('Aantal Bestellingen')
        plt.xticks(rotation=45)  # Rotating x-axis labels for better readability
        st.pyplot(fig=plt.gcf())  # Explicitly passing the figure
