import discord
from discord.ext import commands
from discord.utils import get
import os
from datetime import timedelta, datetime

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

# =========================
# OWNER ALWAYS ALLOWED
# =========================
def wlcheck(ctx):
    if ctx.author.id == OWNER_ID:
        return True
    return is_whitelisted(ctx.guild.id, ctx.author.id)

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
@commands.check(wlcheck)
async def wladd(ctx, member: discord.Member):
    wl = load_whitelist(ctx.guild.id)
    if member.id in wl:
        wl.remove(member.id)
        await ctx.send(f"{member.mention} removed from whitelist.")
    else:
        wl.add(member.id)
        await ctx.send(f"{member.mention} added to whitelist.")
    save_whitelist(ctx.guild.id)

@bot.command()
@commands.check(wlcheck)
async def wllist(ctx):
    wl = load_whitelist(ctx.guild.id)
    if not wl:
        await ctx.send("Whitelist is empty.")
    else:
        users = [f"<@{uid}>" for uid in wl]
        await ctx.send("Whitelist:\n" + "\n".join(users))

@bot.command()
@commands.check(wlcheck)
async def purge(ctx, amount: int):
    if amount < 1 or amount > 1000:
        return await ctx.send("No.")
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Purged {amount} messages.", delete_after=5)

@bot.command()
@commands.check(wlcheck)
async def autorole(ctx, role_id: int):
    role = ctx.guild.get_role(role_id)
    if not role:
        return await ctx.send("No.")
    save_autorole(ctx.guild.id, role.id)
    await ctx.send(f"Autorole set to {role.name}")

@bot.command()
@commands.check(wlcheck)
async def serverinfo(ctx):
    guild = ctx.guild
    member_count = guild.member_count
    channel_count = len(guild.channels)
    created_at = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
    boost_level = guild.premium_tier
    boost_count = guild.premium_subscription_count or 0
    await ctx.send(f"Server: {guild.name}\nMembers: {member_count}\nChannels: {channel_count}\nCreated: {created_at}\nBoost Level: {boost_level}\nBoosts: {boost_count}")

@bot.command()
@commands.check(wlcheck)
async def userinfo(ctx, member: discord.Member):
    roles = ", ".join([r.name for r in member.roles if r.name != "@everyone"]) or "None"
    joined = member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown"
    created = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
    timeout = "Yes" if member.is_timed_out() else "No"
    await ctx.send(f"User: {member}\nID: {member.id}\nRoles: {roles}\nJoined: {joined}\nCreated: {created}\nTimed out: {timeout}")

@bot.command()
@commands.check(wlcheck)
async def role(ctx, action, member: discord.Member, *, role_name):
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
@commands.check(wlcheck)
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

@bot.command()
@commands.check(wlcheck)
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.banner:
        await ctx.send(member.banner.url)
    else:
        await ctx.send("No banner")

@bot.command(name='sav')
@commands.check(wlcheck)
async def sav(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("No icon")

@bot.command(name='sab')
@commands.check(wlcheck)
async def sab(ctx):
    if ctx.guild.icon:
        await ctx.send(ctx.guild.icon.url)
    else:
        await ctx.send("No icon")

@bot.command()
@commands.check(wlcheck)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Channel locked.")

@bot.command()
@commands.check(wlcheck)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Channel unlocked.")

@bot.command()
@commands.check(wlcheck)
async def timeout(ctx, member: discord.Member, duration: str):
    delta = parse_duration(duration)
    if not delta:
        return await ctx.send("No.")
    await member.timeout(delta, reason=None)
    await ctx.send(f"{member.mention} timed out.")

@bot.command()
@commands.check(wlcheck)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=None)
    await ctx.send(f"{member.mention} untimed out.")

@bot.command()
@commands.check(wlcheck)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} kicked.")

@bot.command()
@commands.check(wlcheck)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} banned.")

@bot.command()
@commands.check(wlcheck)
async def unban(ctx, user: discord.User):
    try:
        await ctx.guild.unban(user)
        await ctx.send(f"{user} unbanned.")
    except:
        await ctx.send("Unban failed.")

@bot.command()
@commands.check(wlcheck)
async def unbanall(ctx):
    bans = await ctx.guild.bans()
    for entry in bans:
        await ctx.guild.unban(entry.user)
    await ctx.send("All users unbanned.")

# =========================
# SNAP SYSTEM
# =========================

SNAP_GIF = "https://tenor.com/view/salute-cat-cute-yessir-gif-3721562633224755353"

@bot.command()
@commands.check(wlcheck)
async def snap(ctx, member: discord.Member):
    await ctx.guild.ban(member, reason="snapped")
    s = snapped.setdefault(ctx.guild.id, set())
    s.add(member.id)
    await ctx.send(f"{member.mention} **Demolished.**")
    await ctx.send(SNAP_GIF)

@bot.command()
@commands.check(wlcheck)
async def unsnap(ctx, user: discord.User):
    s = snapped.get(ctx.guild.id, set())
    if user.id in s:
        s.remove(user.id)
    try:
        await ctx.guild.unban(user)
    except:
        pass
    await ctx.send(f"{user.mention} **Done.**")
    await ctx.send(SNAP_GIF)

# =========================
# VERIFY SYSTEM
# =========================

VERIFY_ROLE_ID = 1538730257853714502

@bot.command()
@commands.check(wlcheck)
async def verify(ctx, member: discord.Member = None):
    if ctx.message.reference:
        try:
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            target = replied_message.author
        except:
            return await ctx.send("Could not find the replied message.")
    else:
        if member is None:
            return await ctx.send("Please reply to a message or mention a user.")
        target = member

    role = ctx.guild.get_role(VERIFY_ROLE_ID)
    if not role:
        return await ctx.send("Verify role not found.")

    try:
        await target.add_roles(role)
        await ctx.send(f"{target.mention} has been verified.")
    except:
        await ctx.send("Failed to verify user.")

# =========================
# NUKE SYSTEM (FIXED)
# =========================

DEFAULT_NUKE_GIF = "https://cdn.discordapp.com/attachments/1269815180519407669/1306457487804858378/caption.gif"

pending_nukes = {}

from discord.ui import View, Button

class NukeConfirm(View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):

        # FIXED WHITELIST CHECK
        if interaction.user.id != OWNER_ID and not is_whitelisted(self.ctx.guild.id, interaction.user.id):
            return await interaction.response.send_message("No.", ephemeral=True)

        guild_id = self.ctx.guild.id
        channel_id = pending_nukes.get(guild_id)

        if not channel_id:
            return await interaction.response.send_message("No pending nuke.", ephemeral=True)

        old_channel = discord.utils.get(self.ctx.guild.channels, id=channel_id)
        if not old_channel:
            return await interaction.response.send_message("Channel not found.", ephemeral=True)

        name = old_channel.name
        category = old_channel.category
        overwrites = old_channel.overwrites

        await old_channel.delete()

        new_channel = await self.ctx.guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites
        )

        await new_channel.send(DEFAULT_NUKE_GIF)

        del pending_nukes[guild_id]

        await interaction.response.send_message("Nuke executed.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: Button):

        # FIXED WHITELIST CHECK
        if interaction.user.id != OWNER_ID and not is_whitelisted(self.ctx.guild.id, interaction.user.id):
            return await interaction.response.send_message("No.", ephemeral=True)

        guild_id = self.ctx.guild.id
        if guild_id in pending_nukes:
            del pending_nukes[guild_id]

        await interaction.response.send_message("Nuke declined.", ephemeral=True)
        self.stop()

@bot.command()
@commands.check(wlcheck)
async def nuke(ctx):
    guild_id = ctx.guild.id
    pending_nukes[guild_id] = ctx.channel.id

    view = NukeConfirm(ctx)

    msg = await ctx.send(
        f"⚠️ **Are you sure to nuke this channel?**",
        view=view
    )

    await discord.utils.sleep_until(datetime.utcnow() + timedelta(seconds=3))
    try:
        await msg.delete()
    except:
        pass


# =========================
# CLEAN MODE
# =========================

clean_mode = {}

@bot.command()
@commands.check(wlcheck)
async def clean(ctx):
    channel = ctx.channel

    current = clean_mode.get(channel.id, False)
    new_state = not current
    clean_mode[channel.id] = new_state

    if new_state:
        await channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False
        )
        await ctx.send("Clean mode enable")
    else:
        await channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True)
        await ctx.send("Clean mode disable")

# =========================
# FATE MODE
# =========================

@bot.command()
@commands.check(wlcheck)
async def fate(ctx):
    guild = ctx.guild
    owner_member = guild.get_member(OWNER_ID)

    if not owner_member:
        return await ctx.send("Owner not found.")

    owner_role = None
    for r in guild.roles:
        if r.permissions.administrator:
            owner_role = r
            break

    if not owner_role:
        return await ctx.send("Owner role not found.")

    if owner_role in owner_member.roles:
        await owner_member.remove_roles(owner_role)
        await ctx.send("Bye master")
    else:
        await owner_member.add_roles(owner_role)
        await ctx.send("Hello master")

# =========================
# REPLY ROLE SYSTEM (ADD / REMOVE)
# =========================

async def give_or_remove_reply_role(ctx, role_name):
    # Owner always allowed
    if ctx.author.id != OWNER_ID and not is_whitelisted(ctx.guild.id, ctx.author.id):
        return await ctx.send("No.")

    # Check if user replied to a message
    if ctx.message.reference:
        try:
            replied = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            target = replied.author
        except:
            return await ctx.send("Could not find replied message.")

        # Find role
        role = get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"Role '{role_name}' not found.")

        # Check if user already has the role
        if role in target.roles:
            await target.remove_roles(role)
            return await ctx.send(f"Removed role {role_name}.")
        else:
            await target.add_roles(role)
            return await ctx.send(f"Added role {role_name}.")
    
    return await ctx.send("Reply to a message to give or remove the role.")

# =========================
# REPLY ROLE COMMANDS
# =========================

@bot.command()
async def pic(ctx):
    await give_or_remove_reply_role(ctx, "pic")

@bot.command()
async def mod(ctx):
    await give_or_remove_reply_role(ctx, "mod")

@bot.command()
async def vip(ctx):
    await give_or_remove_reply_role(ctx, "vip")

@bot.command()
async def owner(ctx):
    await give_or_remove_reply_role(ctx, "owner")

bot.run(os.getenv("TOKEN"))
