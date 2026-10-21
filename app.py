import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Living Longer, But Living Better?", layout="wide")

# 1. Load and prepare Eurostat data
@st.cache_data
def load_data():
    raw = pd.read_csv("data/hlth_hlye_linear_2_0.csv.gz", compression="gzip")

    data = raw[[
        "geo", "Geopolitical entity (reporting)", "TIME_PERIOD", "sex",
        "hlth_hle", "unit", "OBS_VALUE", "OBS_FLAG"
    ]].copy()

    data = data.rename(columns={
        "geo": "country_code",
        "Geopolitical entity (reporting)": "country",
        "TIME_PERIOD": "year",
        "hlth_hle": "indicator",
        "OBS_VALUE": "value",
        "OBS_FLAG": "observation_flag"
    })

    codes = ["LE_Y0", "HLY_Y0", "HLY_LE_Y0_PC"]
    data = data[data["indicator"].isin(codes)].copy()
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    return raw, data


raw, data = load_data()


st.title("Living Longer, But Living Better?")
st.caption("Healthy life expectancy in Europe, 2004–2024")

st.markdown("### Research question")
st.markdown("**Are Europeans living longer, or are they living healthier?**")

st.write(
    "This dashboard explores life expectancy and healthy life years "
    "across European countries, including differences between women and men."
)

st.caption("Source: Eurostat — Healthy life years by sex (hlth_hlye).")

st.divider()


# The European Union totals are not individual countries.
countries_data = data[~data["country_code"].isin(["EU27_2020", "EU28"])]

# 2. Sidebar filters
with st.sidebar:
    st.header("Filters")
    countries = sorted(countries_data["country"].unique())
    country = st.selectbox("Country", countries, index=countries.index("France"))

    sex_options = {"Total": "T", "Female": "F", "Male": "M"}
    sex_label = st.selectbox("Population", list(sex_options))
    sex = sex_options[sex_label]

    available_years = sorted(
        data[(data["country"] == country) & (data["sex"] == sex)]["year"]
        .dropna().astype(int).unique(), reverse=True
    )
    year = st.selectbox("Reference year", available_years)
    period = st.slider("Trend period", 2004, 2024, (2004, 2024))

# 3. Key indicators
selected = data[
    (data["country"] == country) &
    (data["year"] == year) &
    (data["sex"] == sex)
]


def indicator_value(code):
    values = selected[selected["indicator"] == code]["value"].dropna()
    if values.empty:
        return None
    return values.iloc[0]


def label_value(value, unit):
    if value is None:
        return "N/A"
    return f"{value:.1f}{unit}"


life = indicator_value("LE_Y0")
healthy = indicator_value("HLY_Y0")
share = indicator_value("HLY_LE_Y0_PC")

st.subheader(f"{country} — {year} ({sex_label})")

c1, c2, c3 = st.columns(3, gap="medium", border=True)

c1.metric("Life expectancy", label_value(life, " years"))
c2.metric("Healthy life years", label_value(healthy, " years"))
c3.metric("Healthy life share", label_value(share, "%"))

flags = selected[selected["observation_flag"].notna()]

if not flags.empty:
    st.caption("Some data are provisional or flagged. See Data and methods.")

# 4. Dashboard sections
trend_tab, comparison_tab, gender_tab, quality_tab = st.tabs([
    "Evolution", "Country comparison", "Women and men", "Data and methods"
])

with trend_tab:
    st.subheader("Life expectancy over time")

    st.write(
        "How have life expectancy and healthy life years changed over time?"
    )

    trend = data[
        (data["country"] == country) &
        (data["sex"] == sex) &
        (data["year"].between(period[0], period[1])) &
        (data["indicator"].isin(["LE_Y0", "HLY_Y0"]))
    ].dropna(subset=["value"]).copy()

    trend["Measure"] = trend["indicator"].replace({
        "LE_Y0": "Life expectancy", "HLY_Y0": "Healthy life years"
    })

    if trend.empty:
        st.info("No data for this selection.")
    else:
        fig = px.line(
            trend.sort_values("year"), x="year", y="value", color="Measure",
            markers=True, labels={"year": "Year", "value": "Years at birth"},
            color_discrete_map={
                "Life expectancy": "#487FA5", "Healthy life years": "#699D98"
            }, hover_data=["observation_flag"]
        )
        fig.update_layout(hovermode="x unified", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

        # Compare the earliest and latest years with both indicators available.
        life_years = trend[trend["indicator"] == "LE_Y0"].set_index("year")["value"]
        healthy_years = trend[trend["indicator"] == "HLY_Y0"].set_index("year")["value"]
        common_years = sorted(set(life_years.index) & set(healthy_years.index))
        if len(common_years) >= 2:
            first, last = common_years[0], common_years[-1]
            life_change = life_years.loc[last] - life_years.loc[first]
            healthy_change = healthy_years.loc[last] - healthy_years.loc[first]

            st.write(
                f"From {first} to {last}: "
                f"life expectancy {life_change:+.1f} years, "
                f"healthy life years {healthy_change:+.1f} years."
            )
            
            # Interpret the evolution
            if life_change > 0 and healthy_change > 0:
                if life_change > healthy_change:
                    st.write(
                        "Life expectancy increased faster than healthy life years."
                    )
                elif healthy_change > life_change:
                    st.write(
                        "Healthy life years increased faster than life expectancy."
                    )
                else:
                    st.write(
                        "Both indicators increased by the same amount."
                    )
            elif life_change < 0 and healthy_change < 0:
                st.write("Both indicators decreased during this period.")
            else:
                st.write(
                    "Life expectancy and healthy life years followed different trends."
                )

        else:
            st.caption("At least two comparable years are needed to calculate change.")
    st.caption("Provisional data and changes in methodology may affect comparisons over time.")

with comparison_tab:
    st.subheader("Comparison between countries")
    comparison = countries_data[
        (countries_data["year"] == year) &
        (countries_data["sex"] == sex) &
        (countries_data["indicator"] == "HLY_Y0")
    ].dropna(subset=["value"]).copy()

    if comparison.empty:
        st.info("No country data available for this selection.")
    else:
        st.caption(f"{len(comparison)} countries with available data in {year}.")
        comparison = comparison.sort_values("value")
        # Choose which countries to display
        ranking = st.selectbox(
            "Show countries",
            ["Top 10", "Bottom 10", "All countries"]
        )

        if ranking == "Top 10":
            chart_data = comparison.nlargest(10, "value")

        elif ranking == "Bottom 10":
            chart_data = comparison.nsmallest(10, "value")

        else:
            chart_data = comparison.copy()

        chart_data = chart_data.sort_values("value")
        bar = px.bar(
            chart_data, x="value", y="country", orientation="h",
            labels={"value": "Healthy life years (years)", "country": "Country"},
            color_discrete_sequence=["#487FA5"], hover_data=["observation_flag"]
        )
        bar.update_layout(height=max(400, 25 * len(chart_data) + 100))
        st.plotly_chart(bar, use_container_width=True)

        
        # Country comparison interpretation
        highest = comparison.loc[comparison["value"].idxmax()]
        lowest = comparison.loc[comparison["value"].idxmin()]

        difference = highest["value"] - lowest["value"]

        st.write(
            f"In {year}, {highest['country']} had the highest "
            f"number of healthy life years ({highest['value']:.1f}), "
            f"while {lowest['country']} had the lowest "
            f"({lowest['value']:.1f})."
        )

        st.write(
            f"The difference between these countries was "
            f"{difference:.1f} years."
        )


        st.markdown("**Healthy life years in Europe**")
        # Eurostat uses two-letter country codes. Plotly's map needs ISO-3 codes.
        iso3 = {
            "AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
            "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC",
            "ES": "ESP", "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN",
            "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
            "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
            "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
            "UK": "GBR"
        }
        comparison["iso3"] = comparison["country_code"].map(iso3)
        map_data = comparison.dropna(subset=["iso3"])
        map_fig = px.choropleth(
            map_data, locations="iso3", color="value", hover_name="country",
            scope="europe", color_continuous_scale="Teal",
            labels={"value": "Healthy years"}, hover_data=["observation_flag"]
        )
        # Improve map display
        map_fig.update_geos(
            scope="europe",
            projection_type="mercator",
            lataxis_range=[34, 72],
            lonaxis_range=[-12, 35],
            showframe=False,
            showcountries=True,
            bgcolor="rgba(0,0,0,0)"
        )

        map_fig.update_layout(
            height=650,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(map_fig, use_container_width=True)
        st.caption("Countries without available observations are not colored.")

with gender_tab:
    st.subheader("Differences between women and men")

    # Select data for women and men
    gender_data = data[
        (data["country"] == country) &
        (data["year"] == year) &
        (data["sex"].isin(["F", "M"])) &
        (data["indicator"].isin(["LE_Y0", "HLY_Y0"]))
    ].copy()

    # Rename categories
    gender_data["Gender"] = gender_data["sex"].replace({
        "F": "Female",
        "M": "Male"
    })

    gender_data["Indicator"] = gender_data["indicator"].replace({
        "LE_Y0": "Life expectancy",
        "HLY_Y0": "Healthy life years"
    })

    # Create the chart
    fig_gender = px.bar(
        gender_data,
        x="Gender",
        y="value",
        color="Indicator",
        barmode="group",
        text="value",
        labels={"value": "Years"},
        color_discrete_map={
            "Life expectancy": "#487FA5",
            "Healthy life years": "#699D98"
        }
    )

    fig_gender.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside"
    )

    fig_gender.update_layout(
    height=450,
    yaxis_title="Years",
    showlegend=True,
    legend_title_text="",
    legend=dict(
        orientation="h",
        y=1.12,
        x=0
    )
)

    st.plotly_chart(fig_gender, use_container_width=True)

    
    # Compare women and men
    gender_values = gender_data.pivot(
        index="Gender",
        columns="Indicator",
        values="value"
    )

    if gender_values.notna().all().all() and len(gender_values) == 2:
        life_gap = (
            gender_values.loc["Female", "Life expectancy"]
            - gender_values.loc["Male", "Life expectancy"]
        )

        healthy_gap = (
            gender_values.loc["Female", "Healthy life years"]
            - gender_values.loc["Male", "Healthy life years"]
        )

        st.write(
            f"Life expectancy difference (female - male): "
            f"{life_gap:+.1f} years."
        )

        st.write(
            f"Healthy life years difference (female - male): "
            f"{healthy_gap:+.1f} years."
        )


    st.caption(
        "Comparison of life expectancy and healthy life years "
        "between women and men."
    )


with quality_tab:
    st.subheader("Data and methodology")
    st.write("Source: Eurostat, hlth_hlye (Healthy life years by sex).")
    q1, q2, q3 = st.columns(3)
    q1.metric("Original rows", len(raw))
    q2.metric("Selected rows", len(data))
    duplicates = data.duplicated(["country_code", "year", "sex", "indicator"]).sum()
    q3.metric("Duplicate observations", int(duplicates))

    st.markdown("**Missing values**")
    st.dataframe(data.isna().sum().rename("Missing values"), use_container_width=True)

    st.markdown("**Indicator validation**")
    checks = data.groupby("indicator")["value"].agg(["count", "min", "max", "mean"]).round(2)
    st.dataframe(checks, use_container_width=True)
    bad_percentage = data[(data["indicator"] == "HLY_LE_Y0_PC") & (~data["value"].between(0, 100))]
    bad_years = data[(data["indicator"].isin(["LE_Y0", "HLY_Y0"])) & (data["value"] < 0)]
    st.write("Out-of-range observations:", len(bad_percentage) + len(bad_years))

    st.markdown("**Observation flags**")
    st.dataframe(data["observation_flag"].fillna("No flag").value_counts().rename("Rows"))
    st.caption("p: provisional; b: break in series; e: estimated; u: low reliability. Flags may be combined.")

    st.markdown("**Method and limitations**")
    st.write("Life expectancy estimates years of life under current mortality conditions. Healthy life years estimate years without activity limitations.")
    st.write("Some observations are provisional or not available. Changes in methodology may affect trends. Country differences do not prove causality.")
    with st.expander("View the selected dataset"):
        st.dataframe(data, use_container_width=True)
    st.markdown("[Eurostat data source](https://ec.europa.eu/eurostat/databrowser/view/hlth_hlye/default/table?lang=en)")

# General conclusion
st.subheader("Conclusion")

st.write(
    "The results show that living longer does not always "
    "mean living healthier."
)

st.write(
    "Life expectancy and healthy life years do not always "
    "increase at the same rate. We can also observe differences "
    "between European countries and between women and men."
)

st.write(
    "This shows why it is important to consider both indicators "
    "when studying population health."
)
st.divider()
st.caption("Source: Eurostat (hlth_hlye).")
