import discord
import os
import traceback
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from rb_rules import rules as server_rules

load_dotenv()
TOKEN = os.getenv("RB_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(intents=intents, command_prefix='!', case_insensitive=True,
                   activity=discord.Activity(type=discord.ActivityType.watching, name='Royal Bacon YT'))


class MyNewHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, title='HELP')
            await destination.send(embed=emby)


bot.help_command = MyNewHelp()


@bot.event
async def on_ready():
    print(f'Logged in/Rejoined as {bot.user} (ID: {bot.user.id})')
    print(
        f"https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=applications.commands%20bot")
    print('------ Error Log ------')

@bot.event
async def setup_hook():
    print("If you are seeing this then unseeyou's epic bot is working!")

@bot.event
async def on_message(message: discord.Message):
    if message.channel.type == discord.ChannelType.news:
        await message.publish()
    await bot.process_commands(message)

@bot.hybrid_command(help='probably my ping', name='ping')
async def _ping(ctx: commands.Context):
    latency = round(bot.latency*1000, 2)
    message = await ctx.send("Pong!")
    await message.edit(content=f"Pong! My ping is `{latency} ms`")
    print(f'Ping: `{latency} ms`')

@bot.hybrid_command(help='sends the guild info', name='guild_info')
async def _guild_info(ctx: commands.Context):
    guild = ctx.guild
    embed = discord.Embed(title='Guild Info', description=f'Name: {guild.name}\nID: {guild.id}\nOwner: {guild.owner}', colour=discord.Colour.blue())
    embed.set_image(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.hybrid_command(help='closes the interview channel', name='close')
@commands.has_permissions(manage_messages=True)
async def _close(ctx: commands.Context):
    try:
        if ctx.channel.category.id == 1170658500859416657:
            await ctx.reply('Interview closed!')
            channel: discord.TextChannel = ctx.channel
            for member in ctx.channel.members:
                if not member.guild_permissions.moderate_members:
                    await channel.edit(position=1,
                                       overwrites={ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                                   member: discord.PermissionOverwrite(send_messages=False, view_channel=True)})
            closed_category = discord.utils.get(ctx.guild.categories, id=1170665554516922460)
            channel_names = []
            for existing_channel in reversed(closed_category.channels):
                existing_channel: discord.TextChannel
                channel_names.append(existing_channel.name)
            if f'closed-{channel.name}-1' not in channel_names:
                valid_name = f'closed-{channel.name}-1'
            else:
                i = 2
                while f'closed-{channel.name}-{i}' in channel_names:
                    i += 1
                valid_name = f'closed-{channel.name}-{i}'

            await channel.edit(category=closed_category, name=valid_name)
            sorted_channels = sorted(closed_category.channels, key=lambda c: c.created_at, reverse=False)
            for i, chan in enumerate(sorted_channels):
                if chan.position != i:
                    print('moving', chan.name, 'to', i)
                    await chan.edit(position=i)
            for existing_channel in sorted_channels:
                if len(closed_category.channels) > 10:
                    print(f"deleting {existing_channel.name}")
                    await existing_channel.delete()
                    closed_category = discord.utils.get(ctx.guild.categories, id=1170665554516922460)
                    print(f"{len(closed_category.channels)} channels remain")
        else:
            await ctx.reply('This command can only be used in an interview channel.')
    except Exception as err:
        traceback.print_exception(type(err), err, err.__traceback__)
        trace = traceback.format_exception(type(err), err, err.__traceback__)
        await ctx.reply('\n'.join(trace))

@bot.command(help='sends the specified server rule(s)', name='rule')
async def _rule(ctx, *rules: str):
    rules = [i for i in rules if i.isnumeric() and int(i) > 0]
    if len(rules) > 0:
        embeds = []
        for rule in rules:
            try:
                embed = discord.Embed(title=f'Rule #{rule}', description=server_rules[int(rule)-1], colour=discord.Colour.og_blurple())
                embeds.append(embed)
            except IndexError:
                pass

        if len(embeds) == 0:
            await ctx.send(f"Read the server rules at https://discord.com/channels/1161898338988347452/1167358841638354954")
        elif len(embeds) <= 10:
            await ctx.send(embeds=embeds)
        else:
            split_list = [embeds[i:i + 10] for i in range(0, len(embeds), 10)]  # splits the list into every 10 units
            # due to discord's ten embed per message limit
            for r in split_list:
                await ctx.send(embeds=r)
    else:
        await ctx.send(f"Read the server rules at https://discord.com/channels/1161898338988347452/1167358841638354954")

@bot.command()
@commands.is_owner()
async def sync(ctx):
    await ctx.typing()
    await bot.tree.sync(guild=None)  # global sync
    await ctx.send('Synced CommandTree!')


async def main():
    async with bot:
        await bot.load_extension("cogs.rb_commands")
        await bot.start(TOKEN)


asyncio.run(main())