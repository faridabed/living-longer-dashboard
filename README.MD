# Living Longer, But Living Better?

**Student:** Farida Bedewy  
**Class:** I2-BIO  
**Project:** Individual Student Project – Data Storytelling with Streamlit

## Project Description

This project explores life expectancy and healthy life years across European countries between 2004 and 2024 using Python and Streamlit.

The main research question is:

**Are Europeans living longer, or are they living healthier?**

The goal is to compare life expectancy with the number of years lived in good health and explore differences between countries and between women and men.

## Dataset

**Source:** Eurostat  
**Dataset:** Healthy life years by sex (`hlth_hlye`)

The dataset contains information about life expectancy and healthy life years by country, year and sex.

## Tools

- Python
- Streamlit
- Pandas
- Plotly

## Dashboard Features

- Interactive filters by country, year and population
- Key indicators (life expectancy, healthy life years and healthy life share)
- Evolution of life expectancy over time
- Comparison between European countries
- Interactive European map
- Comparison between women and men
- Data quality checks

## Data Limitations

Some data may be missing or provisional. Differences in statistical methods can also affect comparisons between countries and over time.

The results show trends and differences, but do not explain their causes.

## How to Run

Install the required libraries:
pip install -r requirements.txt

Run the application:
streamlit run app.py
