import discord
from discord.ext import commands, tasks
from discord import slash_command, Option
import ezcord
import itertools
import os
import requests
channel_ID = 1270721758462214235
intents = discord.Intents.default()
bot = ezcord.Bot(debug_guilds=["1428835818792947884"], ready_event=ezcord.ReadyEvent.table_vertical, intents=intents)

@bot.event
async def on_ready():
    print(f"[STARTING UP] Logged in as {bot.user}")
   


if __name__ == "__main__":
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
bot.run(os.getenv("TOKEN"))