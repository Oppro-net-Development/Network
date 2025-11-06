import discord
from discord import slash_command, Option, SeparatorSpacingSize
from discord.ui import Container, View
from discord.ext import commands
import ezcord

class Status(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Setzt den Bot-Status (Ausfall, Störung, Wartung, Online).")
    @discord.default_permissions(administrator=True)
    async def status(
        self,
        ctx,
        message: str,
        bot: discord.Member,
        status: Option(str, "Wähle den Status", choices=["Ausfall", "Störung", "Wartungsarbeiten", "Online"])
    ):
        channel = self.bot.get_channel(1429030623367921715)

        banner_url = "https://cdn.discordapp.com/attachments/1420436338284695657/1429104060879077467/server-status.png?ex=68f4ec5f&is=68f39adf&hm=118309b93d12c227d7c8ae69e573ed739f96dcfc2f6dfc42f980e25b59a10c2e&"
        banner = discord.ui.MediaGallery()
        banner.add_item(banner_url)

        # 🔴 Ausfall
        ausfall_container = Container()
        ausfall_container.add_item(banner)
        ausfall_container.add_text(f"## 🔴 Failure for {bot}")
        ausfall_container.add_separator(spacing=SeparatorSpacingSize.small)
        ausfall_container.add_text(f"**Reason:**\n{message}\n-# Powered by ManagerX")
        view_ausfall = View()
        view_ausfall.add_item(ausfall_container)

        # 🟠 Störung
        stoerung_container = Container()
        stoerung_container.add_item(banner)
        stoerung_container.add_text(f"## 🟠 Issue for {bot}")
        stoerung_container.add_separator(spacing=SeparatorSpacingSize.small)
        stoerung_container.add_text(f"**Details:**\n{message}\n-# Powered by ManagerX")
        view_stoerung = View()
        view_stoerung.add_item(stoerung_container)

        # 🟡 Wartungsarbeiten
        wartung_container = Container()
        wartung_container.add_item(banner)
        wartung_container.add_text(f"## 🔵 Maintenance for {bot}")
        wartung_container.add_separator(spacing=SeparatorSpacingSize.small)
        wartung_container.add_text(f"**Info:**\n{message}\n-# Powered by ManagerX")
        view_wartung = View()
        view_wartung.add_item(wartung_container)

        # 🟢 Online
        online_container = Container()
        online_container.add_item(banner)
        online_container.add_text(f"## 🟢 Online: {bot}")
        online_container.add_separator(spacing=SeparatorSpacingSize.small)
        online_container.add_text(f"{message}\n-# Powered by ManagerX")
        view_online = View()
        view_online.add_item(online_container)

        # View je nach Status auswählen
        views = {
            "Ausfall": view_ausfall,
            "Störung": view_stoerung,
            "Wartungsarbeiten": view_wartung,
            "Online": view_online
        }

        selected_view = views[status]

        # ✅ Jetzt funktioniert es
        await channel.send(view=selected_view)
        await ctx.respond(f"✅ Status für **{bot}** auf **{status}** gesetzt!", ephemeral=True)

def setup(bot):
    bot.add_cog(Status(bot))
