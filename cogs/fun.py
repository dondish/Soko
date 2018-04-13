import discord
from discord.ext import commands
import random
import aiohttp
import asyncio

NEW_SESSION_URL = "http://api-en4.akinator.com/ws/new_session?partner=1"
ANSWER_URL = "http://api-en4.akinator.com/ws/answer?callback=&session={}&signature={}&step={}&answer={}"
GET_GUESS_URL = "http://api-en4.akinator.com/ws/list?callback=&session={}&signature={}&step={}"
CHOICE_URL = "http://api-en4.akinator.com/ws/choice?callback=&session={}&signature={}&step={}&element={}"
EXCLUSION_URL = "http://api-en4.akinator.com/ws/exclusion?callback=&session={}&signature={}&step={}&forward_answer={}"


class Guess:
    def __init__(self, js):
        self.element = js
        self.id = js["id"]
        self.name = js["name"]
        self.desc = js["description"]
        self.ranking = js["ranking"]
        self.imgpath = js["absolute_picture_path"]

    def embed(self):
        e = discord.Embed(title=self.name, description=self.desc)
        e.set_image(url=self.imgpath)
        e.set_footer(text=f"Ranking: {self.ranking} - Id: {self.id}")
        return e


class Step:
    def __init__(self, ctx, js):
        self.ctx = ctx
        self.identification = js["parameters"]["identification"]
        self.session = self.identification["session"]
        self.signature = self.identification["signature"]
        self.g = None
        self.question = js["parameters"]["step_information"]["question"]
        self.answers = js["parameters"]["step_information"]["answers"]
        self.completion = js["completion"]
        self.progression = float(js["parameters"]["step_information"]["progression"])
        self.step = js["parameters"]["step_information"]["step"]

    def update(self, js):
        self.question = js["parameters"]["question"]
        self.answers = js["parameters"]["answers"]
        self.completion = js["completion"]
        self.progression = float(js["parameters"]["progression"])
        self.step = js["parameters"]["step"]

    def askcheck(self, m):
        return m.content.lower() in ["yes", "no", "don't know", "probably", "probably not"] and m.author == self.ctx.author and m.channel == self.ctx.channel

    def guesscheck(self, m):
        return m.content.lower() in ["yes", "no"] and m.author == self.ctx.author and m.channel == self.ctx.channel

    async def answer(self, aid):
        if self.progression > 90:
            await self.guess(aid)
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(ANSWER_URL.format(self.session, self.signature, self.step, aid),
                                       allow_redirects=False) as response:
                    js = await response.json()
                    if not js["completion"] == "OK":
                        return
                    self.update(js)
                    await self.ask()

    async def ask(self):
        async with self.ctx.channel.typing():
            s = "**"+self.ctx.author.display_name + ": Question " + str(int(self.step)+1) +": " + self.question+"**\n"
            index = 0
            for answer in self.answers:
                s += (f"{str(index+1)}. {answer['answer']}\n")
                index += 1
            s += "Progression: " + str(self.progression) + "%"
            await self.ctx.send(s)
        m = await self.ctx.bot.wait_for("message", check=self.askcheck, timeout=20)
        inp = ["yes", "no", "don't know", "probably", "probably not"].index(m.content.lower())
        await self.answer(inp)

    async def guess(self, aid):
        async with aiohttp.ClientSession() as session:
            async with session.get(GET_GUESS_URL.format(self.session, self.signature, self.step),
                                   allow_redirects=False) as response:
                js = await response.json()
                self.g = Guess(js["parameters"]["elements"][0]["element"])
                await self.ctx.send("Is this your character?\n[yes/no]\n", embed=self.g.embed())
                m = await self.ctx.bot.wait_for("message", check=self.guesscheck, timeout=20)
                inp = str(["yes", "no"].index(m.content.lower()))
                await self.answerguess(inp, aid)

    async def answerguess(self, aid, prev):
        if aid == "0":
            async with aiohttp.ClientSession() as session:
                async with session.get(CHOICE_URL.format(self.session, self.signature, self.step, self.g.element),
                                       allow_redirects=False) as response:
                    await self.ctx.send("Great! Guessed right one more time.\n<http://akinator.com>")
        elif aid == "1":
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCLUSION_URL.format(self.session, self.signature, self.step, "1"),
                                       allow_redirects=False) as response:
                    self.progression -= 30
                    await self.answer(prev)


async def start(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get(NEW_SESSION_URL, allow_redirects=False) as response:
            js = await response.json()
            if not js["completion"] == "OK":
                return
            step = Step(ctx, js)
            await step.ask()


class Fun_Error(commands.UserInputError):
    pass


class Fun:
    """Commands for fun! Jokes and other stupid things."""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)

    async def __error(self, ctx, error):
        if not isinstance(error, commands.UserInputError) and not isinstance(error, TimeoutError):
            raise error
        elif isinstance(error, TimeoutError):
            return
        try:
            await ctx.send(error)
        except discord.Forbidden:
            pass  # /shrug

    @commands.command(no_pm=True)
    async def say(self, ctx, *, query: str):
        """Echoes what you said."""
        if query == "":
            await ctx.send("Message cannot be empty!")
        await ctx.send(query)

    @commands.command(no_pm=True)
    async def stupid(self, ctx, member: discord.Member):
        """Blame stupid people"""
        await ctx.send(f"{member.display_name} is stupid! omg he/she is a huge idiot. 🤦‍")

    @commands.command(no_pm=True)
    async def ban(self, ctx, member: discord.Member):
        """Ban whoever you dislike."""
        await ctx.send(f"{member.display_name}, I dismiss you from this server! bye bye!👋")

    @commands.command(no_pm=True)
    async def disappointment(self, ctx, member: discord.Member):
        """He is definitely a disappointment."""
        await ctx.send(f"{member.display_name} is a disgrace to this server!")

    @commands.command(no_pm=True)
    async def praise(self, ctx, member: discord.Member):
        """Let the world know who's the best!"""
        await ctx.send(f"I love you {member.display_name}! You are an angel!")

    @commands.command(no_pm=True)
    async def gossip(self, ctx, member: discord.Member):
        """Gossip the bot noticed throughout the server. Shhh."""
        assert isinstance(ctx, commands.Context)
        a = ctx.guild.members.copy()
        a.remove(member)
        another_m = random.choice(a)
        l = [f"I heard {member.mention} has a big crush on {another_m.mention}!",
             f"I heard from an unknown source that {another_m.mention} is cheating on {member.mention}!",
             f"{another_m.mention} hates {member.mention} but pretends he likes him when {member.mention} is around!",
             f"{another_m.mention} told me {member.mention} has super cancer aids.",
             f"{member.mention} thinks about {another_m.mention} every night!",
             f"If you thought {member.mention} is stupid, you never knew {another_m.mention}"]
        await ctx.send(random.choice(l))

    @commands.command(no_pm=True)
    async def guess(self, ctx):
        """Bot guesses your number from 0 to 100!"""
        await ctx.send("Imma guess your number!\nfor each question answer higher, lower or equal!")
        high = 100
        low = 0
        num = random.randint(low, high)
        while True:
            await ctx.send(f"{ctx.message.author.mention} {num}?")
            try:
                mess = await self.bot.wait_for("message", check=lambda
                    m: m.author == ctx.message.author and m.channel == ctx.message.channel and m.content in ["higher",
                                                                                                             "lower",
                                                                                                             "equal"],
                                               timeout=20.)
            except TimeoutError or asyncio.TimeoutError:
                raise Fun_Error(ctx.send("Time's up."))
            c = mess.content
            if c == "equal":
                await ctx.send(f"{ctx.message.author.mention} I won! like I always do of course. your number is {num}!")
                return
            elif c == "higher":
                low = num + 1

            else:
                high = num - 1
            if high == low:
                await ctx.send(f"{ctx.message.author.mention} there are no other options, your number is {high}!")
                return
            num = random.randint(low, high)

    @commands.command(no_pm=True)
    async def meme(self, ctx):
        """Random meme supplied by kanliam."""
        memes = {"stop it, get some help\n": "https://www.youtube.com/watch?v=AzLcDo4Wpbs\n",
                 "hello darkness my old friend\n": "https://www.youtube.com/watch?v=4zLfCnGVeL4\n",
                 "these nuts\n": "https://www.youtube.com/watch?v=8tOsQv-rrEE\n",
                 "goteem\n": "https://www.youtube.com/watch?v=8tOsQv-rrEE\n",
                 "my name is jeff\n": "https://www.youtube.com/watch?v=AfIOBLr1NDU\n",
                 "nine plus ten   twenty one\n": "https://www.youtube.com/watch?v=OLBOn0Whhyc\n",
                 "smoke weed everyday\n": "https://youtu.be/wWSAI9d3Vxk?t=38s\n",
                 "i am the one\n": "https://www.youtube.com/watch?v=w4oHBoeuZ10\n",
                 "the screaming goat/sheep\n": "https://www.youtube.com/watch?v=SIaFtAKnqBU\n",
                 "why you always lying\n": "https://www.youtube.com/watch?v=WcWM_1hBu_c\n",
                 "i love big butts\n": "https://www.youtube.com/watch?v=reTx5sqvVJ4\n",
                 "you dumbass motherfucker\n": "https://www.youtube.com/watch?v=kvOd9rkNlI4\n",
                 "never gonna give you up\n": "https://www.youtube.com/watch?v=dQw4w9WgXcQ\n",
                 "nooooooooooo god please no nooooooooooooooooo\n": "https://www.youtube.com/watch?v=umDr0mPuyQc\n",
                 "pen pineapple apple pen\n": "https://youtu.be/Ct6BUPvE2sM?t=29s\n",
                 "here comes the boom\n": "https://www.youtube.com/watch?v=nqWZqQXk_Ao\n",
                 "get the fuck out of my room im playing minecraft\n": "https://youtu.be/4XY731ZYR0Y?t=11s\n",
                 "here's johny\n": "https://www.youtube.com/watch?v=fLEdpDpoTTA\n",
                 "when you try your best and you dont succeed\n": "https://www.youtube.com/watch?v=4qgrN6-JsOU\n",
                 "that moment he know he fucked up\n": "https://www.youtube.com/watch?v=j7DVh9IPHqM\n",
                 "who can say where the road goes\n": "https://www.youtube.com/watch?v=upkYQqbrjSc\n",
                 "Windows xp startup\n": "https://www.youtube.com/watch?v=7nQ2oiVqKHw\n",
                 "windows xp shutdown\n": "https://www.youtube.com/watch?v=7nQ2oiVqKHw\n",
                 "illuminati confirmed\n": "https://www.youtube.com/watch?v=sahAbxq8WPw\n",
                 "i have crippling depression\n": "https://youtu.be/SLEdsI731J4?t=2s\n",
                 "I Have Osteoporosis\n": "https://youtu.be/k8c9_4TAiXo?t=2s\n",
                 "BRUH\n": "https://www.youtube.com/watch?v=NzishIREebw\n",
                 "HIYAA Cracked kid\n": "https://www.youtube.com/watch?v=wF1l_KtIUoA\n",
                 "China Donald Trump\n": "https://www.youtube.com/watch?v=RDrfE9I8_hs\n",
                 "My father gave me a small loan of a million dollars\n": "https://www.youtube.com/watch?v=BuXlf7oTfLE\n",
                 "Error\n": "https://www.youtube.com/watch?v=mKkLjJHwRec\n",
                 "Yeah Boiiiiii\n": "https://www.youtube.com/watch?v=UdiGsDktSBA\n",
                 "Oh shit\n": "https://youtu.be/6AOmH5pNEdk?t=4s\n",
                 "This is sparta\n": "https://www.youtube.com/watch?v=LEXj9JrSwE0\n",
                 "we are number one\n": "https://www.youtube.com/watch?v=SYAMjPcUP7E\n",
                 "Look at this dude ahhaahha no no non o haahahahahahah\n": "https://www.youtube.com/watch?v=3cdk2Fs2CP0\n",
                 "sad\n": "https://www.youtube.com/watch?v=7ODcC5z6Ca0\n",
                 "WOW\n": "https://www.youtube.com/watch?v=LYkg-B6f5iA\n",
                 "2 hours later spongebob\n": "https://www.youtube.com/watch?v=-vCOLA75mAk\n",
                 "really nigga?\n": "https://www.youtube.com/watch?v=rfsqEO-WQHc\n",
                 "Oh baby a triple oh yeah\n": "https://www.youtube.com/watch?v=XlLbsTP0C_U\n",
                 "denied\n": "https://www.youtube.com/watch?v=XlLbsTP0C_U\n",
                 "mom get the camera\n": "https://www.youtube.com/watch?v=8fsH1Rp_5bk\n",
                 "GTA V Wasted/Busted\n": "https://www.youtube.com/watch?v=K3kFQHKE0LA\n",
                 "Do you honestly think you're funny\n": "https://www.youtube.com/watch?v=ICGoPyAp0Hw\n",
                 "shut your fking mouth\n": "https://www.youtube.com/watch?v=AqcyQItOL9g\n",
                 "gotcha bitch\n": "https://www.youtube.com/watch?v=H7O17O1t-9g\n",
                 "suspense maftia\n": "https://www.youtube.com/watch?v=QEjxSLTe5_M\n",
                 "why u hef to be med\n": "https://www.youtube.com/watch?v=XnQ-5uFuDtc\n",
                 "Hi okey\n": "https://www.youtube.com/watch?v=Obgnr9pc820\n"}
        meme = random.choice(list(memes.keys()))
        embed = discord.Embed()
        embed.title(meme)
        embed.url = memes[meme]
        await ctx.send(embed)

    @commands.command(no_pm=True)
    async def rps(self, ctx, stance: str):
        """Play Rock Paper Scissors with the bot!"""
        win_sits = [("R", "S"), ("P", "R"), ("S", "P")]
        choices = ["R", "S", "P"]
        trans = {"R": "rock", "S": "scissors", "P": "paper"}
        choice = random.choice(choices)
        inv = {v: k for k, v in trans.items()}
        try:
            echoice = inv[stance]
        except KeyError:
            raise Fun_Error("Please use %rps [rock|paper|scissors]")
        if (echoice, choice) in win_sits:
            await ctx.send(f"You did {trans[echoice]} while I did {trans[choice]}, I lose 😔")
        elif (choice, echoice) in win_sits:
            await ctx.send(f"I did {trans[choice]} while you did {trans[echoice]}, I win 😁")

        else:
            await ctx.send(f"We both did {trans[choice]}, draw 😐")

    @commands.command(no_pm=True)
    async def akinator(self, ctx):
        """Play Akinator, http://en.akinator.com"""
        await start(ctx)


def setup(bot):
    bot.add_cog(Fun(bot))
