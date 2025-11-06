import discord
from discord.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio

class ServerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = "data/server_stats.json"
        self.stats_data = self.load_stats()
        self.cleanup_old_stats.start()
    
    def load_stats(self):
        """Load statistics from JSON file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.create_empty_stats()
        except Exception as e:
            print(f"Error loading statistics: {e}")
            return self.create_empty_stats()
    
    def create_empty_stats(self):
        """Create empty statistics structure"""
        return {
            "daily_stats": {},  # Format: "YYYY-MM-DD": {"new_members": 0, "left_members": 0, ...}
            "total_stats": {
                "total_members": 0,
                "total_messages": 0,
                "total_joins": 0,
                "total_leaves": 0
            }
        }
    
    def save_stats(self):
        """Save statistics to JSON file"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving statistics: {e}")
    
    def get_today_string(self):
        """Get today's date as string"""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_date_string(self, date):
        """Convert date to string"""
        return date.strftime("%Y-%m-%d")
    
    def ensure_today_stats(self):
        """Ensure today's statistics exist"""
        today = self.get_today_string()
        if today not in self.stats_data["daily_stats"]:
            self.stats_data["daily_stats"][today] = {
                "new_members": 0,
                "left_members": 0,
                "messages": 0,
                "voice_joins": 0,
                "reactions_added": 0,
                "commands_used": 0,
                "channels_created": 0,
                "roles_created": 0
            }
    
    def add_stat(self, stat_type, amount=1):
        """Add statistic"""
        self.ensure_today_stats()
        today = self.get_today_string()
        
        # Daily statistic
        if stat_type in self.stats_data["daily_stats"][today]:
            self.stats_data["daily_stats"][today][stat_type] += amount
        
        # Total statistic
        total_key = f"total_{stat_type}"
        if stat_type == "new_members":
            total_key = "total_joins"
        elif stat_type == "left_members":
            total_key = "total_leaves"
        
        if total_key in self.stats_data["total_stats"]:
            self.stats_data["total_stats"][total_key] += amount
        
        self.save_stats()
    
    def get_7_day_stats(self):
        """Get 7-day statistics"""
        stats_7_days = {
            "new_members": 0,
            "left_members": 0,
            "messages": 0,
            "voice_joins": 0,
            "reactions_added": 0,
            "commands_used": 0,
            "channels_created": 0,
            "roles_created": 0
        }
        
        # Calculate last 7 days
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = self.get_date_string(date)
            
            if date_str in self.stats_data["daily_stats"]:
                day_stats = self.stats_data["daily_stats"][date_str]
                for key in stats_7_days:
                    stats_7_days[key] += day_stats.get(key, 0)
        
        return stats_7_days
    
    def get_daily_breakdown(self):
        """Get daily breakdown for last 7 days"""
        daily_breakdown = []
        
        for i in range(6, -1, -1):  # Start from 6 days ago to today
            date = datetime.now() - timedelta(days=i)
            date_str = self.get_date_string(date)
            day_name = date.strftime("%a")  # Mon, Tue, etc.
            
            if date_str in self.stats_data["daily_stats"]:
                day_stats = self.stats_data["daily_stats"][date_str]
                daily_breakdown.append({
                    "date": date_str,
                    "day": day_name,
                    "stats": day_stats
                })
            else:
                daily_breakdown.append({
                    "date": date_str,
                    "day": day_name,
                    "stats": {
                        "new_members": 0,
                        "left_members": 0,
                        "messages": 0,
                        "voice_joins": 0,
                        "reactions_added": 0,
                        "commands_used": 0
                    }
                })
        
        return daily_breakdown
    
    @tasks.loop(hours=24)
    async def cleanup_old_stats(self):
        """Clean up statistics older than 30 days"""
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_str = self.get_date_string(cutoff_date)
        
        dates_to_remove = []
        for date_str in self.stats_data["daily_stats"]:
            if date_str < cutoff_str:
                dates_to_remove.append(date_str)
        
        for date_str in dates_to_remove:
            del self.stats_data["daily_stats"][date_str]
        
        if dates_to_remove:
            self.save_stats()
            print(f"Cleaned up {len(dates_to_remove)} old statistic entries")
    
    @cleanup_old_stats.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
    
    # Event Listeners
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Event: New member joined"""
        if not member.bot:  # Ignore bots
            self.add_stat("new_members")
            print(f"New member: {member.name} joined {member.guild.name}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Event: Member left the server"""
        if not member.bot:  # Ignore bots
            self.add_stat("left_members")
            print(f"Member left: {member.name} left {member.guild.name}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Event: Message was sent"""
        if not message.author.bot and message.guild:  # Ignore bot messages and DMs
            self.add_stat("messages")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Event: Voice channel status changed"""
        # If someone joins a voice channel
        if before.channel is None and after.channel is not None and not member.bot:
            self.add_stat("voice_joins")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Event: Reaction added"""
        if not user.bot and reaction.message.guild:
            self.add_stat("reactions_added")
    
    @commands.Cog.listener()
    async def on_application_command(self, ctx):
        """Event: Slash command used"""
        if not ctx.user.bot:
            self.add_stat("commands_used")
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Event: Channel created"""
        self.add_stat("channels_created")
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Event: Role created"""
        self.add_stat("roles_created")
    
    @discord.slash_command(name="statistics", description="Show server statistics for the last 7 days")
    async def statistics(self, ctx):
        """Slash command for server statistics"""
        try:
            await ctx.defer()  # Defer the response for processing time
            
            # Get 7-day statistics
            stats_7_days = self.get_7_day_stats()
            total_stats = self.stats_data["total_stats"]
            daily_breakdown = self.get_daily_breakdown()
            
            # Current member count
            current_members = len([m for m in ctx.guild.members if not m.bot])
            
            # Create main embed
            embed = discord.Embed(
                title=f"<:statistics:1411782823454441514> Server Statistics - {ctx.guild.name}",
                description="Statistics for the last 7 days",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Server info
            embed.add_field(
                name="🏠 Server Info",
                value=f"**Current Members:** {current_members:,}\n"
                      f"**Total Channels:** {len(ctx.guild.channels)}\n"
                      f"**Server Created:** {ctx.guild.created_at.strftime('%d.%m.%Y')}",
                inline=True
            )
            
            # 7-day member statistics
            net_growth = stats_7_days['new_members'] - stats_7_days['left_members']
            growth_emoji = "📈" if net_growth > 0 else "📉" if net_growth < 0 else "📊"
            
            embed.add_field(
                name="👥 Members (7 Days)",
                value=f"**New Members:** {stats_7_days['new_members']}\n"
                      f"**Members Left:** {stats_7_days['left_members']}\n"
                      f"**Net Growth:** {growth_emoji} {net_growth:+d}",
                inline=True
            )
            
            # Activity statistics
            embed.add_field(
                name="💬 Activity (7 Days)",
                value=f"**Messages:** {stats_7_days['messages']:,}\n"
                      f"**Voice Joins:** {stats_7_days['voice_joins']}\n"
                      f"**Reactions:** {stats_7_days['reactions_added']}\n"
                      f"**Commands Used:** {stats_7_days['commands_used']}",
                inline=True
            )
            
            # Total statistics
            embed.add_field(
                name="🔢 All-Time Totals",
                value=f"**Total Joins:** {total_stats['total_joins']:,}\n"
                      f"**Total Leaves:** {total_stats['total_leaves']:,}\n"
                      f"**Total Messages:** {total_stats['total_messages']:,}",
                inline=True
            )
            
            # Averages
            avg_messages = stats_7_days['messages'] / 7
            avg_new_members = stats_7_days['new_members'] / 7
            activity_rate = (avg_messages / max(current_members, 1)) * 100
            
            embed.add_field(
                name="📈 Daily Averages",
                value=f"**Messages:** {avg_messages:.1f}\n"
                      f"**New Members:** {avg_new_members:.1f}\n"
                      f"**Activity Rate:** {activity_rate:.1f}%",
                inline=True
            )
            
            # Daily breakdown in description format
            breakdown_text = "**Daily Breakdown (Last 7 Days):**\n"
            for day in daily_breakdown:
                breakdown_text += f"`{day['day']} {day['date'][-5:]}` - "
                breakdown_text += f"📥{day['stats']['new_members']} 📤{day['stats']['left_members']} "
                breakdown_text += f"💬{day['stats']['messages']}\n"
            
            embed.add_field(
                name="📅 Daily Breakdown",
                value=breakdown_text,
                inline=False
            )
            
            # Add footer
            embed.set_footer(
                text=f"Requested by {ctx.author.display_name}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            
            # Add server icon as thumbnail
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Error in statistics command: {e}")
            await ctx.followup.send("❌ An error occurred while generating statistics.")
    
    @discord.slash_command(name="reset_stats", description="Reset server statistics (Admin only)")
    @commands.has_permissions(administrator=True)
    async def reset_stats(self, ctx):
        """Reset all statistics (Admin only)"""
        try:
            self.stats_data = self.create_empty_stats()
            self.save_stats()
            
            embed = discord.Embed(
                title="🔄 Statistics Reset",
                description="All server statistics have been reset successfully!",
                color=0xff9900,
                timestamp=datetime.now()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            print(f"Error resetting statistics: {e}")
            await ctx.respond("❌ An error occurred while resetting statistics.", ephemeral=True)
    
    @discord.slash_command(name="export_stats", description="Export statistics as JSON file (Admin only)")
    @commands.has_permissions(administrator=True)
    async def export_stats(self, ctx):
        """Export statistics as downloadable JSON file"""
        try:
            await ctx.defer(ephemeral=True)
            
            # Create export data with readable timestamps
            export_data = {
                "server_name": ctx.guild.name,
                "server_id": ctx.guild.id,
                "export_date": datetime.now().isoformat(),
                "statistics": self.stats_data
            }
            
            # Save to temporary file
            export_filename = f"stats_export_{ctx.guild.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(export_filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Send file
            with open(export_filename, 'rb') as f:
                file = discord.File(f, filename=export_filename)
                await ctx.followup.send(
                    "📁 Here's your statistics export:",
                    file=file,
                    ephemeral=True
                )
            
            # Clean up temporary file
            os.remove(export_filename)
            
        except Exception as e:
            print(f"Error exporting statistics: {e}")
            await ctx.followup.send("❌ An error occurred while exporting statistics.", ephemeral=True)
    
    @discord.slash_command(name="stats_summary", description="Show a quick summary of today's statistics")
    async def stats_summary(self, ctx):
        """Quick summary of today's stats"""
        try:
            today = self.get_today_string()
            today_stats = self.stats_data["daily_stats"].get(today, {
                "new_members": 0,
                "left_members": 0,
                "messages": 0,
                "voice_joins": 0,
                "reactions_added": 0,
                "commands_used": 0
            })
            
            embed = discord.Embed(
                title="📈 Today's Summary",
                description=f"Statistics for {datetime.now().strftime('%A, %B %d, %Y')}",
                color=0x0099ff,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Today's Activity",
                value=f"**New Members:** {today_stats['new_members']}\n"
                      f"**Members Left:** {today_stats['left_members']}\n"
                      f"**Messages:** {today_stats['messages']:,}\n"
                      f"**Voice Joins:** {today_stats['voice_joins']}\n"
                      f"**Reactions:** {today_stats['reactions_added']}\n"
                      f"**Commands:** {today_stats['commands_used']}",
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            print(f"Error in stats summary: {e}")
            await ctx.respond("❌ An error occurred while generating today's summary.")
    
    @tasks.loop(hours=24)
    async def cleanup_old_stats(self):
        """Clean up statistics older than 30 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            cutoff_str = self.get_date_string(cutoff_date)
            
            dates_to_remove = []
            for date_str in self.stats_data["daily_stats"]:
                if date_str < cutoff_str:
                    dates_to_remove.append(date_str)
            
            for date_str in dates_to_remove:
                del self.stats_data["daily_stats"][date_str]
            
            if dates_to_remove:
                self.save_stats()
                print(f"Cleaned up {len(dates_to_remove)} old statistic entries")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    @cleanup_old_stats.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.cleanup_old_stats.cancel()

# Setup function for loading the cog
def setup(bot):
    bot.add_cog(ServerStats(bot))