import json
import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
import pytz
from discord.ui import Container
from discord import SeparatorSpacingSize

banner = "https://cdn.discordapp.com/attachments/1384650878161784934/1406659991309648002/ticket.png?ex=68a345b4&is=68a1f434&hm=16cd2ad91e53ac2ba0d6074fbfb7022dcbfa736a8ac6377264314d06706e8848&"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Persistent Views for use after a restart
class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='➕ Create a Ticket', style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        cog = interaction.client.get_cog("TicketSystem")
        if cog and not cog.is_open():
            hours = cog.get_opening_hours_text()
            container = Container()
            banner = discord.ui.MediaGallery()
            banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764647779205270/support-times.png?ex=68f3b045&is=68f25ec5&hm=244c1fcb00a51a17e3de1e7b290493f225778eb073b0811255386eeacff5376a&=&format=webp&quality=lossless&width=1208&height=261")
            container.add_item(banner)
            container.add_text("## ⏰ Support Currently Closed")
            container.add_separator(spacing=SeparatorSpacingSize.small)
            container.add_text(f"Our Support is currently closed.\n\n{hours}\n-# Please try again during our opening hours.")
            view = discord.ui.View(container, timeout=None)
            await interaction.response.send_message(view=view, ephemeral=True)
            return

        await interaction.response.send_message('Creating ticket...', ephemeral=True)

        ticket_channel = await interaction.guild.create_text_channel(
            name=f'ticket-{interaction.user.name}',
            category=interaction.guild.get_channel(1421784692969177200)
        )

        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket_channel.set_permissions(interaction.guild.default_role, read_messages=False, send_messages=False)

        container = Container()
        banner = discord.ui.MediaGallery()
        banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764647300927600/support-tickets.png?ex=68f3b045&is=68f25ec5&hm=515197dd3b455268602d79e7519f0973a31332b25200dd87dc2e1b7239cbe1ac&=&format=webp&quality=lossless&width=1208&height=261")
        container.add_item(banner)
        container.add_text("## Welcome to Your Ticket")
        container.add_separator(spacing=SeparatorSpacingSize.small)
        container.add_text("A friendly and helpful team member will shortly take care of your request with patience and attention. We want to ensure you receive the best possible support and are always here to help you and answer your questions. Thank you for your trust – we look forward to helping you!")

        view = discord.ui.View(container, timeout=None)
        await ticket_channel.send(view=view)
        await ticket_channel.send(view=TicketSystemView())

        try:
            ticket_info_path = "data/ticket_info.json"
            ticket_info = {}
            if os.path.exists(ticket_info_path):
                with open(ticket_info_path, "r") as f:
                    ticket_info = json.load(f)

            ticket_info[str(ticket_channel.id)] = interaction.user.id

            with open(ticket_info_path, "w") as f:
                json.dump(ticket_info, f, indent=2)

            embed = discord.Embed(
                title="Ticket Created",
                description=f"Your ticket has been successfully created: {ticket_channel.mention}",
                color=discord.Color.green()
            )
            try:
                await interaction.user.send(embed=embed)
            except discord.Forbidden:
                print(f"Could not send DM to user {interaction.user.id}")
        except Exception as e:
            print(f"Error saving ticket information: {e}")

    @discord.ui.button(label='⭐ Rating Average', style=discord.ButtonStyle.secondary, row=1, custom_id="rating_avg")
    async def show_average(self, button: discord.ui.Button, interaction: discord.Interaction):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.send_average_rating(interaction, ephemeral=True)
        else:
            await interaction.response.send_message("Rating system is currently not available.", ephemeral=True)


class TicketSystemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='❌ Close the Ticket', style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('Closing ticket!', ephemeral=True)

        creator_id = None
        ticket_info_path = "data/ticket_info.json"
        try:
            if os.path.exists(ticket_info_path):
                with open(ticket_info_path, "r") as f:
                    ticket_info = json.load(f)
                    creator_id = ticket_info.get(str(interaction.channel.id))

                    if str(interaction.channel.id) in ticket_info:
                        del ticket_info[str(interaction.channel.id)]
                        with open(ticket_info_path, "w") as f:
                            json.dump(ticket_info, f, indent=2)
        except Exception as e:
            print(f"Error retrieving ticket information: {e}")

        if creator_id:
            user = interaction.client.get_user(int(creator_id))
            if not user:
                try:
                    user = await interaction.client.fetch_user(int(creator_id))
                except Exception as e:
                    print(f"Error fetching user: {e}")

            if user:
                cog = interaction.client.get_cog("TicketSystem")
                if cog:
                    try:
                        ticket_name = interaction.channel.name
                        guild_id = interaction.guild.id

                        container = Container()
                        banner = discord.ui.MediaGallery()
                        banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764646973898773/support-rating.png?ex=68f3b045&is=68f25ec5&hm=4db9d39e0ad0c37f5ba59acbf0539a2e9e9249ee0e8ba0164f4cd5b38ff06012&=&format=webp&quality=lossless&width=1208&height=261")
                        container.add_item(banner)
                        container.add_text("# Ticket Rating")
                        container.add_separator(spacing=SeparatorSpacingSize.small)
                        container.add_text(f"Your ticket **{ticket_name}** has been closed.\nHow would you rate our support?")
                        
                        view = discord.ui.View(container, timeout=None)
                        rating_view = RatingView(ticket_name=ticket_name, guild_id=guild_id)
                        
                        try:
                            await user.send(view=view)
                            message = await user.send(view=rating_view)

                            rating_messages_path = "data/rating_messages.json"
                            rating_data = {}
                            if os.path.exists(rating_messages_path):
                                with open(rating_messages_path, "r") as f:
                                    rating_data = json.load(f)

                            rating_data[str(message.id)] = {
                                "user_id": creator_id,
                                "guild_id": interaction.guild.id,
                                "ticket_name": ticket_name
                            }

                            with open(rating_messages_path, "w") as f:
                                json.dump(rating_data, f, indent=2)

                            await cog.log_ticket_action(
                                guild_id=guild_id,
                                action="Ticket closed and rating request sent",
                                ticket_name=ticket_name,
                                user=user
                            )

                            print(f"Rating request sent to {user.name} ({user.id}).")
                        except discord.Forbidden:
                            print(f"Could not send DM to user {creator_id} - DMs disabled")
                            await interaction.followup.send(f"User has DMs disabled, could not send rating request.", ephemeral=True)
                        except Exception as e:
                            print(f"Error sending rating request: {e}")
                    except Exception as e:
                        print(f"Error creating rating request: {e}")
            else:
                print(f"Could not find user with ID {creator_id}")

        await interaction.channel.delete()

    @discord.ui.button(label='🔒 Claim Ticket', style=discord.ButtonStyle.secondary, custom_id="claim_ticket")
    async def claim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message('You do not have the required permissions to claim tickets!', ephemeral=True)
            return

        await interaction.response.send_message('Ticket has been claimed!', ephemeral=True)
        await interaction.channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        container = Container()
        banner = discord.ui.MediaGallery()
        banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764647300927600/support-tickets.png?ex=68f501c5&is=68f3b045&hm=59aea2e4d0f6f5cf4b1c44beadef1be9fd71533bfc4a96dbbf5b8ddfdfca5bdd&=&format=webp&quality=lossless&width=1730&height=374")
        container.add_item(banner)
        container.add_text("# Ticket Claimed")
        container.add_separator(spacing=SeparatorSpacingSize.small)
        container.add_text(f"{interaction.user.mention} has claimed the ticket and will assist you shortly.")

        view = discord.ui.View(container, timeout=None)
        await interaction.channel.send(view=view)

        try:
            ticket_info_path = "data/ticket_info.json"
            if os.path.exists(ticket_info_path):
                with open(ticket_info_path, "r") as f:
                    ticket_info = json.load(f)
                    creator_id = ticket_info.get(str(interaction.channel.id))

                    if creator_id:
                        user = interaction.client.get_user(int(creator_id))
                        if user:
                            dm_embed = discord.Embed(
                                title="Ticket Update",
                                description=f"Your ticket **{interaction.channel.name}** has been claimed by {interaction.user.mention}.",
                                color=discord.Color.green()
                            )
                            try:
                                await user.send(embed=dm_embed)
                            except discord.Forbidden:
                                print(f"Could not send DM to user {creator_id} - DMs disabled")
        except Exception as e:
            print(f"Error sending claim notification: {e}")

    @discord.ui.button(label='🔓 Release Ticket', style=discord.ButtonStyle.secondary, custom_id="unclaim_ticket")
    async def unclaim_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message('You do not have the required permissions to release tickets!', ephemeral=True)
            return

        await interaction.response.send_message('Ticket has been released!', ephemeral=True)

        container = Container()
        banner = discord.ui.MediaGallery()
        banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764647300927600/support-tickets.png?ex=68f501c5&is=68f3b045&hm=59aea2e4d0f6f5cf4b1c44beadef1be9fd71533bfc4a96dbbf5b8ddfdfca5bdd&=&format=webp&quality=lossless&width=1730&height=374")
        container.add_item(banner)
        container.add_text("# Ticket Released")
        container.add_separator(spacing=SeparatorSpacingSize.small)
        container.add_text(f"{interaction.user.mention} has released the ticket.")

        view = discord.ui.View(container, timeout=None)
        await interaction.channel.send(view=view)


class RatingSelect(discord.ui.Select):
    def __init__(self, ticket_name=None, guild_id=None):
        self.ticket_name = ticket_name
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="⭐⭐⭐⭐⭐ Excellent", value="5"),
            discord.SelectOption(label="⭐⭐⭐⭐ Good", value="4"),
            discord.SelectOption(label="⭐⭐⭐ Average", value="3"),
            discord.SelectOption(label="⭐⭐ Poor", value="2"),
            discord.SelectOption(label="⭐ Very Poor", value="1")
        ]
        super().__init__(placeholder="Please rate our support", options=options, custom_id="rating_select")

    async def callback(self, interaction: discord.Interaction):
        rating = int(self.values[0])

        cog = interaction.client.get_cog("TicketSystem") 
        if cog:
            message_id = str(interaction.message.id)
            if message_id in cog.submitted_ratings:
                old_rating = cog.submitted_ratings[message_id]
                stars = "⭐" * old_rating

                embed = discord.Embed(
                    title="Rating Already Submitted",
                    description=f"You have already rated our support with {stars} ({old_rating}/5). Changes are not possible.",
                    color=discord.Color.gold()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await cog.add_rating(rating)

            stars = "⭐" * rating
            embed = discord.Embed(
                title="Thank You for Your Rating!",
                description=f"You have rated our support with {stars} ({rating}/5).",
                color=discord.Color.gold()
            )

            avg = cog.get_average_rating()
            avg_stars = "⭐" * int(avg)
            if avg % 1 >= 0.5:
                avg_stars += "✨"

            embed.add_field(
                name="Current Average Rating",
                value=f"{avg_stars} ({avg:.1f}/5) based on {cog.ratings.get('count', 0)} ratings"
            )

            if self.ticket_name and self.guild_id:
                await cog.log_ticket_action(
                    guild_id=self.guild_id,
                    action=f"Ticket rated with {rating}/5 stars",
                    ticket_name=self.ticket_name,
                    user=interaction.user
                )

            try:
                disabled_view = RatingViewDisabled(rating=rating, avg=avg, count=cog.ratings.get('count', 0))
                await interaction.message.edit(view=disabled_view)
                await cog.mark_rating_as_submitted(interaction.message.id, rating)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                print(f"Error updating rating message: {e}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Rating system is currently not available.", ephemeral=True)


class RatingView(discord.ui.View):
    def __init__(self, ticket_name=None, guild_id=None):
        super().__init__(timeout=None)
        self.add_item(RatingSelect(ticket_name=ticket_name, guild_id=guild_id))

    @discord.ui.button(label="⭐ Rating Average", style=discord.ButtonStyle.secondary, custom_id="dm_rating_avg")
    async def show_average(self, button: discord.ui.Button, interaction: discord.Interaction):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.send_average_rating(interaction, ephemeral=True)
        else:
            await interaction.response.send_message("Rating system is currently not available.", ephemeral=True)


class RatingViewDisabled(discord.ui.View):
    def __init__(self, rating=None, avg=None, count=0):
        super().__init__(timeout=None)
        self.rating = rating
        self.avg = avg
        self.count = count

    @discord.ui.button(label="⭐ Rating Average", style=discord.ButtonStyle.secondary, custom_id="dm_rating_avg_disabled")
    async def show_average(self, button: discord.ui.Button, interaction: discord.Interaction):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.send_average_rating(interaction, ephemeral=True)
        else:
            await interaction.response.send_message("Rating system is currently not available.", ephemeral=True)


class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ratings = {}
        self.submitted_ratings = {}
        self.load_ratings()
        self.load_submitted_ratings()

        self.ticket_create_view = None
        self.ticket_system_view = None
        self.rating_view = None
        
        self.timezone = pytz.timezone('Europe/Berlin')
        self.opening_hours_channel_id = 1428745792063012966
        self.opening_hours_message_id = None
        
    def load_ratings(self):
        try:
            ratings_path = "data/ratings.json"
            if os.path.exists(ratings_path):
                with open(ratings_path, "r") as f:
                    self.ratings = json.load(f)
            else:
                self.ratings = {"total": 0, "count": 0, "ratings": []}
                self.save_ratings()
        except Exception as e:
            print(f"Error loading ratings: {e}")
            self.ratings = {"total": 0, "count": 0, "ratings": []}

    def save_ratings(self):
        try:
            ratings_path = "data/ratings.json"
            with open(ratings_path, "w") as f:
                json.dump(self.ratings, f, indent=2)
        except Exception as e:
            print(f"Error saving ratings: {e}")

    def load_submitted_ratings(self):
        try:
            submitted_path = "data/submitted_ratings.json"
            if os.path.exists(submitted_path):
                with open(submitted_path, "r") as f:
                    self.submitted_ratings = json.load(f)
            else:
                self.submitted_ratings = {}
                self.save_submitted_ratings()
        except Exception as e:
            print(f"Error loading submitted ratings: {e}")
            self.submitted_ratings = {}

    def save_submitted_ratings(self):
        try:
            submitted_path = "data/submitted_ratings.json"
            with open(submitted_path, "w") as f:
                json.dump(self.submitted_ratings, f, indent=2)
        except Exception as e:
            print(f"Error saving submitted ratings: {e}")

    async def mark_rating_as_submitted(self, message_id, rating):
        message_id = str(message_id)
        self.submitted_ratings[message_id] = rating
        self.save_submitted_ratings()

    def get_average_rating(self):
        if self.ratings.get("count", 0) > 0:
            return self.ratings.get("total", 0) / self.ratings.get("count", 1)
        return 0.0

    async def add_rating(self, rating):
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            print(f"Invalid rating: {rating}")
            return False

        if "total" not in self.ratings:
            self.ratings["total"] = 0
        if "count" not in self.ratings:
            self.ratings["count"] = 0
        if "ratings" not in self.ratings:
            self.ratings["ratings"] = []

        self.ratings["total"] += rating
        self.ratings["count"] += 1
        self.ratings["ratings"].append(rating)

        self.save_ratings()
        return True

    def is_open(self):
        now = datetime.now(self.timezone)
        current_hour = now.hour
        is_weekend = now.weekday() >= 5
        
        if is_weekend:
            return 8 <= current_hour < 20
        else:
            return 8 <= current_hour < 18

    def get_opening_hours_text(self):
        return (
            "**📅 Opening Hours:**\n"
            "**Monday - Friday:** 8:00 AM - 6:00 PM\n"
            "**Saturday - Sunday:** 8:00 AM - 8:00 PM"
        )

    def get_status_embed(self):
        is_open = self.is_open()
        now = datetime.now(self.timezone)
        
        if is_open:
            color = discord.Color.green()
            status = "🟢 OPEN"
            description = "Our support team is currently available to help you!"
        else:
            color = discord.Color.red()
            status = "🔴 CLOSED"
            description = "Our support team is currently offline. Please try again during our opening hours."
        
        embed = discord.Embed(
            title=f"Support Status: {status}",
            description=description,
            color=color,
            timestamp=now
        )
        
        embed.add_field(
            name="Opening Hours",
            value=self.get_opening_hours_text(),
            inline=False
        )
        
        embed.set_footer(text="🚀oppro-network.de™ | Last updated")
        
        return embed

    @tasks.loop(minutes=5)
    async def update_opening_hours_message(self):
        try:
            if not self.opening_hours_message_id:
                return
                
            channel = self.bot.get_channel(self.opening_hours_channel_id)
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(self.opening_hours_message_id)
                embed = self.get_status_embed()
                await message.edit(embed=embed)
            except discord.NotFound:
                await self.create_opening_hours_message()
        except Exception as e:
            print(f"Error updating opening hours message: {e}")

    async def create_opening_hours_message(self):
        try:
            channel = self.bot.get_channel(self.opening_hours_channel_id)
            if not channel:
                print(f"Opening hours channel not found: {self.opening_hours_channel_id}")
                return
            
            # Check if message already exists in channel
            try:
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds:
                        embed = message.embeds[0]
                        if embed.title and "Support Status:" in embed.title:
                            self.opening_hours_message_id = message.id
                            print(f"Found existing opening hours message: {message.id}")
                            # Update the message with current status
                            new_embed = self.get_status_embed()
                            await message.edit(embed=new_embed)
                            # Save the ID
                            opening_hours_path = "data/opening_hours.json"
                            with open(opening_hours_path, "w") as f:
                                json.dump({"opening_hours_message_id": message.id}, f, indent=2)
                            return
            except Exception as e:
                print(f"Error checking for existing message: {e}")
            
            # Create new message only if none exists
            embed = self.get_status_embed()
            message = await channel.send(embed=embed)
            self.opening_hours_message_id = message.id
            print(f"Created new opening hours message: {message.id}")
            
            opening_hours_path = "data/opening_hours.json"
            data = {"opening_hours_message_id": message.id}
            try:
                if os.path.exists(opening_hours_path):
                    with open(opening_hours_path, "r") as f:
                        existing_data = json.load(f)
                        data.update(existing_data)

                with open(opening_hours_path, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving opening hours message ID: {e}")
                
        except Exception as e:
            print(f"Error creating opening hours message: {e}")

    def load_opening_hours_message_id(self):
        try:
            opening_hours_path = "data/opening_hours.json"
            if os.path.exists(opening_hours_path):
                with open(opening_hours_path, "r") as f:
                    data = json.load(f)
                    self.opening_hours_message_id = data.get("opening_hours_message_id")
        except Exception as e:
            print(f"Error loading opening hours message ID: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            print(f"Ticket System for {self.bot.user.name} is ready!")

            self.ticket_create_view = TicketCreateView()
            self.ticket_system_view = TicketSystemView()
            self.rating_view = RatingView()

            self.bot.add_view(self.ticket_create_view)
            self.bot.add_view(self.ticket_system_view)
            self.bot.add_view(self.rating_view)
            self.bot.add_view(RatingViewDisabled())

            await self.check_and_update_rating_messages()

            message_info_path = "data/message_info.json"
            if os.path.exists(message_info_path):
                with open(message_info_path, "r") as f:
                    data = json.load(f)
                    channel_id = data["channel_id"]
                    message_id = data["message_id"]

                channel = self.bot.get_channel(channel_id)
                if channel:
                    try:
                        message = await channel.fetch_message(message_id)
                        print(f"Message already exists: {message.id}")
                    except discord.NotFound:
                        print("Message not found. Creating new message.")
                        await self.create_ticket_message(channel)
                else:
                    print("Channel not found. Using default channel.")
                    default_channel = self.bot.get_channel(1421784878134853703)
                    if default_channel:
                        await self.create_ticket_message(default_channel)
            else:
                print("No saved messages found. Creating new one.")
                default_channel = self.bot.get_channel(1421784878134853703)
                if default_channel:
                    await self.create_ticket_message(default_channel)

            self.load_opening_hours_message_id()
            if self.opening_hours_message_id:
                try:
                    channel = self.bot.get_channel(self.opening_hours_channel_id)
                    if channel:
                        message = await channel.fetch_message(self.opening_hours_message_id)
                        embed = self.get_status_embed()
                        await message.edit(embed=embed)
                        print(f"Opening hours message updated: {self.opening_hours_message_id}")
                except discord.NotFound:
                    await self.create_opening_hours_message()
            else:
                await self.create_opening_hours_message()
            
            if not self.update_opening_hours_message.is_running():
                self.update_opening_hours_message.start()

        except Exception as e:
            print(f"Error starting ticket system: {e}")
            default_channel = self.bot.get_channel(1421784878134853703)
            if default_channel:
                await self.create_ticket_message(default_channel)

    async def check_and_update_rating_messages(self):
        try:
            rating_messages_path = "data/rating_messages.json"
            if os.path.exists(rating_messages_path):
                with open(rating_messages_path, "r") as f:
                    rating_messages = json.load(f)

                for message_id, data in rating_messages.items():
                    if message_id in self.submitted_ratings:
                        user_id = data.get("user_id")
                        if user_id:
                            try:
                                user = await self.bot.fetch_user(int(user_id))
                                if user:
                                    try:
                                        channel = await user.create_dm()
                                        message = await channel.fetch_message(int(message_id))

                                        rating = self.submitted_ratings[message_id]
                                        avg = self.get_average_rating()
                                        count = self.ratings.get("count", 0)

                                        disabled_view = RatingViewDisabled(rating=rating, avg=avg, count=count)
                                        await message.edit(view=disabled_view)
                                        print(f"Rating message {message_id} for user {user_id} updated")
                                    except discord.NotFound:
                                        print(f"Rating message {message_id} not found")
                                    except Exception as e:
                                        print(f"Error updating rating message {message_id}: {e}")
                            except Exception as e:
                                print(f"Error loading user {user_id}: {e}")
        except Exception as e:
            print(f"Error checking rating messages: {e}")

    async def create_ticket_message(self, channel):
        container = Container()
        banner = discord.ui.MediaGallery()
        banner.add_item("https://media.discordapp.net/attachments/1420436338284695657/1428764647300927600/support-tickets.png?ex=68f501c5&is=68f3b045&hm=59aea2e4d0f6f5cf4b1c44beadef1be9fd71533bfc4a96dbbf5b8ddfdfca5bdd&=&format=webp&quality=lossless&width=1730&height=374")
        container.add_item(banner)
        container.add_text("# Ticket System")
        container.add_separator(spacing=SeparatorSpacingSize.small)
        container.add_text("Here you have the opportunity to create a ticket so that a dedicated team member can take care of your concern as quickly as possible. We are here to help and support you to assist you in the best possible way.")
        view = discord.ui.View(container, timeout=None)
        try:
            if not self.ticket_create_view:
                self.ticket_create_view = TicketCreateView()

            message = await channel.send(view=view)
            view_message = await channel.send(view=self.ticket_create_view)
            self.save_message_info(channel.id, message.id, view_message.id)
            print(f"Message successfully sent and ID saved: {message.id}, {view_message.id}")
        except discord.Forbidden:
            print("Error: Bot does not have permission to send messages.")
        except discord.HTTPException as e:
            print(f"Error sending message: {e}")

    def save_message_info(self, channel_id, message_id, view_message_id):
        data = {
            "channel_id": channel_id,
            "message_id": message_id,
            "view_message_id": view_message_id
        }
        try:
            message_info_path = "data/message_info.json"
            with open(message_info_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Message information saved: Channel {channel_id}, Message {message_id}, View {view_message_id}")
        except Exception as e:
            print(f"Error saving message information: {e}")

    async def send_average_rating(self, interaction, ephemeral=True):
        avg = self.get_average_rating()
        avg_formatted = f"{avg:.1f}"

        full_stars = int(avg)
        has_half_star = avg % 1 >= 0.5

        stars = "⭐" * full_stars
        if has_half_star:
            stars += "✨"

        embed = discord.Embed(
            title="Rating Average",
            description=f"Our current average rating is {stars} ({avg_formatted}/5)",
            color=discord.Color.gold()
        )

        if "ratings" in self.ratings and self.ratings["ratings"]:
            ratings_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for r in self.ratings["ratings"]:
                if r in ratings_count:
                    ratings_count[r] += 1

            stats = "\n".join([f"{'⭐' * i}: {count} rating(s)" for i, count in ratings_count.items() if count > 0])
            embed.add_field(name="Distribution", value=stats)

        embed.set_footer(text=f"Based on {self.ratings.get('count', 0)} ratings")

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=ephemeral)
        except Exception as e:
            print(f"Error sending rating average: {e}")
            try:
                await interaction.followup.send(embed=embed, ephemeral=ephemeral)
            except:
                pass

    async def log_ticket_action(self, guild_id, action, ticket_name, user=None):
        """Logs ticket actions in a log channel"""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        log_channel_id = 1421833160492187759
        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="Ticket Log",
            description=f"**Action:** {action}\n**Ticket:** {ticket_name}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        if user:
            embed.add_field(name="User", value=f"{user.mention} ({user.name})")
            embed.set_thumbnail(url=user.display_avatar.url)

        await log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(TicketSystem(bot))