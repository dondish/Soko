import discord
import sys
from discord.ext import commands

from config import Bot


async def modup(ctx):
    return ctx.channel.permissions_for(ctx.message.author).manage_messages


class General:
    """General Management Commands."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def is_owner(ctx):
        return ctx.message.author.id == Bot.OWNER_ID

    @commands.command(no_pm=True)
    async def info(self, ctx):
        """Shows bot info"""
        embed_info = discord.Embed(
            color=0x1abc9c
        ).set_author(name=str(ctx.bot.user), icon_url=ctx.bot.user.avatar_url) \
            .add_field(name="Creator", value=Bot.OWNER_NAME) \
            .add_field(name="Version", value=Bot.VERSION) \
            .add_field(name="Discord Library Version", value=discord.__version__) \
            .add_field(name="Libraries Used", value="\n".join(sys.modules.keys()))
        await ctx.message.channel.send(embed=embed_info)

    @commands.command(no_pm=True)
    async def ping(self, ctx):
        """Shows bot's latency"""
        await ctx.send(str(int(self.bot.latency*1000))+"ms")

    @commands.command(no_pm=True)
    @commands.has_permissions(manage_guild=True)
    async def purge(self, ctx, *, limit: int):
        """<Admin> Purge x messages not (including this command)"""
        if limit < 100:
            await ctx.message.channel.purge(limit=limit, before=ctx.message)

    @commands.command(no_pm=True)
    async def serverinfo(self, ctx):
        """General info about the server."""
        embed = discord.Embed()
        guild = ctx.message.guild
        embed.set_author(name=str(guild), icon_url=guild.icon_url)
        embed.add_field(name="Owner:", value=str(guild.owner))
        embed.add_field(name="Created at:", value=str(guild.created_at.strftime("%d-%m-%Y at %H:%M")))
        embed.add_field(name="Member Count:", value=str(guild.member_count))
        embed.add_field(name="Role Count:", value=str(len(guild.roles)))
        embed.add_field(name="Channel Count:", value=str(len(guild.channels)))
        embed.add_field(name="TextChannel Count:", value=str(len(guild.text_channels)))
        embed.add_field(name="VoiceChannel Count:", value=str(len(guild.voice_channels)))
        embed.add_field(name="Catergory Count:", value=str(len(guild.categories)))
        await ctx.message.channel.send(embed=embed)

    @commands.check(is_owner)
    async def shutdown(self, ctx):
        """Simple shutdown command"""
        exit()


def setup(bot):
    bot.add_cog(General(bot))