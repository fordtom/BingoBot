"""Discord-related utility functions used across the bot."""
import discord
import logging
import re

logger = logging.getLogger(__name__)

async def resolve_mentions(interaction: discord.Interaction, text: str) -> str:
    """Convert Discord mentions in the provided text to usernames."""
    mention_pattern = r'<@!?(\d+)>'
    mentions = re.finditer(mention_pattern, text)
    replacements = {}

    for match in mentions:
        user_id = match.group(1)
        guild = interaction.guild
        if guild:
            try:
                mentioned_member = guild.get_member(int(user_id))
                if not mentioned_member:
                    try:
                        mentioned_member = await guild.fetch_member(int(user_id))
                    except (discord.NotFound, discord.HTTPException) as e:
                        logger.warning(f"Could not fetch member {user_id}: {e}")
                        continue
                if mentioned_member:
                    logger.debug(
                        f"Resolving mention {match.group(0)} to {mentioned_member.name}"
                    )
                    replacements[match.group(0)] = mentioned_member.name
            except (ValueError, Exception) as e:
                logger.warning(f"Error resolving mention {user_id}: {e}")

    for mention, username in replacements.items():
        text = text.replace(mention, username)

    return text

async def restore_mentions(interaction: discord.Interaction, response: str) -> str:
    """Convert usernames in the response back to Discord mentions."""
    guild = interaction.guild
    if not guild:
        return response

    try:
        members = guild.members
        if len(members) < 10:
            members = [member async for member in guild.fetch_members(limit=None)]
    except Exception as e:
        logger.warning(f"Could not fetch guild members: {e}")
        return response

    username_to_member = {member.name.lower(): member for member in members}
    for member in members:
        if member.display_name != member.name:
            username_to_member[member.display_name.lower()] = member

    modified_response = response

    at_pattern = r'@([a-zA-Z0-9_]+)'

    def replace_at_mention(match):
        username = match.group(1).lower()
        if username in username_to_member:
            member = username_to_member[username]
            logger.debug(f"Converting @{username} to mention")
            return member.mention
        return match.group(0)

    modified_response = re.sub(at_pattern, replace_at_mention, modified_response)

    sorted_usernames = sorted(username_to_member.keys(), key=len, reverse=True)

    for username in sorted_usernames:
        member = username_to_member[username]
        pattern = r'\b' + re.escape(username) + r'\b'

        def replace_username(match):
            logger.debug(
                f"Converting standalone username '{match.group(0)}' to mention"
            )
            return member.mention

        modified_response = re.sub(
            pattern, replace_username, modified_response, flags=re.IGNORECASE
        )

    return modified_response


def parse_player_ids(players_str: str) -> list[int]:
    """Parse a string of player mentions and return a list of user IDs."""
    player_ids = []
    # Regular expression to find user mentions
    mention_pattern = r'<@!?(\d+)>'
    
    # Find all matches in the input string
    matches = re.findall(mention_pattern, players_str)
    
    for user_id_str in matches:
        try:
            player_ids.append(int(user_id_str))
        except ValueError:
            # This should not happen with the regex, but as a safeguard
            logger.warning(f"Could not parse user ID: {user_id_str}")
            
    return player_ids


def format_username(user: discord.abc.User) -> str:
    """Return a filesystem-safe version of the user's actual username."""
    base_name = getattr(user, "name", str(user))
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", base_name)
