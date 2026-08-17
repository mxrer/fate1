import discord
from discord.ext import commands
from discord.utils import get
import os
from datetime import timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=",", intents=intents)

OWNER_ID = 1477802548189593864
AUTO_ROLE_NAME = "1538730480466141335"

whitelists = {}
snapped = {}
os.makedirs("whitelists", exist_ok=True)
os.makedirs("autoroles", exist_ok=True)

def load_whitelist(guild_id):
    if guild_id in whitelists:
        return whitelists[guild_id]
    path = f"whitelists/{guild_id}.txt"
    s = set()
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line.isdigit():
                    s.add(int(line))
    whitelists[guild_id] = s
    return s

def save_whitelist(guild_id):
    s = whitelists.get(guild_id, set())
    path = f"whitelists/{guild_id}.txt"
    with open(path, "w") as f:
        for uid in s:
            f.write(str(uid) + "\n")

def is_whitelisted(guild_id, user_id):
    return user_id in load_whitelist(guild_id)

def load_autorole(guild_id):
    path = f"autoroles/{guild_id}.txt"
    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return None

def save_autorole(guild_id, role_id):
    path = f"autoroles/{guild_id}.txt"
    with open(path, "w") as f:
        f.write(str(role_id))

def parse_duration(s):
    s = s.lower()
    if s.endswith('d'):
        try:
            v = int(s[:-1])
            return timedelta(days=v)
        except:
            return None
    if s.endswith('w'):
        try:
            v = int(s[:-1])
            return timedelta(weeks=v)
        except:
            return None
    try:
        v = int(s)
        return timedelta(minutes=v)
    except:
        return None

@bot.event
async def on_ready():
    print(f"Bot started as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_member_join(member):
    role_id = load_autorole(member.guild.id)
    role = None
    if role_id:
        role = member.guild.get_role(role_id)
    if not role:
        role = get(member.guild.roles, name=AUTO_ROLE_NAME)
    if role:
        await member.add_roles(role)

@bot.event
async def on_member_unban(guild, user):
    s = snapped.get(guild.id)
    if s and user.id in s:
        try:
            await guild.ban(user, reason="re-snapped")
        except:
            pass

@bot.command()
async def wladd(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("No.")
    wl = load_whitelist(ctx.guild.id)
    if member.id in wl:
        wl.remove(member.id)
        await ctx.send(f"{member.mention} removed from whitelist.")
    else:
        wl.add(member.id)
        await ctx.send(f"{member.mention} added to whitelist.")
    save_whitelist(ctx.guild.id)

@bot.command()
async def wllist(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("No.")
    wl = load_whitelist(ctx.guild.id)
    if not wl:
        await ctx.send("Whitelist is empty.")
    else:
        users = [f"<@{uid}>" for uid in wl]
        await ctx.send("Whitelist:\n" + "\n".join(users))

@bot.command()
async def purge(ctx, amount: int):
    if not ctx.author.guild_permissions.manage_messages:
        return await ctx.send("No.")
    if amount < 1 or amount > 1000:
        return await ctx.send("No.")
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Purged {amount} messages.", delete_after=5)

@bot.command()
async def autorole(ctx, role_id: int):
    if not ctx.author.guild_permissions.manage_guild:
        return await ctx.send("No.")
    role = ctx.guild.get_role(role_id)
    if not role:
        return await ctx.send("No.")
    save_autorole(ctx.guild.id, role.id)
    await ctx.send(f"Autorole set to {role.name}")

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    member_count = guild.member_count
    channel_count = len(guild.channels)
    created_at = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
    boost_level = guild.premium_tier
    boost_count = guild.premium_subscription_count or 0
    await ctx.send(f"Server: {guild.name}\nMembers: {member_count}\nChannels: {channel_count}\nCreated: {created_at}\nBoost Level: {boost_level}\nBoosts: {boost_count}")

@bot.command()
async def userinfo(ctx, member: discord.Member):
    roles = ", ".join([r.name for r in member.roles if r.name != "@everyone"]) or "None"
    joined = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown"
    created = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
    timeout = "Yes" if member.is_timed_out() else "No"
    await ctx.send(f"User: {member}\nID: {member.id}\nRoles: {roles}\nJoined: {joined}\nCreated: {created}\nTimed out: {timeout}")

@bot.command()
async def role(ctx, action, member: discord.Member, *, role_name):
    if not ctx.author.guild_permissions.manage_roles:
        return await ctx.send("No.")
    role = get(ctx.guild.roles, name=role_name)
    if not role:
        return await ctx.send("Role not found.")
    if action.lower() == "add":
        await member.add_roles(role)
        await ctx.send(f"{role.name} added to {member.mention}.")
    elif action.lower() == "remove":
        await member.remove_roles(role)
        await ctx.send(f"{role.name} removed from {member.mention}.")
    else:
        await ctx.send("Use add or remove.")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.banner:
        await ctx.send(member.banner.url)
    else:
        await ctx.send("No banner")

# FIXED — zwei getrennte Commands statt Doppel-Decorator
@bot.command(name='sav')
async def sav(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("No icon")

@bot.command(name='sab')
async def sab(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("No icon")

@bot.command()
async def lock(ctx):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Channel locked.")

@bot.command()
async def unlock(ctx):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Channel unlocked.")

@bot.command()
async def timeout(ctx, member: discord.Member, duration: str):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    delta = parse_duration(duration)
    if not delta:
        return await ctx.send("No.")
    await member.timeout(delta, reason=None)
    await ctx.send(f"{member.mention} timed out.")

@bot.command()
async def untimeout(ctx, member: discord.Member):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await member.timeout(None, reason=None)
    await ctx.send(f"{member.mention} untimed out.")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} kicked.")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} banned.")

@bot.command()
async def unban(ctx, user: discord.User):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    try:
        await ctx.guild.unban(user)
        await ctx.send(f"{user} unbanned.")
    except:
        await ctx.send("Unban failed.")

@bot.command()
async def unbanall(ctx):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    bans = await ctx.guild.bans()
    for entry in bans:
        await ctx.guild.unban(entry.user)
    await ctx.send("All users unbanned.")

@bot.command()
async def snap(ctx, member: discord.Member):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    await ctx.guild.ban(member, reason="snapped")
    s = snapped.setdefault(ctx.guild.id, set())
    s.add(member.id)
    await ctx.send("snapped.")

@bot.command()
async def unsnap(ctx, user: discord.User):
    if not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")
    s = snapped.get(ctx.guild.id, set())
    if user.id in s:
        s.remove(user.id)
    try:
        await ctx.guild.unban(user)
    except:
        pass
    await ctx.send("unsnapped.")

# TOKEN entfernt — Railway nutzt Environment Variable
bot.run(os.getenv("TOKEN"))
