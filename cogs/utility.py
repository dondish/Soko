import discord
from discord.ext import commands
import random
import re
import asyncio
from config import Bot


class Utility_Error(commands.UserInputError):
    pass


class Utility:
    """Utility is for people who want easy tasks to be done!"""
    def __init__(self, bot):
        assert isinstance(bot, commands.Bot)
        self.bot = bot

    async def __error(self, ctx, error):
        if not isinstance(error, commands.UserInputError) and not isinstance(error, TimeoutError):
            raise error
        elif isinstance(error, TimeoutError):
            return
        try:
            await ctx.send(error)
        except discord.Forbidden:
            pass  # /shrug

    lh = "Calculates Simple Python Math Queries\nArithmetic Operators:\n" \
         "+ : Addition\n" \
         "- : Subtraction\n" \
         "* : Multiplication\n" \
         "/ : Division\n" \
         "// : Floor Division (Integer Division)\n" \
         "% : Modulus\n" \
         "** : Exponent\n" \
         "Comparsion Operators:\n" \
         "== : Equals\n" \
         "!= : Not Equal\n" \
         "> or < : Much Greater / Smaller\n" \
         ">= or <= Great or Equal / Small or Equal\n" \
         "; : To support assignment"
    @commands.command(help=lh)
    async def math(self, ctx, *, query:str):
        """Calculates simple math queries."""
        p = re.compile("((\d)|(\W)|(and)|(or)|(is)|(not)(in))+")
        if re.fullmatch(p, query):
            await ctx.send(eval(query))
        else:
            raise Utility_Error("Incorrect use of math. Use " + Bot.PREFIX + "help math for help.")

    lh2 = "Generates a random integer\n" \
         "(Optional) add 2 numbers which are the range of the numbers"
    @commands.command(no_pm=True, help=lh2)
    async def random(self, ctx):
        """Random number generator."""
        if len(ctx.message.content.split()) == 3:
            await ctx.send(random.randint(int(ctx.message.content.split()[1]), int(ctx.message.content.split()[2])))
        else:
            await ctx.send(random.randint(-10000000, 10000000))

    @commands.command(no_pm=True)
    async def roll(self, ctx):
        """Roll the dice."""
        await ctx.send(random.randint(1, 6))

    @commands.command(no_pm=True)
    async def choose(self, ctx, *choices):
        """Randomly chooses element of a list"""
        try:
            await ctx.send(random.choice(choices))
        except IndexError:
            raise Utility_Error("Correct usage: " + Bot.PREFIX +  "choose element1 element2 ...")

    async def reminder_protocol(self, ctx, time, message):
        await asyncio.sleep(time*60)
        await ctx.send(f"Reminder for {ctx.author.mention}: {message}")

    @commands.command(no_pm=True)
    async def remind(self, ctx, *, message:str):
        """Set a reminder after x minutes."""
        time = int(message.split()[0])
        reminder = ' '.join(message.split()[1:])
        self.bot.loop.create_task(self.reminder_protocol(ctx, time, reminder))
        await ctx.send(f"Successfully set a reminder for {ctx.author.mention} after {time} minutes.")

def setup(bot):
    bot.add_cog(Utility(bot))