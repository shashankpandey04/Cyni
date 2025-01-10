import requests
import time
from datetime import datetime

GET_ALL_SHIFTS = 'https://core.ermbot.xyz/api/v1/shifts'
SEARCH_SHIFTS = 'https://core.ermbot.xyz/api/v1/shifts/search'


def format_duration(seconds: int) -> str:
    """
    Convert seconds to a string in the format 'X hours Y minutes'.
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    second = int(seconds % 60)
    time_string = ""
    if hours > 0:
        time_string += f"{hours} hours "
    if minutes > 0:
        time_string += f"{minutes} minutes "
    if second > 0:
        time_string += f"{second} seconds"
    return time_string

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

def ongoing_shift_more_than4h(username: str, data: dict) -> bool:
    """
    Check if there are any ongoing shifts longer than 4 hours.
    :param username: The username of the user.
    :param data: The data containing the shifts.
    :return: True if there is any ongoing shift longer than 4 hours, False otherwise.
    """
    for shift in data['data']:
        if shift['username'] == username and shift['end_epoch'] == 0:
            duration = time.time() - shift['start_epoch']
            if duration > 14400:
                return True

    return False

def total_shift_time(username: str, data: dict) -> str:
    """
    Calculate the total shift time for a given user.
    :param username: The username of the user.
    :param data: The data containing the shifts.
    :return: The total shift time in the format 'X hours Y minutes'.
    """
    total_duration = 0

    for shift in data['data']:
        if shift['username'] == username and shift['end_epoch'] != 0:
            total_duration += shift['end_epoch'] - shift['start_epoch']

    return format_duration(total_duration)

def get_roblox_thumbnail(user_id: str) -> str:
    """
    Get the Roblox thumbnail URL for a user.
    """
    try:
        response = requests.get(f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=true')
        response.raise_for_status()

        data = response.json()
        
        if 'data' in data and len(data['data']) > 0:
            image_url = data['data'][0]['imageUrl']
            return image_url
        else:
            return 'https://tr.rbxcdn.com/180DAY-f37f4fe7dbc6d6a1511c556b1c962a95/420/420/Image/Webp/noFilter'

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
    except (IndexError, KeyError) as e:
        return "An unexpected error occurred while processing the response."


def format_shift_data(user_shifts):
    """
    Format the user shifts data into the desired example format.
    Each entry contains total_duration, total_moderations, and shift_type.
    """
    formatted_data = []

    for shift in user_shifts['data']:
        if shift['end_epoch'] != 0:
            duration_seconds = shift['end_epoch'] - shift['start_epoch']
            total_duration = format_duration(duration_seconds)
        else:
            total_duration = "Ongoing"

        total_moderations = len(shift['moderations'])

        formatted_data.append({
            'username': shift['username'],
            'user_id': shift['user_id'],
            'total_duration': total_duration,
            'total_moderations': total_moderations,
            'shift_type': shift['type_'],
            'thumbnail': get_roblox_thumbnail(shift['user_id']),
        })

    return formatted_data