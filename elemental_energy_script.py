import pandas as pd


def parse_date(df, column):
	"""The function takes in a dataframe and a string "column" which is the name of the datetime column,
	it outputs the datframe with 3 new columns, month, year, hour which are columns with the corresponding
	date levels extracted from the datetime column"""
	df[column] = pd.to_datetime(df[column])
	df['month'] = pd.DatetimeIndex(df[column]).month
	df['year'] = pd.DatetimeIndex(df[column]).year
	df['hour'] = pd.DatetimeIndex(df[column]).hour
	return df


def remove_outliers(ser):
	"""
	Takes in a series, and replaces the every value above the 95 percentile with the median,
	if I had more time I would've done this by meter_id
	"""
	outlier_thresh = ser.quantile(0.95)
	median = ser.quantile(0.5)
	ser = ser.apply(lambda x: median if x >= outlier_thresh else x)
	return ser


def clean_df(filtered_df):
	"""
	Takes in a dataframe, removes missing values, turns negative values
	positive foe the meter reading, removes outliers and drops duplicates
	"""
	clean_df =filtered_df.dropna()
	clean_df["consumption_kwh"] = clean_df["consumption_kwh"].apply(lambda x: x * -1 if x < 0 else x)
	clean_df["consumption_kwh"] = remove_outliers(clean_df["consumption_kwh"])
	clean_df.drop_duplicates()
	return clean_df


def get_smart_data(file_name, filter_data, **kwargs):
	"""
	reads a file into dataframe, if filter_data is True, filters data based on keyword arguments corresponding to columns,
	then cleans data and returns
	"""
	df = pd.read_csv(file_name)
	time_df = parse_date(df,'DateTime')
	if filter_data:
		for key,value in kwargs.items():
			time_df = time_df[time_df[key] == value]
	cleaned_df = clean_df(time_df)
	return cleaned_df


def calculate_rate(*x):
	"""
	multiplies 2 numbers together and returns the result
	"""
	return x[0] *x[1]


def calculate_cost(df, fixed_rate, other_rate_name, other_rate,cut_off):
	"""
	calculates the fixed rate from the energy consumption, calculates an alternate pricing rate, tarriff determined by cutoff hour
	"""
	df["Electricity cost (£) on current flat rate tariff"] = df["consumption_kwh"] * fixed_rate
	df.loc[df['hour'] < cut_off, 'tariff_type'] = other_rate['Low']
	df.loc[df['hour'] >= cut_off, 'tariff_type'] = other_rate['High']
	df[other_rate_name] = df[['tariff_type',"consumption_kwh"]].apply(lambda x : calculate_rate(*x), axis=1)
	df["Potential cost savings (£) if household was on an {} tariff".format(other_rate_name)] = df["Electricity cost (£) on current flat rate tariff"]- df[other_rate_name]
	return df


def group_data(df, columns):
	"""
	Group a dataframe by columns and sum them together
	"""
	grouped_df = df.groupby(columns, as_index=False).sum()
	return grouped_df


if __name__=='__main__':
	df = get_smart_data("ee_coding_challenge_dataset.csv",False, month=12, year=2013, meter_id="MAC000069")
	cost_df = calculate_cost(df, 0.15, "Economy 7", {"Low": 0.12, "High": 0.16}, 7)

	columns = ["month", "year", "meter_id"]
	selected_cols = ["month", "year", "meter_id", "Electricity cost (£) on current flat rate tariff", "Potential cost savings (£) if household was on an Economy 7 tariff"]
	grouped_df = group_data(cost_df, columns)[selected_cols]
	print(grouped_df)