from config import Bot
import discord


def setup(bot):
    """
    Setup here bot events of your choice.
    """
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, TimeoutError):
            return
        print(error)

    @bot.event
    async def on_ready():
        print('Logged in as:\n{0} (ID: {0.id})'.format(bot.user))
        bot.load_extension('cogs.music')
        bot.load_extension('cogs.utility')
        bot.load_extension('cogs.general')
        bot.load_extension('cogs.fun')
        await bot.change_presence(activity=discord.Game(Bot.PREFIX+"help"))