import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import matplotlib.dates as mdates
#import data
harvest_perrault = pd.read_csv('harvester_perrault.csv')
harvest_pilot = pd.read_csv('harvest_pilot.csv')
harvest_perrault['vpm'] = harvest_perrault['vpm'] * 3 #number of perrault harvesters running per shift
perrault = harvest_perrault.groupby('variety')['productive_minutes'].sum().reset_index()
# Define the order in which varieties need to be picked
picking_order = [
    'Simcoe', 'Citra', 'Sabro', 'Mosaic', 'HBC 1019', 'Palisade', 'HBC 522', 'Idaho 7', 'Talus', 'HBC 682',
    'HBC 638', 'HBC 586', 'Experimental'
]

# Sort the DataFrame based on the picking order
perrault['order'] = perrault['variety'].apply(lambda x: picking_order.index(x))
perrault = perrault.sort_values(by='order')#.drop(columns='order')

import xlwings as xw
import pandas as pd
from datetime import datetime, timedelta

data = perrault


def is_working_day(date):
    return date.weekday() < 5  # Monday to Friday are working days

def next_working_day(current_datetime):
    next_day = current_datetime + timedelta(days=1)
    while not is_working_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def calculate_shift_time_with_breaks(total_minutes, work_period=240, break_duration=10, lunch_duration=30, shift_length=600):
    num_breaks_per_shift = shift_length // work_period
    total_break_time_per_shift = num_breaks_per_shift * break_duration
    effective_shift_length = shift_length - total_break_time_per_shift
    return effective_shift_length, total_break_time_per_shift

def create_shift_schedule_with_breaks(data, start_datetime, variety_shift_lengths, break_duration=10, lunch_duration=30):
    schedule = []
    current_datetime = start_datetime

    for index, row in data.iterrows():
        variety = row['variety']
        shift_length = variety_shift_lengths.get(variety, 630)  # Default to 10.5 hours if not specified
        effective_shift_length, total_break_time_per_shift = calculate_shift_time_with_breaks(
            shift_length, shift_length=shift_length)

        if not is_working_day(current_datetime):
            current_datetime = datetime.combine(next_working_day(current_datetime), datetime.min.time()) + timedelta(hours=8)

        shift_end_time = current_datetime + timedelta(minutes=effective_shift_length + total_break_time_per_shift)

        schedule.append({
            'variety': variety,
            'ShiftStart': current_datetime,
            'ShiftEnd': shift_end_time,
            'ShiftTime': effective_shift_length,
            'BreakTime': total_break_time_per_shift,
            'LunchBreak': lunch_duration if effective_shift_length >= 300 else 0,
            'Date': current_datetime.strftime('%m-%d-%Y')
        })

        current_datetime = next_working_day(shift_end_time)
        current_datetime = datetime.combine(current_datetime, datetime.min.time()) + timedelta(hours=8)

    return pd.DataFrame(schedule)

@xw.func
def create_shift_schedule_excel(start_date, picking_order, varieties, shift_lengths):
    data = pd.DataFrame({
        'Picking Order': picking_order,
        'variety': varieties,
        'shift_length': shift_lengths
    })

    data = data.sort_values(by='Picking Order').reset_index(drop=True)
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M')

    # Generate the shift schedule
    variety_shift_lengths = dict(zip(data['variety'], data['shift_length']))
    schedule = create_shift_schedule_with_breaks(data, start_datetime, variety_shift_lengths)

    return schedule.values.tolist()

# Example usage (this is not part of the function, just to show how it would be used)
if __name__ == "__main__":
    # Assuming `data` is loaded or defined elsewhere
    start_datetime = datetime(2024, 9, 1, 6, 0)

    variety_shift_lengths = {
        'Simcoe': 600,  # 10 hours
        'Citra': 600,  # 10 hours
        'Sabro': 600,  # 10 hours
        'Mosaic': 600,  # 10 hours
        'HBC 1019': 450, # 7.5 hours
        'Palisade' : 450, # 7.5 hours
        'HBC 522' : 450, # 7.5 hours
        'Idaho 7' : 450, # 7.5 hours
        'Talus' : 450, # 7.5 hours
        'HBC 682' : 450, # 7.5 hours
        'HBC 638' : 450, # 7.5 hours
        'HBC 586' : 450, # 7.5 hours
        'Experimental' : 450 # 7.5 hours
    }

    # You would normally call this from Excel using xlwings, but here's an example:
    shift_schedule = create_shift_schedule_with_breaks(data, start_datetime, variety_shift_lengths)
    print(shift_schedule)
#%%
