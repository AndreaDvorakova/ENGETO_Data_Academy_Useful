#import knihoven
import streamlit as st
import numpy as np
import pandas as pd
import pymysql
import sqlalchemy
import altair as alt

#tvorba sidebar a vice stranek
page = st.sidebar.radio('Page', ['Testing', 'Super Graf'])


if page == 'Testing':

    #spojeni s databazi
    conn_string = "mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com/data_academy_02_2022"
    engine = sqlalchemy.create_engine(conn_string)
        
    #data zemepisne a teploty
    query = """
    SELECT
        north, 
        yearly_average_temperature
    FROM countries
    WHERE 1=1
        AND yearly_average_temperature IS NOT NULL
        AND north IS NOT NULL
    """
    df = pd.read_sql(query, engine)

    #tvorba grafu 1
    chart1 = alt.Chart(df).mark_circle().encode(
        x='north',
        y='yearly_average_temperature',
        tooltip = ['north', 'yearly_average_temperature']
    ).interactive()


    #data CR covid testy
    query_test = """
        SELECT
            *
        FROM covid19_tests
        WHERE 1=1
            AND country IN ('Czech Republic', 'Austria', 'Slovakia')
    """
    df_tests = pd.read_sql(query_test, engine)
    df_tests.dropna(inplace= True)
    df_tests['date'] = pd.to_datetime(df_tests['date'])


    #tvorba grafu 2
    selection = alt.selection_multi(fields=['country'], bind='legend')

    chart2 = alt.Chart(df_tests).mark_line().encode(
        x=alt.X('date', axis= alt.Axis(format=('%Y-%m-%d'), labelAngle=45)),
        y='tests_performed',
        color='country',
        opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    ).properties(
        width=700
    ).add_selection(selection).interactive()

    c1, c2 = st.columns((1,2))

    c1.altair_chart(chart1, use_container_width=True)
    c2.altair_chart(chart2, use_container_width=True)

elif page == 'Super Graf':
    
    #spojeni s databazi
    conn_string = "mysql+pymysql://data-student:u9AB6hWGsNkNcRDm@data.engeto.com/data_academy_02_2022"
    engine = sqlalchemy.create_engine(conn_string)

    query_price = """
        SELECT 
            DATE(a.date_from) AS date,
            a.value,
            b.name AS product, 
            c.name AS location
        FROM czechia_price a
        LEFT JOIN czechia_price_category b
            ON a.category_code = b.code
        LEFT JOIN czechia_region c
            ON a.region_code = c.code
        WHERE c.name IS NOT NULL
        """
    df = pd.read_sql(query_price, engine)

    #nacteni unikatnich hodnot potravinovych kategorii
    product_options_query = """
        SELECT
            DISTINCT name
        FROM czechia_price_category
    """

    #unikatni nazvy produktu se nactou do dataframu a pak se z nich vytvori list
    product_options_dataframe = pd.read_sql(product_options_query, engine)
    product_options_list = product_options_dataframe['name'].to_list()
    #z listu se vztvori sidebar, ktery se chova jako selectionbox
    product_choice = st.sidebar.selectbox('Product', product_options_list)

    region_options_query = """
        SELECT
            DISTINCT name
        FROM czechia_region
    """
    #unikatni nazvy regionu se nactou do dataframu a pak se z nich vytvori list
    region_options_dataframe = pd.read_sql(region_options_query, engine)
    region_options_list = region_options_dataframe['name'].to_list()
    #z listu se vztvori sidebar, ktery se chova jako selectionbox
    region_choice = st.sidebar.multiselect('Region', region_options_list, default='Hlavní město Praha')

    #omezeni dataframu na zaklade vyberu v sidebar
    df = df[(df['product']== product_choice) & (df['location'].isin(region_choice))]
    

    #pomocny = abyc vybrala na jednom grafu cast podle x osy
    brush = alt.selection(type = 'interval', encodings = ['x'])
    #pro oznaceni jednotlivych dat, zbytek zasedne
    selection = alt.selection_multi(fields=['location'], bind='legend')

    #zaklad pro vsechny grafy
    base = alt.Chart(df).mark_line().encode(
        x='date:T',
        y='value:Q',
        color = 'location',
        opacity = alt.condition(selection, alt.value(1), alt.value(0.2))
    ).add_selection(
        selection
    )

    #horni graf se automaticky upravuje podle brush vyberu ve spodnim grafu
    upper = base.encode(
        alt.X('date', scale=alt.Scale(domain=brush)),
    ).properties(width=700)

    #spodni graf
    lower = base.properties(height=60, width=700).add_selection(brush)

    c1, c2, c3 = st.columns((1,5,1))

    c2.markdown('# Product prices by regions')

    #prontuje grafy do containeru, aby se automaticky roztahly na celou sirku
    st.altair_chart(upper & lower, use_container_width=True)

    #base
    #st.altair_chart(base, use_container_width=True)

    

    
