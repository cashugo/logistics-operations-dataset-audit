import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

load = pd.read_csv("loads.csv", encoding="latin1")
delivery = pd.read_csv("delivery_events.csv", encoding="latin1")

delivery_data = pd.merge(load, delivery, on="load_id", how="inner")

#Clean column names for faster typing
delivery_data.columns = [c.lower().replace(" ", "_").replace("(", "").replace(")", "") for c in delivery_data.columns]

#Number of rows
row_number = delivery_data.shape


#Finding Null Values Each Column
#for c in delivery_data.columns:
#   print(f"There are {delivery_data[c].isnull().sum()} null values present in {c}")

#ChiSquare
for c in delivery_data.columns:
    contingency_table = pd.crosstab(delivery_data[c], delivery_data["on_time_flag"])
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
#    print(f"P-Value: {p_value} for {c}")

#General Idea for Booking Type
bkng_typ = delivery_data["booking_type"].value_counts()
total_revenue = delivery_data["revenue"].sum()


on_time_data = delivery_data[delivery_data["on_time_flag"] == True]
late_data = delivery_data[delivery_data["on_time_flag"] == False]

total_rev_map = delivery_data.groupby("booking_type")["revenue"].sum()
on_time_rev_map = on_time_data.groupby("booking_type")["revenue"].sum()
late_rev_map = late_data.groupby("booking_type")["revenue"].sum()

fulfillment = delivery_data.groupby("booking_type").agg({"on_time_flag":[
    ("Total", "count"),
    ("On-Time", lambda x: x.sum()),
    ("On-Time %", lambda x: f"{((x.sum() / x.count())*100).round(1)}%"),
    ("Late", lambda x:  x.count() - x.sum()),
    ("Late %", lambda x: f"{(((x.count() - x.sum()) / x.count())*100).round(1)}%"),
],
"revenue" : [("Total Revenue", lambda x: f"${int(x.sum()):,}"),
             ("Revenue Share", lambda x: f"{((int(x.sum()) / total_revenue)*100).round(1)}%"),
             ("Volume", lambda x: f"{int(x.count())} shippings"),
             ("Cost per Shipping",lambda x: f"${int(x.mean()):,}" )
]})

fulfillment["Total Revenue"]   = fulfillment.index.map(lambda x: f"${total_rev_map[x]:,}")
fulfillment["On-Time Revenue"] = fulfillment.index.map(lambda x: f"${on_time_rev_map[x]:,}")
fulfillment["Late Revenue"]    = fulfillment.index.map(lambda x: f"${late_rev_map[x]:,}")
fulfillment["On-Time Revenue Share"] = fulfillment.index.map(lambda x: f"{((on_time_rev_map[x] / total_rev_map[x])*100).round(1)}%")

#55% vs 45% across all Customer Types is unusual, so further basic breakdown is needed
pickup_flag = delivery_data.groupby(["booking_type","event_type"])["on_time_flag"].value_counts(normalize=True)

#Detention
delivery_data["detention_time"] = pd.cut(delivery_data["detention_minutes"], bins=[-1,0,60,np.inf], labels=["None", "Within 1 hr", "More than 1 hr"])
dtntn_tm = delivery_data.groupby(["booking_type","detention_time"])["on_time_flag"].value_counts(normalize=True)

#Datetime
delivery_data["scheduled_datetime"] = pd.to_datetime(delivery_data["scheduled_datetime"])
#Month Year
delivery_data["month_year"] = delivery_data["scheduled_datetime"].dt.strftime("%B %Y")
#Days of the Year
delivery_data["days_of_week"] = delivery_data["scheduled_datetime"].dt.strftime("%A")
#Hours of the Day
delivery_data["hours_of_day"] = delivery_data["scheduled_datetime"].dt.hour

#ChiSquare for Datetime
for d in [delivery_data["month_year"], delivery_data["days_of_week"], delivery_data["hours_of_day"]]:
    contingency_table = pd.crosstab(d, delivery_data["on_time_flag"])
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
    #print(f"P-Value: {p_value}")

daysofyear = pd.crosstab(index=[delivery_data["booking_type"],delivery_data["days_of_week"]],
                                columns=delivery_data["on_time_flag"],
                                normalize="index")

hoursofday = pd.crosstab(index=[delivery_data["booking_type"],delivery_data["hours_of_day"]],
                                columns=delivery_data["on_time_flag"],
                                normalize="index")

#Location
destination_state = pd.crosstab(index=[delivery_data["booking_type"],delivery_data["location_state"]],
                                columns=delivery_data["on_time_flag"],
                                normalize="index")

destination_city = pd.crosstab(index=[delivery_data["booking_type"],delivery_data["location_city"]],
                                columns=delivery_data["on_time_flag"],
                                normalize="index")

#Comparison
comparison_df = destination_city[destination_city[True] < destination_city[False]].reset_index()

spot_df = set(comparison_df[comparison_df["booking_type"] == "Spot"]["location_city"])
dedicated_df = set(comparison_df[comparison_df["booking_type"] == "Dedicated"]["location_city"])
contract_df = set(comparison_df[comparison_df["booking_type"] == "Contract"]["location_city"])

if spot_df == dedicated_df == contract_df:
    print("No Difference")
    print(f"{sorted(list(spot_df))}")
else:
    print("Different")
    print(f"Spot: {len(spot_df)} | {sorted(list(spot_df))}")
    print(f"Dedicated: {len(dedicated_df)} | {sorted(list(dedicated_df))}")
    print(f"Contract: {len(contract_df)} | {sorted(list(contract_df))}")

print(fulfillment)


plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Chart 1: Revenue vs Performance
booking_types = ['Spot', 'Contract', 'Dedicated']
revenue = [132.6, 131.9, 260.5]
ontime_rate = [55.8, 55.5, 55.7]

color_blue = '#1f77b4'
color_red = '#d62728'

# Revenue
ax1_twin = ax1.twinx()
bars = ax1.bar(booking_types, revenue, color=color_blue, alpha=0.7, width=0.4, label='Total Revenue ($M)')
ax1.set_yticklabels([])
ax1.grid(False)
ax1.set_ylabel('Total Revenue (Million $)', color=color_blue, fontsize=12)
ax1.tick_params(axis='y', labelcolor=color_blue)
ax1.set_ylim(0, 300)

# On-Time Rate
line = ax1_twin.plot(booking_types, ontime_rate, color=color_red, marker='o', linewidth=3, markersize=8, label='On-Time Rate (%)')
ax1_twin.set_yticklabels([])
ax1_twin.grid(False)
ax1_twin.set_ylabel('On-Time Fulfillment Rate (%)', color=color_red, fontsize=12)
ax1_twin.tick_params(axis='y', labelcolor=color_red)
ax1_twin.set_ylim(0, 100)

ax1.bar_label(bars, padding=5, fmt='$%.1fM', fontweight='bold', color=color_blue)

for i, val in enumerate(ontime_rate):
    ax1_twin.text(i, val + 3, f'{val}%', ha='center', fontweight='bold', color=color_red)

ax1.set_title('Revenue Share vs. Fulfillment Performance\nper Booking Type', fontsize=14, fontweight='bold')

#Synthetic Hours of Day Shift
hourly_data = (delivery_data.groupby(['hours_of_day', 'booking_type'])['on_time_flag'].mean().unstack() * 100).round(1)

fig, ax = plt.subplots(figsize=(12,6))
plt.style.use('seaborn-v0_8-whitegrid')

#Plot
ax.plot(hourly_data['Dedicated'], color='#00a2e8', label='Dedicated', linewidth=2.5, marker='o')
ax.plot(hourly_data['Contract'], color='#ed1c24', label='Contract', linewidth=2.5, marker='o')
ax.plot(hourly_data['Spot'], color='#fff200', label='Spot', linewidth=2.5, marker='o')
ax.axhline(y=50, color='#c3c3c3', linestyle='--', linewidth=2)
ax.text(0.0, 50.5, '50%', color='#a3a3a3', fontweight='bold', fontsize=10, va='bottom', ha='right')

ax.set_ylim(0, 100)
ax.set_yticks([])
ax.grid(False)

ax.set_xticks(list(range(24)))
ax.set_xticklabels([
    '12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM',
    '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
    '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM',
    '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM'
], fontsize=9, rotation=45)

ax.set_title('On-Time Performance per Hour by Booking Type', fontsize=12, fontweight='bold')
ax.set_xlabel("Scheduled Hour of Day", color="#555555", fontsize=11, labelpad=10)
ax.legend(loc='upper right')

plt.tight_layout()
plt.show()
