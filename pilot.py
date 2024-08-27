import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Function to check if the given date is a working day based on selected days
def is_working_day(date, working_days):
    return date.weekday() in working_days

# Function to find the next working day starting from current_datetime
def next_working_day(current_datetime, working_days):
    next_day = current_datetime + timedelta(days=1)
    while not is_working_day(next_day, working_days):
        next_day += timedelta(days=1)
    return next_day

# Function to calculate effective shift time and break time in a shift
def calculate_shift_time_with_breaks(shift_length=timedelta(minutes=600), break_duration=10, lunch_duration=30):
    work_period = timedelta(minutes=240)
    num_breaks_per_shift = shift_length // work_period
    total_break_time_per_shift = num_breaks_per_shift * timedelta(minutes=break_duration)
    effective_shift_time = shift_length - timedelta(minutes=lunch_duration)
    return effective_shift_time, total_break_time_per_shift.total_seconds() / 60  # Convert break time to minutes

# Function to create the shift schedule for a single shift starting at 6:00 AM
def create_single_shift_schedule_with_breaks(data, start_datetime, variety_shift_lengths, working_days, break_duration=10, lunch_duration=30):
    schedule = []
    current_datetime = start_datetime

    # Convert variety_shift_lengths DataFrame to a dictionary for faster lookups
    shift_length_dict = variety_shift_lengths.set_index('variety')['length'].to_dict()

    while not data.empty:
        for i, row in data.iterrows():
            variety = row['variety']
            remaining_minutes = row['productive_minutes']

            # Get the shift length for this variety
            shift_length = shift_length_dict.get(variety, timedelta(minutes=600))  # Default to 600 minutes if not found

            while remaining_minutes > 0:
                effective_shift_time, total_break_time_per_shift = calculate_shift_time_with_breaks(
                    shift_length=shift_length, break_duration=break_duration, lunch_duration=lunch_duration)

                # Skip non-working days
                if not is_working_day(current_datetime, working_days):
                    current_datetime = next_working_day(current_datetime, working_days)

                # Set the shift start time to 6:00 AM
                shift_start_time = current_datetime.replace(hour=6, minute=0)
                shift_end_time = shift_start_time + shift_length
                actual_shift_time = min(remaining_minutes, effective_shift_time.total_seconds() / 60)
                remaining_minutes -= actual_shift_time

                schedule.append({
                    'Variety': variety,
                    'ShiftStart': shift_start_time,
                    'ShiftEnd': shift_end_time,
                    'ShiftTime': shift_length.total_seconds() / 60,  # Convert to minutes
                    'EffectiveShiftTime': actual_shift_time,
                    'RemainingMinutes': remaining_minutes,
                    'BreakTime': total_break_time_per_shift,
                    'LunchBreak': lunch_duration
                })

                # Move to the next working day for the next shift
                current_datetime = next_working_day(shift_end_time, working_days)

            # Deduct the leftover from the next variety's remaining minutes
            if remaining_minutes < (effective_shift_time.total_seconds() / 60):  # Convert effective_shift_time to minutes
                leftover = (effective_shift_time.total_seconds() / 60) - remaining_minutes
                remaining_minutes = 0  # Set current variety's remaining minutes to 0

                # Deduct leftover from the next variety's remaining minutes
                if i + 1 < len(data):
                    next_variety_minutes = data.at[i + 1, 'productive_minutes']
                    if next_variety_minutes >= leftover:
                        data.at[i + 1, 'productive_minutes'] -= leftover
                    else:
                        # If leftover exceeds next variety's minutes, set next variety's minutes to 0
                        data.at[i + 1, 'productive_minutes'] = 0
                        leftover -= next_variety_minutes

            # If remaining minutes for this variety are zero, remove it from the DataFrame
            if remaining_minutes <= 0:
                data = data.drop(i).reset_index(drop=True)
                break  # Move to the next variety in the next iteration

    return pd.DataFrame(schedule)

# Streamlit app interface
st.title("Shift Scheduler")

# Get user inputs
start_date = st.date_input("Enter the start date:", datetime(2024, 9, 1))
start_datetime = datetime.combine(start_date, datetime.min.time()).replace(hour=6, minute=0)

# Select working days
working_days_selection = st.multiselect(
    "Select working days:",
    options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
)

# Map working days to weekday numbers
working_days_map = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6
}
working_days = [working_days_map[day] for day in working_days_selection]

picking_order = st.text_input("Enter the picking order, separated by commas:", "Cascade, Simcoe, Citra, Mosaic, HBC 682, HBC 586")
picking_order = [x.strip() for x in picking_order.split(',')]

shift_lengths = st.text_input("Enter the shift lengths for each variety, separated by commas:", "480, 480, 480, 480, 480, 480")
shift_lengths = [int(x.strip()) for x in shift_lengths.split(',')]

# Create a DataFrame with variety and corresponding shift lengths
variety_shift_lengths_df = pd.DataFrame({
    'variety': picking_order,
    'length': [timedelta(minutes=minutes) for minutes in shift_lengths]
})

# Example pilot DataFrame with sample data
pilot = pd.DataFrame({
    'variety': ['Cascade', 'Simcoe', 'Citra', 'Mosaic', 'HBC 682', 'HBC 586'],
    'productive_minutes': [555.317077, 2844.198612, 2052.972642, 448.106181, 506.610797, 2286.922384]  # Example data
})

# Sort the DataFrame based on the picking order
pilot['order'] = pilot['variety'].apply(lambda x: picking_order.index(x))
pilot_sorted = pilot.sort_values(by='order', ascending=True)

# Create the shift schedule
shift_schedule = create_single_shift_schedule_with_breaks(
    data=pilot_sorted,
    start_datetime=start_datetime,
    variety_shift_lengths=variety_shift_lengths_df,  # Pass the DataFrame with the shift lengths
    working_days=working_days  # Pass the selected working days
)

# Display the shift schedule in the Streamlit app
st.write("Shift Schedule")
st.dataframe(shift_schedule)

# Export the schedule to Excel if the button is clicked
if st.button("Export to Excel"):
    shift_schedule.to_excel('shift_schedule.xlsx', index=False)
    st.success("Schedule exported to shift_schedule.xlsx")


