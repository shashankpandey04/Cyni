"""

This is a snippet from utils/Schema.py:
It is used to define the schema for the MongoDB database.

"""

import discord

server_settings = {
    "_id": 0,
    "basic_settings" : {
        "staff_roles": [],
        "management_roles": [],
        "message_quota": None
    },
    "moderation_module" : {
        "enabled" : False,
    },
    "anti_ping_module" : {
        "enabled" : False,
        "affected_roles" : [],
        "exempt_roles" : []
    },
    "loa_module": {
        "enabled": False,
        "loa_roles": [],
        "loa_channel": 0
    },
    "staff_management": {
        "enabled" : False,
        "promotion_channel" : 0,
        "demotion_channel" : 0,
    },
    "customization": {
        "prefix": "?"
    },
    "logging_channels": {
        "audit_log": 0,
        "mod_log_channel": 0,
        "application_channel": 0,
        "ban_appeal_channel": 0
    }
}

warning = {
    "_id": 0,
    "warnings": []
}