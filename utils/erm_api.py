import requests
import time

GET_ALL_SHIFTS = 'https://core.ermbot.xyz/api/v1/shifts'
SEARCH_SHIFTS = 'https://core.ermbot.xyz/api/v1/shifts/search'


def format_duration(seconds: int) -> str:
    """
    Convert seconds to a string in the format 'X hours Y minutes'.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} hours {minutes} minutes"

def get_user_shifts(username: str, guild_id: str, erm_token: str) -> dict:
    headers = {
        'Authorization': erm_token,
        'Guild': guild_id
    }
    querystrings = {
        'username': username
    }
    response = requests.request('GET', SEARCH_SHIFTS, headers=headers, params=querystrings)
    return response.json()

def longest_shift_duration(data):
    """
    Find the longest shift duration from completed shifts.
    """
    max_duration = 0
    longest_shift = None

    for shift in data['data']:
        if shift['end_epoch'] != 0:  # Completed shifts
            duration = shift['end_epoch'] - shift['start_epoch']
            if duration > max_duration:
                max_duration = duration
                longest_shift = shift

    return longest_shift, format_duration(max_duration)

def ongoing_shift_over_4_hours(data):
    ongoing_shifts = []

    for shift in data['data']:
        if shift['end_epoch'] == 0:
            duration = time.time() - shift['start_epoch']
            if duration > 14400:
                ongoing_shifts.append({
                    "username": shift['username'],
                    "nickname": shift['nickname'],
                    "user_id": shift['user_id'],
                    "duration": format_duration(duration)
                })

def total_shift_duration(data):
    """
    Calculate the total shift duration for all shifts and return it in string format.
    """
    total_duration = 0

    for shift in data['data']:
        if shift['end_epoch'] != 0:
            total_duration += shift['end_epoch'] - shift['start_epoch']

    return format_duration(total_duration)

def count_shifts(data: dict) -> int:
    """
    Count the total number of shifts.
    """
    return len(data['data'])

def get_all_shifts(erm_token: str, guild_id: str) -> dict:
    headers = {
        'Authorization': erm_token,
        'Guild': guild_id
    }
    response = requests.get(GET_ALL_SHIFTS, headers=headers)
    return response.json()

def ongoing_shifts_over_4_hours(data):
    """
    Find all users with ongoing shifts longer than 4 hours.
    """
    ongoing_users = []

    for shift in data['data']:
        if shift['end_epoch'] == 0:
            duration = time.time() - shift['start_epoch']
            if duration > 14400:
                ongoing_users.append({
                    "username": shift['username'],
                    "nickname": shift['nickname'],
                    "user_id": shift['user_id'],
                    "duration": format_duration(duration)
                })

    return ongoing_users

def ongoing_shifts_over_1_minute(data):
    """
    Find all users with ongoing shifts longer than 1 minute.
    """
    ongoing_users = []

    for shift in data['data']:
        if shift['end_epoch'] == 0:
            duration = time.time() - shift['start_epoch']
            if duration > 60:
                ongoing_users.append({
                    "username": shift['username'],
                    "nickname": shift['nickname'],
                    "user_id": shift['user_id'],
                    "duration": format_duration(duration)
                })

    return ongoing_users