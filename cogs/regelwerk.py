import discord
from discord.ext import commands, tasks
from discord.ui import Container
from discord import SeparatorSpacingSize
import ezcord
import random
import string
import datetime
from typing import Dict, List

# Config
BANNER_URL = "https://cdn.discordapp.com/attachments/1420436338284695657/1428764646650679316/server-rules.png?ex=68f3b044&is=68f25ec4&hm=c2cbb71a7dbef0982116668881cef37933785e8ac7cb9d8a540f15ae7b578fcc&"
EMOJI = "<:dot:1421834173127069778>"

class UserData:
    def __init__(self):
        self.verification_attempts: Dict[int, int] = {}
        self.last_verification_time: Dict[int, datetime.datetime] = {}
        self.blocked_users: List[int] = []
        self.cooldown_duration = 3600  # 1h
        self.max_attempts = 3

    def can_attempt_verification(self, user_id: int) -> tuple[bool, str]:
        if user_id in self.blocked_users:
            return False, "User is permanently blocked"
        attempts = self.verification_attempts.get(user_id, 0)
        if attempts >= self.max_attempts:
            last_time = self.last_verification_time.get(user_id)
            if last_time and (datetime.datetime.now() - last_time).total_seconds() < self.cooldown_duration:
                remaining = self.cooldown_duration - (datetime.datetime.now() - last_time).total_seconds()
                return False, f"Cooldown active. Try again in {int(remaining // 60)} minutes"
            else:
                self.verification_attempts[user_id] = 0
                return True, ""
        return True, ""

    def add_verification_attempt(self, user_id: int) -> int:
        self.verification_attempts[user_id] = self.verification_attempts.get(user_id, 0) + 1
        self.last_verification_time[user_id] = datetime.datetime.now()
        return self.verification_attempts[user_id]

    def reset_user(self, user_id: int):
        self.verification_attempts.pop(user_id, None)
        self.last_verification_time.pop(user_id, None)
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)

class RulesSystem(ezcord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules_channel_id = 1420436338284695654
        self.rules_message_id = 1428813209338511361
        self.log_channel_id = None
        self.member_role_name = "👤┇Member"
        self.user_data = UserData()
        self.stats = {
            "total_verifications": 0,
            "failed_attempts": 0,
            "blocked_users": 0,
            "system_start_time": datetime.datetime.now()
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"🔧 Rules System loaded for {self.bot.user}")
        await self.setup_rules_message()
        self.cleanup_old_data.start()
        print("✅ Rules System fully initialized")

    def cog_unload(self):
        self.cleanup_old_data.cancel()

    def calculate_success_rate(self) -> float:
        total = self.stats['total_verifications'] + self.stats['failed_attempts']
        return 100.0 if total == 0 else round((self.stats['total_verifications'] / total) * 100, 1)

    def create_unified_rules_container(self) -> discord.ui.View:
        container = Container()
        banner = discord.ui.MediaGallery()
        banner.add_item(BANNER_URL)
        container.add_item(banner)

        # Alle Regeln
        container.add_text("## SERVER RULES & GUIDELINES")
        container.add_separator(spacing=SeparatorSpacingSize.small)
        container.add_text(
            "Welcome to **OPPRO.NET Network**! Please read and accept our community guidelines.\n"
            "**By joining this server, you agree to follow these rules and our digital house rights.**\n\n"
        )
        # Community Standards
        container.add_text(
            f"## 🤝 **Community Standards**\n"
            f"{EMOJI} Be respectful and kind to all members\n"
            f"{EMOJI} No harassment, hate speech, or discrimination\n"
            f"{EMOJI} Keep conversations appropriate and family-friendly\n"
            f"{EMOJI} No spam, excessive caps, or disruptive behavior\n"
            f"{EMOJI} Political discussions are strictly prohibited\n\n"
        )
        container.add_separator(spacing=SeparatorSpacingSize.small)
        # Prohibited Content
        container.add_text(
            f"## 🚫 **Prohibited Content**\n"
            f"{EMOJI} NSFW, illegal, or harmful content\n"
            f"{EMOJI} Personal information or doxxing\n"
            f"{EMOJI} Advertising without permission\n"
            f"{EMOJI} Malware, viruses, or malicious links\n\n"
        )
        container.add_separator(spacing=SeparatorSpacingSize.small)
        # Enforcement
        container.add_text(
            f"## ⚖️ **Enforcement**\n"
            f"{EMOJI} **1st Violation:** Warning\n"
            f"{EMOJI} **2nd Violation:** Temporary timeout\n"
            f"{EMOJI} **3rd Violation:** Permanent ban\n\n"
        )
        container.add_separator(spacing=SeparatorSpacingSize.small)
        # Digital House Rights
        container.add_text(
            f"## 🏠 **Digital House Rights**\n"
            f"{EMOJI} **OPPRO.NET Network** reserves full moderation rights\n"
            f"{EMOJI} Staff decisions are final and binding\n"
            f"{EMOJI} We maintain the right to remove disruptive users\n"
            f"{EMOJI} Server access is a privilege, not a right\n\n"
        )
        # Support & Appeals
        container.add_text(
            f"## 📞 **Support & Appeals**\n"
            f"{EMOJI} Contact staff for questions or rule clarifications\n"
            f"{EMOJI} Report violations through proper channels\n"
            f"{EMOJI} Appeals must be submitted respectfully\n\n"
        )
        # Footer
        container.add_text(
            "───────────────────────────────────\n"
            f"**© 2024 OPPRO.NET Network** • *Rules may be updated without notice*\n"
            f"**Total Verifications:** `{self.stats['total_verifications']}` • **Success Rate:** `{self.calculate_success_rate()}%`"
        )

        view = discord.ui.View(timeout=None)
        view.add_item(container)
        return view

    def combine_views(self, *views: discord.ui.View) -> discord.ui.View:
        combined = discord.ui.View(timeout=None)
        for view in views:
            for item in view.children:
                combined.add_item(item)
        return combined

    async def update_or_create_message(self, channel, container, view):
        final_view = self.combine_views(container, view)
        if self.rules_message_id:
            try:
                msg = await channel.fetch_message(self.rules_message_id)
                await msg.edit(view=final_view)
                print("✅ Rules message updated")
                return
            except discord.NotFound:
                print("⚠️ Message not found, creating new one")
            except Exception as e:
                print(f"❌ Editing message failed: {e}")
        try:
            new_msg = await channel.send(view=final_view)
            self.rules_message_id = new_msg.id
            print(f"✅ New rules message created: {new_msg.id}")
        except Exception as e:
            print(f"❌ Sending message failed: {e}")

    async def setup_rules_message(self):
        channel = self.bot.get_channel(self.rules_channel_id)
        if not channel:
            print(f"❌ Channel {self.rules_channel_id} not found")
            return
        container = self.create_unified_rules_container()
        view = RulesView(self)
        await self.update_or_create_message(channel, container, view)

    @tasks.loop(hours=2)
    async def cleanup_old_data(self):
        now = datetime.datetime.now()
        expired = [uid for uid, t in self.user_data.last_verification_time.items()
                   if (now - t).total_seconds() > self.user_data.cooldown_duration]
        for uid in expired:
            self.user_data.verification_attempts.pop(uid, None)
            self.user_data.last_verification_time.pop(uid, None)
        if expired:
            print(f"🧹 Cleaned up {len(expired)} users")

# ----- Views -----
class RulesView(discord.ui.View):
    def __init__(self, cog: RulesSystem):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="I Accept All Rules", style=discord.ButtonStyle.success, custom_id="rules_accept_all", emoji="✅")
    async def accept_rules(self, button, interaction):
        member_role = discord.utils.get(interaction.guild.roles, name=self.cog.member_role_name)
        if member_role in interaction.user.roles:
            await interaction.response.send_message("✅ Already verified!", ephemeral=True)
            return
        can_attempt, reason = self.cog.user_data.can_attempt_verification(interaction.user.id)
        if not can_attempt:
            await interaction.response.send_message(f"⛔ {reason}", ephemeral=True)
            return
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        await interaction.response.send_message(
            f"Your verification code: `{code}`",
            ephemeral=True
        )
        view = VerificationView(self.cog, code, interaction.user.id)
        await interaction.followup.send("Click below to enter the code:", view=view, ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self, cog: RulesSystem, code: str, user_id: int):
        super().__init__(timeout=600)
        self.cog = cog
        self.code = code
        self.user_id = user_id

    @discord.ui.button(label="Enter Code", style=discord.ButtonStyle.primary, emoji="🔐")
    async def enter_code(self, button, interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Not your verification!", ephemeral=True)
            return
        modal = VerificationModal(self.cog, self.code, self.user_id)
        await interaction.response.send_modal(modal)

class VerificationModal(discord.ui.Modal):
    def __init__(self, cog: RulesSystem, code: str, user_id: int):
        super().__init__(title="🔐 Enter Verification Code")
        self.cog = cog
        self.code = code
        self.user_id = user_id
        self.code_input = discord.ui.InputText(label="Code", placeholder="Enter the code", required=True, max_length=20)
        self.add_item(self.code_input)

    async def callback(self, interaction):
        if self.code_input.value.lower().strip() == self.code.lower():
            role = discord.utils.get(interaction.guild.roles, name=self.cog.member_role_name)
            if role:
                await interaction.user.add_roles(role, reason="Verified")
                self.cog.stats["total_verifications"] += 1
                self.cog.user_data.reset_user(self.user_id)
                await interaction.response.send_message("✅ Verified!", ephemeral=True)
        else:
            attempts = self.cog.user_data.add_verification_attempt(self.user_id)
            await interaction.response.send_message(f"❌ Wrong code. Attempt {attempts}/{self.cog.user_data.max_attempts}", ephemeral=True)

def setup(bot):
    bot.add_cog(RulesSystem(bot))
