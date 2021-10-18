import asyncio
import discord
import hashlib
import hmac
import os
from quart import Quart, request, abort

TWITCH_SECRET = os.getenv('TWITCH_SECRET')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = int(os.getenv('DISCORD_GUILD'))
ENV = os.getenv('ENV')

app = Quart(__name__)
client = discord.Client()


def find_discord_channel(user_login, guild):
    category = None
    for channel in guild.channels:
        if not isinstance(channel, discord.CategoryChannel):
            continue
        if channel.name.lower().find(user_login.lower()) != -1:
            category = channel

    if not category:
        return None

    for channel in category.channels:
        if not isinstance(channel, discord.TextChannel):
            continue
        if channel.name.find("annonces") != -1:
            return channel


def find_discord_role(user_login, guild):
    for role in guild.roles:
        if role.name.lower().find(user_login.lower()) != -1:
            return role


def find_discord_infos(user_login):
    guild = client.get_guild(DISCORD_GUILD)
    return find_discord_channel(user_login, guild), find_discord_role(user_login, guild)


async def write_discord_announcement(channel, role, user_name, user_login):
    if role is None:
        await channel.send(f"📢 Hello !\n{user_name} vient de lancer un live !\n➡️ Rejoins nous sur https://twitch.tv/{user_login}")
    else:
        await channel.send(f"📢 Hello ||<@&{role.id}>|| !\n{user_name} vient de lancer un live !\n➡️ Rejoins nous sur https://twitch.tv/{user_login}")


@app.before_serving
async def before_serving():
    loop = asyncio.get_event_loop()
    await client.login(DISCORD_TOKEN)
    loop.create_task(client.connect())


@app.route('/', methods=['GET', 'POST'])
async def twitch_callback():
    msg_id = request.headers.get('Twitch-Eventsub-Message-Id')
    if msg_id is None:
        return abort(400)

    if verify_signature(request.headers, await request.get_data()) is False:
        print(f"{msg_id} - Wrong signature")
        return abort(403)

    req_body = await request.get_json()
    if "challenge" in req_body:
        return req_body["challenge"]

    user_login = req_body['event']['broadcaster_user_login']
    user_name = req_body['event']['broadcaster_user_name']
    print(f"{msg_id} - {user_login}")
    channel, role = find_discord_infos(user_login)
    if channel == None:
        print(f"{msg_id} - Channel not found")
        return abort(500)
    await write_discord_announcement(channel, role, user_name, user_login)
    return ''


def verify_signature(headers, body):
    message_signature = headers.get('Twitch-Eventsub-Message-Signature')
    message_id = headers.get('Twitch-Eventsub-Message-Id')
    message_timestamp = headers.get('Twitch-Eventsub-Message-Timestamp')
    hmac_message = message_id + message_timestamp + body.decode("utf-8")
    signature = hmac.new(TWITCH_SECRET.encode(),
                         hmac_message.encode(), hashlib.sha256)
    expected_signature_header = 'sha256=' + signature.hexdigest()
    if message_signature != expected_signature_header:
        return False
    return True


client.start(DISCORD_TOKEN)

if ENV == "dev":
    app.run(port=5000, debug=True)
else:
    app.run(host='0.0.0.0', port=8000, debug=False)
