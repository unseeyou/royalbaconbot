import discord
import datetime
import asyncio
from discord.ext import commands
from discord import app_commands
from typing import Literal


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.interviews = {}

    @commands.Cog.listener(name='on_message')
    async def interview_logger(self, message: discord.Message):
        bot: commands.Bot = self.bot
        if len(self.interviews) == 0:
            for c in bot.get_guild(1161898338988347452).channels:
                for l in bot.get_guild(1161898338988347452).threads:
                    if str(c.id) in l.name:
                        if c.category.id == 1170658500859416657:
                            self.interviews[c] = l
        if message.channel.category.id == 1170658500859416657:
            log_thread: discord.Thread = self.interviews[message.channel]
            webhooks = await log_thread.parent.webhooks()
            if len(webhooks) == 0 or 'interview logger' not in [w.name for w in webhooks]:
                webhook = await log_thread.parent.create_webhook(name='interview logger')
            else:
                for hook in webhooks:
                    if hook.name == 'interview logger':
                        webhook = hook
            await webhook.send(str(message.content),
                               username=message.author.name,
                               avatar_url=message.author.display_avatar.url,
                               thread=log_thread)

    @app_commands.command(name='interview', description='starts an interview session')
    @app_commands.checks.has_permissions(manage_channels=True)
    async def _interview(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            log_channel = discord.utils.get(interaction.guild.text_channels, id=1170658361990205482)
            category = discord.utils.get(interaction.guild.categories, id=1170658500859416657)
            channel = await interaction.guild.create_text_channel(name=f'interview-{member.name}', category=category)
            await channel.edit(position=1, overwrites={interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                                       member: discord.PermissionOverwrite(send_messages=True, view_channel=True)})
            await channel.send(f'{member.mention}, an interview has started with you by {interaction.user.mention}!')
            await member.send(f'Hello! This is a notification that you have been called into an interview in {channel.mention}. Please come ASAP! Thanks!\n   - RoyalBaconYT Mod Team')
            log = await log_channel.send(f"Created an interview channel at {channel.mention}")
            for c in interaction.guild.channels:
                for l in interaction.guild.threads:
                    if str(c.id) in l.name:
                        if c.category.id == 1170658500859416657:
                            self.interviews[c] = l
            thread = await log.create_thread(name=f'log [{channel.id}]')
            await interaction.followup.send(f'Succesfully created interview with {member.name}! --> {channel.mention}')
            self.interviews[channel] = thread
        except Exception as err:
            print(err)
            await interaction.followup.send(err)

    @commands.hybrid_command(name='clear', help='purges messages')  # clear command
    @commands.has_permissions(manage_channels=True)
    async def clear(self, ctx: commands.Context, quantity: int):
        await ctx.defer(ephemeral=True)
        await ctx.send(f"clearing {quantity} messages")
        channel = ctx.channel
        await channel.purge(limit=int(quantity))  # clears command usage as well as amount of messages
        await asyncio.sleep(0.2)
        msg = await ctx.send(f"cleared {quantity} messages!")
        msg2 = await ctx.send("just a reminder that this bot has trouble deleting messages more then 2 weeks old")
        await asyncio.sleep(2)
        await msg.delete()
        await msg2.delete()

    @commands.hybrid_command(name='purge', description='clear but only in a certain timeframe')
    @app_commands.describe(time='age of the messages to purge')
    @commands.has_permissions(manage_channels=True)
    async def _purge(self, ctx: commands.Context, time: int, time_type: Literal["Day", "Hour", "Minute"]):
        await ctx.defer()
        current_time = datetime.datetime.now()
        channel = ctx.channel
        timedelta = datetime.timedelta
        if time_type == "Day":
            current_time -= timedelta(days=time)
        elif time_type == "Hour":
            current_time -= timedelta(hours=time)
        elif time_type == "Minute":
            current_time -= timedelta(minutes=time)
        purge = await channel.purge(before=current_time)
        msg = await ctx.send(f'Purged the channel! Deleted ({len(purge)}) messages.')
        await asyncio.sleep(4)
        await msg.delete()

    @commands.hybrid_command(help='gives a role')
    @commands.has_permissions(manage_channels=True)
    async def role(self, ctx, member: discord.Member = None, role: discord.Role = None):
        if member is None:
            member = ctx.message.author
        else:
            pass
        role = discord.utils.get(ctx.guild.roles, name=role.name)
        await member.add_roles(role)
        await ctx.send(f"gave {role.name} to {member.name}!")

    @commands.hybrid_command(help='gives everyone a role - be careful!!!')
    @commands.has_permissions(manage_channels=True)
    async def roleall(self, ctx, role: discord.Role):
        members = ctx.guild.members
        for member in members:
            try:
                await member.add_roles(role)
            except Exception:
                pass  # best error handling
        await ctx.send('gave the role to everyone I had permission to')

    @commands.hybrid_command(help='the ultimate undo if you accidentlly do /roleall')
    @commands.has_permissions(manage_channels=True)
    async def unroleall(self, ctx, role: discord.Role):
        members = ctx.guild.members
        for user in members:
            await user.remove_roles(role)
        await ctx.send('removed role from all the members I had permission to')

    @commands.hybrid_command(help='trololol')
    @commands.has_permissions(manage_channels=True)
    async def removerole(self, ctx, role: discord.Role, user: discord.Member):
        await user.remove_roles(role)
        await ctx.send(f'removed {role.name} from {user.name}!')

    @commands.hybrid_command(help='locks down a channel, only admins can talk and unlock it', aliases=['lock', 'ld'])
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx: commands.Context):
        perms = ctx.channel.overwrites_for(ctx.guild.default_role)
        print(perms.view_channel)
        if perms.view_channel is not None and not perms.view_channel:
            print('private channel')
            await ctx.send("I cannot lock down a private channel!")
            return 0
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(ctx.channel.mention + " ***is now in lockdown.***")

    @commands.hybrid_command(help='unlocks a channel', aliases=['unlockdown', 'uld', 'ul'])
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(ctx.channel.mention + " ***has been unlocked.***")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass
        if isinstance(error, discord.ext.commands.errors.MissingPermissions):
            await ctx.send("You are not an admin!")
        else:
            print(error)
            await ctx.send(error)

    @commands.hybrid_command(help='mute someone!')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(duration='max: 28 days')
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason specified", duration: int,
                   duration_type: Literal["Day", "Hour", "Minute", "Second"]):
        embed = discord.Embed(title="MUTE",
                              description=f"timed out {member.mention} for reason: `{reason}`\nDuration: `{duration} {duration_type}{'s' if duration != 1 else ''}`",
                              colour=discord.Colour.red())
        if duration_type == "Day":
            length = datetime.timedelta(days=duration)
        elif duration_type == "Hour":
            length = datetime.timedelta(hours=duration)
        elif duration_type == "Minute":
            length = datetime.timedelta(minutes=duration)
        elif duration_type == "Second":
            length = datetime.timedelta(seconds=duration)
        await member.timeout(length, reason=reason)
        await member.send(embed=embed)
        await ctx.send(embed=embed)

    @commands.hybrid_command(help='unmute someone!')
    @commands.has_permissions(manage_channels=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = 'No reason specified'):
        embed = discord.Embed(title="UNMUTE", description=f"unmuted {member.mention} for reason: `{reason}`",
                              colour=discord.Colour.red())
        await member.timeout(None, reason=reason)
        await member.send(embed=embed)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='avatar', description="gets a requested user's avatar")
    @app_commands.describe(user='the user you are trying to get')
    async def _avatar(self, ctx: commands.Context, user: discord.User):
        await ctx.defer()
        try:
            avatar_url = user.display_avatar
        except AttributeError:
            avatar_url = 'https://th.bing.com/th/id/OIP.oMyBuVEjo8ACQpQ8oMeG4gAAAA?pid=ImgDet&w=300&h=300&rs=1'  # unavailable
        embed = discord.Embed(title=f"{user.name}'s Avatar", url=avatar_url)
        embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=avatar_url, url=avatar_url)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}",
                         icon_url=avatar_url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Commands(bot))
