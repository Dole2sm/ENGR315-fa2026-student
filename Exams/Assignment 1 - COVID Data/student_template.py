import sys

"""
Create a program which will provide answers to the questions posed in the assignment description.
We've provided a function which will parse the NYT covid database file (named "us-counties.csv"); 
however, its correct implementation will be up to you. DO NOT MODIFY THIS FUNCTION.
Your code needs to be successful as well as sufficiently commented/documented to receive full credit.
"""


def parse_nyt_data(file_path=''):
    """
    Parse the NYT covid database and return a list of tuples. Each tuple describes one entry in the source data set.
    Date: the day on which the record was taken in YYYY-MM-DD format
    County: the county name within the State
    State: the US state for the entry
    Cases: the cumulative number of COVID-19 cases reported in that locality
    Deaths: the cumulative number of COVID-19 death in the locality

    :param file_path: Path to data file
    :return: A List of tuples containing (date,county, state, fips, cases, deaths) information

    ____________________ DO NOT MODIFY THIS FUNCTION ___________________
    """
    # data point list
    data=[]

    # open the NYT file path
    try:
        fin = open(file_path)
    except FileNotFoundError:
        print('File ', file_path, ' not found. Exiting!')
        sys.exit(-1)

    # get rid of the headers
    fin.readline()

    # while not done parsing file
    done = False

    # loop and read file
    while not done:
        line = fin.readline()

        if line == '':
            done = True
            continue

        # format is date,county,state,fips,cases,deaths
        (date,county, state, fips, cases, deaths) = line.rstrip().split(",")

        # clean up the data to remove empty entries
        if cases=='':
            cases=0
        if deaths=='':
            deaths=0

        # convert elements into ints
        try:
            entry = (date,county,state, fips, int(cases), int(deaths))
        except ValueError:
            print('Invalid parse of ', entry)

        # place entries as tuple into list
        data.append(entry)


    return data
### YOUR CODE HERE ###

# I am going to use the NYT COVID data file that was given to us.
# This file has one row for each county each day.
# Each row looks like:
# (date, county, state, fips, cases, deaths)

# first I read in the data from the CSV
records = parse_nyt_data("data/covid/us-counties.csv")

# I only care about Harrisonburg city, VA and Rockingham county, VA. 
# I am going to make two lists that only include those rows.
harrisonburg_rows = []
rockingham_rows = []

for row in records:
    date, county, state, fips, cases, deaths = row

    if county == "Harrisonburg city" and state == "Virginia":
        harrisonburg_rows.append(row)

    if county == "Rockingham" and state == "Virginia":
        rockingham_rows.append(row)

# Question 1:
# Find the first date when each place had a positive number of cases.

# This function will find the first date with cases > 0
def first_positive_date(rows):
    for date, county, state, fips, cases, deaths in rows:
        if cases > 0:
            return date
    return "No positive cases found"


h_first = first_positive_date(harrisonburg_rows)
r_first = first_positive_date(rockingham_rows)

print("Q1: Harrisonburg first positive date:", h_first)
print("Q1: Rockingham first positive date:", r_first)

# Question 2:
# Find the date with the biggest jump in new cases for each place.

# This function calculates the new cases each day by subtracting the
# previous day's total from the current day's total.
def daily_new_cases(rows):
    daily = []
    previous_total = 0

    for date, county, state, fips, cases, deaths in rows:
        new_cases = cases - previous_total
        daily.append((date, new_cases))
        previous_total = cases

    return daily


# Now I apply that to both counties.
h_daily = daily_new_cases(harrisonburg_rows)
r_daily = daily_new_cases(rockingham_rows)

# Find the largest daily increase.
def max_daily_increase(daily_list):
    biggest_date = daily_list[0][0]
    biggest_value = daily_list[0][1]

    for date, new_cases in daily_list:
        if new_cases > biggest_value:
            biggest_value = new_cases
            biggest_date = date

    return biggest_date, biggest_value


h_big_date, h_big_cases = max_daily_increase(h_daily)
r_big_date, r_big_cases = max_daily_increase(r_daily)

print("q2: Harrisonburg biggest daily increase:", h_big_date, h_big_cases)
print("q2: Rockingham biggest daily increase:", r_big_date, r_big_cases)

# Question 3:
# Find the 7-day period with the biggest total number of new cases.

# This function looks at all 7-day windows and finds the one with the highest total.
def worst_7_day_period(daily_list):
    best_total = -1
    best_start = None
    best_end = None

    # We need to look at every possible 7-day block.
    for i in range(len(daily_list) - 6):
        total = 0

        for j in range(i, i + 7):
            total += daily_list[j][1]

        if total > best_total:
            best_total = total
            best_start = daily_list[i][0]
            best_end = daily_list[i + 6][0]

    return best_start, best_end, best_total


h_start, h_end, h_total = worst_7_day_period(h_daily)
r_start, r_end, r_total = worst_7_day_period(r_daily)

print("Q3: Harrisonburg worst 7-day period:", h_start, h_end, h_total)
print("Q3: Rockingham worst 7-day period:", r_start, r_end, r_total)

