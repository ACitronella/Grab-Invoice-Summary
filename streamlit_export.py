from sklearn.linear_model import LinearRegression
import numpy as np
import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

EXTRACTED_INFO_FILE = "data/extracted_info.json"
kernel_size = 7
legend_position_dict = dict(x=0.01,y=0.99)
def hover_text_apply(row):
    return f"Money (Baht): {row[money_column_name]:.2f},distance (km): {row[dist_column_name]:.2f},Money Over Distance: {row[money_over_dist_column_name]:.2f}"

with open(EXTRACTED_INFO_FILE) as f:
    data = json.load(f)
invoice_df = pd.DataFrame(data)
invoice_df["datetime"] = invoice_df["ts"].apply(datetime.fromtimestamp)
invoice_df["datetime_str"] = invoice_df["datetime"].apply(lambda dt:f"{dt.year}/{dt.month}/{dt.day}")

st.set_page_config(
    page_title="Grab Usage Summary",
    page_icon="📊"
)
st.write("""
# Grab Usage Summary
         
Select date range and type of service
""")

service_types = invoice_df["type"].unique()
start_date = st.date_input("Start Date", value=invoice_df["datetime"].min())
end_date = st.date_input("End Date") + timedelta(days=1) 
service = st.selectbox("Type of service", options=service_types)
compuation_start_date = start_date - timedelta(days=kernel_size+1)
# compuation_end_date = end_date - timedelta(days=7)

filtered_invoice_df = invoice_df[invoice_df["type"] == service]
filtered_invoice_df = filtered_invoice_df[(filtered_invoice_df["datetime"].apply(lambda x: x >= pd.Timestamp(compuation_start_date))) & (invoice_df["datetime"].apply(lambda x: x <= pd.Timestamp(end_date)))]

if service == "GrabTaxi":
    money_column_name = "money (฿)"
    dist_column_name = "distance (km)"
    money_over_dist_column_name = "money_over_distance"

    filtered_invoice_df[money_over_dist_column_name] = filtered_invoice_df[money_column_name] / filtered_invoice_df[dist_column_name]
    filtered_invoice_df["date"] = filtered_invoice_df["datetime"].apply(lambda x: x.date())
    invoice_groupby_date_df = filtered_invoice_df.groupby("date")
    running_average_df = pd.DataFrame(index=[start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)], columns=[money_column_name, dist_column_name, money_over_dist_column_name], dtype=float)
    running_average_df.index.rename("date", inplace=True)
    running_average_df.loc[:, :] = 0
    running_average_money = invoice_groupby_date_df[money_column_name].mean().rolling(window=kernel_size).mean()
    running_average_dist = invoice_groupby_date_df[dist_column_name].mean().rolling(window=kernel_size).mean()
    running_average_mod = invoice_groupby_date_df[money_over_dist_column_name].mean().rolling(window=kernel_size).mean()
    running_average_df[money_column_name] = running_average_df[money_column_name].add(running_average_money, fill_value=0)
    running_average_df[dist_column_name] = running_average_df[dist_column_name].add(running_average_dist, fill_value=0)
    running_average_df[money_over_dist_column_name] = running_average_df[money_over_dist_column_name].add(running_average_mod, fill_value=0)
    filtered_invoice_df = filtered_invoice_df[(filtered_invoice_df["datetime"].apply(lambda x: x >= pd.Timestamp(start_date))) & (invoice_df["datetime"].apply(lambda x: x <= pd.Timestamp(end_date)))]
    
    mean_money = filtered_invoice_df[money_column_name].mean()
    sum_money = filtered_invoice_df[money_column_name].sum()
    mean_dist = filtered_invoice_df[dist_column_name].mean()
    sum_dist = filtered_invoice_df[dist_column_name].sum()
    mean_money_per_dist = (filtered_invoice_df[money_over_dist_column_name]).mean()

    filtered_invoice_df["hover_text"] = filtered_invoice_df.apply(hover_text_apply, axis=1)

    money_usage_fig = px.scatter(
        filtered_invoice_df,
        x="datetime",
        y=money_column_name,
        title=f"{service} Money Usage (Baht)",
        range_x=(start_date, end_date),
        range_y=(0., filtered_invoice_df[money_column_name].max()*1.1),
        custom_data=["hover_text"]
    )
    money_usage_fig.add_hline(y=mean_money, line_color="red", line_dash="dash", annotation_text=f"Avg money spend per trip = {mean_money:.2f} Baht", annotation_position="top left")
    money_usage_fig.add_scatter(
        x=running_average_df.index,
        y=running_average_df[money_column_name],
        name=f"Running Average Money per day (window={kernel_size})"
    )
    money_usage_fig.update_layout(legend=legend_position_dict)
    money_usage_fig.update_traces(
        hovertemplate="%{customdata[0]}<br>%{x}<extra></extra>"
    )
    st.write("## Money Paid")
    st.plotly_chart(money_usage_fig)
    st.write(f"Average Money Paid: {mean_money:.1f} Baht per trip")
    st.write(f"All Money Paid: {sum_money:.1f} Baht")

    
    dist_fig = px.scatter(
        filtered_invoice_df,
        x="datetime",
        y=dist_column_name,
        title=f"{service} Distance (km)",
        range_x=(start_date, end_date),
        range_y=(0., filtered_invoice_df[dist_column_name].max()*1.1),
        custom_data=["hover_text"]
    )
    dist_fig.add_hline(y=mean_dist, line_color="red", line_dash="dash", annotation_text=f"Avg money over distance per trip = {mean_dist:.2f} km", annotation_position="top left")
    dist_fig.add_scatter(
        x=running_average_df.index,
        y=running_average_df[dist_column_name],
        name="Running Average Distance per day",
        # range_x=(start_date, end_date),
    )
    dist_fig.update_layout(legend=legend_position_dict)
    dist_fig.update_traces(
        hovertemplate="%{customdata[0]}<br>%{x}<extra></extra>"
    )
    st.write("## Distance Travelled")
    st.plotly_chart(dist_fig)
    st.write(f"Average Distance traveled: {mean_dist:.2f} km")
    st.write(f"All Distance traveled: {sum_dist:.2f} km")

    money_over_dist_fig = px.scatter(
        filtered_invoice_df,
        x="datetime",
        y="money_over_distance",
        title=f"{service} money spend over distance travel (Baht/km)",
        range_y=(start_date, end_date),
        custom_data=["hover_text"]
    )
    money_over_dist_fig.add_hline(y=mean_money_per_dist, line_color="red", line_dash="dash", annotation_text=f"Avg MOD per trip = {mean_money_per_dist:.2f} Baht/km", annotation_position="top left")
    money_over_dist_fig.add_scatter(
        x=running_average_df.index,
        y=running_average_df[money_over_dist_column_name],
        name="Running Average MOD per day",
        # range_x=(start_date, end_date),
    )
    money_over_dist_fig.update_layout(legend=legend_position_dict)
    money_over_dist_fig.update_traces(
        hovertemplate="%{customdata[0]}<br>%{x}<extra></extra>"
    )
    st.write("## Money over Distance (MOD)")
    st.plotly_chart(money_over_dist_fig)
    st.write(f"Average Money Paid for {service} per distance: {mean_money_per_dist:.2f}")

    
    lr = LinearRegression()
    lr.fit(filtered_invoice_df[dist_column_name].values[:, np.newaxis], filtered_invoice_df[money_column_name].values)
    dist_money_fig = px.scatter(filtered_invoice_df, x=dist_column_name, y=money_column_name)
    dist_money_fig.add_scatter(
        x=filtered_invoice_df[dist_column_name],
        y=lr.predict(filtered_invoice_df[dist_column_name].values[:, np.newaxis]),
        name=f"M(d) = {lr.coef_[0]:.2f}*d + {lr.intercept_:.2f}",
        line_color="red", line_dash="dash"
    )
    dist_money_fig.update_layout(legend=legend_position_dict)
    st.plotly_chart(dist_money_fig)
    

    st.write("Maybe add per week data later")
else:
    st.dataframe(filtered_invoice_df, hide_index=True)