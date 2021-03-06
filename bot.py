import discord 
from discord.ext import commands
import time
import os
import inspect
import json
from contextlib import redirect_stdout
import io
import textwrap
import traceback
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient


client = AsyncIOMotorClient(os.environ.get("MONGOURL"))
db = client.discordbot2001


async def guildpre(bot, message):
    '''Get the prefix for required guild'''
    f = await bot.db.config.find_one({"gid" : message.guild.id})
    if f is None:
       	return "e."
    else:
        f = f['prefix']
        return f

bot = commands.Bot(command_prefix=guildpre, description="An easy to use discord bot")
bot.load_extension("cogs.fun")
bot.load_extension("cogs.utility")
bot.load_extension("cogs.mod")
bot.load_extension("cogs.Music")
bot._last_result = None
bot.session = aiohttp.ClientSession(loop=bot.loop)
bot.db = db






def cleanup_code(content):
    '''Automatically removes code blocks from the code.'''
    # remove ```py\n```
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])

    return content.strip('` \n')
     


def dev_check(id):
    with open('data/devs.json') as f:
        devs = json.load(f)
        if id in devs:
            return True
        return False


@bot.event
async def on_ready():
	print('Logged in as '+ bot.user.name)
	print(bot.user.id)
	print('------')
	await bot.change_presence(status = os.environ.get('STATUS'), activity=discord.Game(name=os.environ.get('ACTIVITY')))




@bot.command(name='eval')
async def _eval(ctx, *, body):
    """Evaluates python code"""
    if not dev_check(ctx.author.id):
        return await ctx.send("You cannot use this because you are not a developer.")
    env = {
        'ctx': ctx,
        'channel': ctx.channel,
        'author': ctx.author,
        'guild': ctx.guild,
        'message': ctx.message,
        '_': bot._last_result,
        'source': inspect.getsource
    }

    env.update(globals())

    body = cleanup_code(body)
    stdout = io.StringIO()
    err = out = None

    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    def paginate(text: str):
        '''Simple generator that paginates text.'''
        last = 0
        pages = []
        for curr in range(0, len(text)):
            if curr % 1980 == 0:
                pages.append(text[last:curr])
                last = curr
                appd_index = curr
        if appd_index != len(text) - 1:
            pages.append(text[last:curr])
        return list(filter(lambda a: a != '', pages))

    try:
        exec(to_compile, env)
    except Exception as e:
        err = await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')
        return await ctx.message.add_reaction('\u2049')

    func = env['func']
    try:
        with redirect_stdout(stdout):
            ret = await func()
    except Exception as e:
        value = stdout.getvalue()
        err = await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
    else:
        value = stdout.getvalue()
        if ret is None:
            if value:
                try:

                    out = await ctx.send(f'```py\n{value}\n```')
                except:
                    paginated_text = paginate(value)
                    for page in paginated_text:
                        if page == paginated_text[-1]:
                            out = await ctx.send(f'```py\n{page}\n```')
                            break
                        await ctx.send(f'```py\n{page}\n```')
        else:
            bot._last_result = ret
            try:
                out = await ctx.send(f'```py\n{value}{ret}\n```')
            except:
                paginated_text = paginate(f"{value}{ret}")
                for page in paginated_text:
                    if page == paginated_text[-1]:
                        out = await ctx.send(f'```py\n{page}\n```')
                        break
                    await ctx.send(f'```py\n{page}\n```')

    if out:
        await ctx.message.add_reaction('\u2705')  # tick
    elif err:
        await ctx.message.add_reaction('\u2049')  # x
    else:
        await ctx.message.add_reaction('\u2705')
	
@bot.command()
async def ping(ctx):
    '''Ping the bot'''
    t1 = ctx.message.created_at
    m = await ctx.send('**Pong!**')
    time = (m.created_at - t1).total_seconds() * 1000
    await m.edit(content='**Pong!  Took: {}ms**'.format(int(time)))

	
	
	
	

bot.run(os.environ.get("TOKEN"))
