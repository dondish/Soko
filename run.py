#!/root/Downloads/ENV/bin/python3.6
import inspect
import asyncio
import itertools
from discord.ext import commands
from events import setup
from config import Bot


def modup(ctx):
    return ctx.message.channel.permissions_for(ctx.message.author).manage_messages


Paginator = commands.Paginator; Command = commands.Command


class Format(commands.HelpFormatter):
    @asyncio.coroutine
    def format(self):
        self._paginator = Paginator()

        # we need a padding of ~80 or so

        description = self.command.description if not self.is_cog() else inspect.getdoc(self.command)

        if description:
            # <description> portion
            self._paginator.add_line(description, empty=True)

        if isinstance(self.command, Command):
            # <signature portion>
            signature = self.get_command_signature()
            self._paginator.add_line(signature, empty=True)

            # <long doc> section
            if self.command.help:
                self._paginator.add_line(self.command.help, empty=True)

            # end it here if it's just a regular command
            if not self.has_subcommands():
                self._paginator.close_page()
                return self._paginator.pages

        max_width = self.max_name_size

        def category(tup):
            cog = tup[1].cog_name
            # we insert the zero width space there to give it approximate
            # last place sorting position.
            return cog + ':' if cog is not None else '\u200bNo Category:'

        filtered = yield from self.filter_command_list()
        if self.is_bot():
            data = sorted(filtered, key=category)
            self._paginator.add_line("Modules:")
            for category, commands in itertools.groupby(data, key=category):
                # there simply is no prettier way of doing this.
                if category == '\u200bNo Category:':
                    continue
                self._paginator.add_line("\t"+category[:-1])
            self._paginator.add_line()
            self._paginator.add_line("Use " + Bot.PREFIX +"help <module> to find more about each module!\nHave fun!")
        else:
            filtered = sorted(filtered)
            if filtered:
                self._paginator.add_line('Commands:')
                self._add_subcommands_to_page(max_width, filtered)
            self._paginator.add_line()
            ending_note = self.get_ending_note()
            self._paginator.add_line(ending_note)

        # add the ending note
        return self._paginator.pages


bot = commands.Bot(command_prefix=commands.when_mentioned_or(Bot.PREFIX), description=Bot.DESCRIPTION, max_messages=10000, formatter=Format(False, False, 80), shard_count=1, owner_id=Bot.OWNER_ID)


@bot.command(no_pm=True, hidden=True)
@commands.check(modup)
async def load_cog(ctx, *, name:str):
    bot.load_extension(name)


@bot.command(no_pm=True, hidden=True)
@commands.check(modup)
async def unload_cog(ctx, *, name:str):
    bot.unload_extension(name)


@bot.command(no_pm=True, hidden=True)
@commands.check(modup)
async def reload_cog(ctx, *, name:str):
    bot.unload_extension(name)
    bot.load_extension(name)


if __name__ == "__main__":
    setup(bot)
    bot.run(Bot.TOKEN)
