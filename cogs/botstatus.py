import discord
from discord.ext import commands, tasks
import asyncio

class BotStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_index = 0
        self.statuses = [
            "🎮 ᴏᴘᴘʀᴏ-ɴᴇᴛᴡᴏʀᴋ.ᴅᴇ™",
            "💬 Chat, Gaming & Fun",
            "🚀 discord.gg/xwYgKQnpAM",
            "⭐ Partner Programs",
            "🎲 Events & Challenges",
            "🚀 Powered by ManagerX"
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Status System loaded for {self.bot.user}")
        await asyncio.sleep(3)
        
        if not self.change_status.is_running():
            self.change_status.start()
            print("✅ Status Rotation started")

    def cog_unload(self):
        try:
            if self.change_status.is_running():
                self.change_status.cancel()
            print("❌ Status System unloaded")
        except Exception as e:
            print(f"Fehler beim Unload: {e}")

    @tasks.loop(minutes=5)
    async def change_status(self):
        """Ändert den Bot Status alle 5 Minuten"""
        try:
            # Hole aktuellen Status
            status_text = self.statuses[self.status_index]
            
            # Setze Custom Status
            await self.bot.change_presence(
                activity=discord.CustomActivity(name=status_text),
                status=discord.Status.online
            )
            
            print(f"✅ Status geändert: {status_text}")
            
            # Nächster Status
            self.status_index = (self.status_index + 1) % len(self.statuses)
            
        except Exception as e:
            print(f"❌ Fehler beim Status ändern: {e}")

    @change_status.before_loop
    async def before_change_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(BotStatus(bot))