import discord
from utils.constants import BLANK_COLOR, RED_COLOR, YELLOW_COLOR

basic_config_embed = discord.Embed(
    title="Basic Configuration",
    description=(
        "> This is the basic configuration for your server. But what does it do?\n"
        "> The basic configuration allows you to set the following settings:\n"
        "> These settings are crucial for the bot to function properly.\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Staff Role",
    value="- The role that is considered as discord staff and can use Moderation commands and other staff commands.",
    inline=False
).add_field(
    name="Management Role",
    value="- The role that is considered as discord management and can use Management commands like Staff Infraction, Application Results, Ban Appeal Results, etc.",
    inline=False
).add_field(
    name="Prefix",
    value="- The prefix that the bot will use for commands.",
    inline=False
)

anti_ping_embed = discord.Embed(
    title="Anti-Ping Module",
    description=(
        "> **What's the Anti-Ping Module?**\n"
        "- The Anti-Ping Module is a feature that helps to prevent spam and abuse of the ping command.\n\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Anti-Ping Roles",
    value="- These roles mark important individuals in the server. If someone pings a user with one of these roles, the Anti-Ping system will be triggered.",
    inline=False
).add_field(
    name="Bypass Roles",
    value="- These roles allow users to bypass the Anti-Ping system. If a user has one of these roles, they can ping users with Anti-Ping roles without triggering the system.",
    inline=False
)

moderation_module_embed = discord.Embed(
    title="Moderation Module",
    description=(
        "> **What is the Moderation Module?**\n"
        "- The Moderation Module allows you to configure various moderation settings for your server.\n\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Moderation Log Channel",
    value="- The channel where moderation actions will be logged. This is important for keeping track of moderation activities.",
    inline=False
).add_field(
    name="Ban Appeal Channel",
    value="- The channel where users can submit ban appeals. This allows users to appeal their bans and have them reviewed by staff.",
    inline=False
).add_field(
    name="Audit Log Channel",
    value="- The channel where audit logs will be sent, including message edits, deletes, and other important actions.",
    inline=False
)

staff_infractions_embed = discord.Embed(
    title="Staff Infraction Module",
    description=(
        "> **What is the Staff Infraction Module?**\n"
        "- The Staff Infraction Module allows you to manage staff infractions and keep track of staff behavior.\n\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Promotion Log Channel",
    value="- The channel where staff promotions will be logged.",
    inline=False
).add_field(
    name="Demotion Log Channel",
    value="- The channel where staff demotions will be logged.",
    inline=False
).add_field(
    name="Warning Log Channel",
    value="- The channel where staff warnings will be logged, including strikes and other infractions.",
    inline=False
)

activity_commands_embed = discord.Embed(
    title="Activity Commands",
    description=(
        "> **What are Activity Commands?**\n"
        "- CYNI allows you to track yout staff's activity and performance with messages they sent.\n\n"
        "> **Activity Commands**\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Activity Leaderboard",
    value="- The command that shows the activity leaderboard of your staff members.",
    inline=False
).add_field(
    name="Activity Stats",
    value="- The command that shows the activity stats of a specific staff member.",
    inline=False
).add_field(
    name="Activity Reset",
    value="- The command that resets the activity stats of a specific staff member.",
    inline=False
)

giveaway_commands_embed = discord.Embed(
    title="Giveaway Commands",
    description=(
        "> **What are Giveaway Commands?**\n"
        "- CYNI allows you to create and manage giveaways in your server.\n\n"
        "> **Giveaway Commands**\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Giveaway Create",
    value="- The command that creates a giveaway in your server.",
    inline=False
).add_field(
    name="Giveaway List",
    value="- The command that lists all giveaways in your server.",
    inline=False
).add_field(
    name="Giveaway Roll",
    value="- The command that rolls a giveaway winner.",
    inline=False
)

infraction_commands_embed = discord.Embed(
    title="Infraction Commands",
    description=(
        "> **What are Infraction Commands?**\n"
        "- CYNI allows you to manage infractions in your server.\n\n"
        "> **Infraction Commands**\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Infraction Post",
    value="- The command that posts an infraction for a user with 3 different types: Warning, Promotion, and Demotion.",
    inline=False
).add_field(
    name="Infraction View",
    value="- The command that views the infractions of a user.",
    inline=False
).add_field(
    name="Infraction Delete",
    value="- The command that deletes an infraction for a user.",
    inline=False
).add_field(
    name="Infraction Clear",
    value="- The command that clears all infractions for a user.",
    inline=False
)

partnership_commands_embed = discord.Embed(
    title="Partnership Commands",
    description=(
        "> **What are Partnership Commands?**\n"
        "- CYNI allows you to manage partnerships in your server.\n\n"
        "> **Partnership Commands**\n"
    ),
    color=BLANK_COLOR
).add_field(
    name="Partnership All",
    value="- The command that shows all partnerships in your server.",
    inline=False
).add_field(
    name="Partnership Log",
    value="- The command that logs a partnership in your server.",
    inline=False
).add_field(
    name="Partnership Delete",
    value="- The command that deletes a partnership in your server.",
    inline=False
).add_field(
    name="Partnership View",
    value="- The command that views a specific partnership in your server.",
    inline=False
)