import discord, threading, os, json, random, string, asyncio, io
from discord import app_commands
from flask import Flask, session, redirect, request, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "midnimo-secret-123")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
API = "https://discord.com/api/v10"

# --- WEBSITE ---
HOME_HTML = """
<!DOCTYPE html><html lang="so"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Midnimo Bot</title><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#0f0f1a;color:white} nav{display:flex;justify-content:space-between;padding:20px 5%;background:#1a1a2e}
.logo{font-size:24px;font-weight:bold} .logo span{color:#00ff88} nav a{color:white;text-decoration:none;margin-left:20px}
.hero{text-align:center;padding:80px 20px;background:linear-gradient(135deg,#1a1a2e,#16213e)}
.hero h1{font-size:55px} .hero h1 span{color:#00ff88} .hero p{color:#aaa;margin:15px 0 30px;font-size:18px}
.btn{display:inline-block;padding:14px 28px;border-radius:10px;text-decoration:none;font-weight:bold;margin:5px}
.btn-green{background:#00ff88;color:black} .btn-dark{background:#2b2d31;color:white;border:1px solid #444}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;padding:50px 5%}
.card{background:#1a1a2e;padding:25px;border-radius:15px;border:1px solid #333} .card p{color:#aaa;line-height:1.6;margin-top:8px}
.cmd{background:#1a1a2e;padding:12px 18px;border-radius:8px;margin:8px 0;display:flex;justify-content:space-between}
.cmd b{color:#00ff88} footer{text-align:center;padding:30px;color:#666}
.status{background:#003d1f;color:#00ff88;padding:5px 12px;border-radius:20px;font-size:13px}
</style></head><body>
<nav><div class="logo">🎫 <span>Midnimo</span> Bot</div><div><a href="/">Home</a><a href="/login">Dashboard</a></div></nav>
<div class="hero"><span class="status">● ONLINE - 24/7 on Koyeb</span>
<h1>Midnimo <span>Bot</span></h1><p>Somali Ticket + Backup hal bot.<br>Server-kaaga ka dhig mid ammaan ah.</p>
<a class="btn btn-green" href="https://discord.com/oauth2/authorize?client_id=__CID__&permissions=8&scope=bot%20applications.commands">+ Add to Discord</a>
<a class="btn btn-dark" href="/login">Dashboard</a></div>
<div class="features">
<div class="card"><h3>🎫 Ticket System</h3><p>Sida Ticket Tool. Panel, Claim, Close, Transcript, Add/Remove.</p></div>
<div class="card"><h3>💾 Backup</h3><p>/kaydi - Roles, Channels, Permissions, Members, Emojis. Auto-Backup maalin kasta.</p></div>
<div class="card"><h3>🔄 Restore</h3><p>/soceli - Hal click ku soo celi server-kaaga.</p></div>
<div class="card"><h3>🛡️ Security</h3><p>/tirtir wuxuu u baahan yahay code: HAA TIRTIR.</p></div></div>
<div style="padding:0 5% 40px"><h2>📋 Commands</h2><br>
<div class="cmd"><span><b>/kaydi</b> - Kaydi server-ka</span><span>Owner</span></div>
<div class="cmd"><span><b>/soceli</b> - Soo celi backup</span><span>Owner</span></div>
<div class="cmd"><span><b>/backup-list</b> - Liiska backup-yada</span><span>Owner</span></div>
<div class="cmd"><span><b>/ticket-setup</b> - Deji Ticket</span><span>Admin</span></div>
<div class="cmd"><span><b>/panel-create / /panel-send</b> - Panel</span><span>Admin</span></div>
<div class="cmd"><span><b>/tirtir</b> - Tirtir server-ka</span><span>Owner</span></div></div>
<footer>© 2026 Midnimo Bot - Hosted on Koyeb | Somali Community</footer></body></html>
"""

@app.route("/")
def home(): return render_template_string(HOME_HTML.replace("__CID__", CLIENT_ID or ""))
@app.route("/health")
def health(): return "OK", 200
@app.route("/login")
def login(): return redirect(f"{API}/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={os.getenv('REDIRECT_URI')}&response_type=code&scope=identify guilds")
@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": os.getenv("REDIRECT_URI")}
    r = requests.post(f"{API}/oauth2/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}).json()
    token = r.get("access_token")
    if not token: return "Login Failed", 403
    user = requests.get(f"{API}/users/@me", headers={"Authorization": f"Bearer {token}"}).json()
    guilds = requests.get(f"{API}/users/@me/guilds", headers={"Authorization": f"Bearer {token}"}).json()
    my = []
    for g in guilds:
        if int(g["permissions"]) & 0x8:
            icon = f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png" if g.get("icon") else "https://cdn.discordapp.com/embed/avatars/0.png"
            my.append({"id": g["id"], "name": g["name"], "icon": icon})
    session["user"] = user; session["guilds"] = my
    return redirect("/dashboard")
@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect("/login")
    html = "<style>body{background:#0f0f1a;color:white;font-family:sans-serif;padding:30px}.g{background:#1a1a2e;padding:15px;border-radius:12px;margin:10px 0;display:flex;gap:15px;align-items:center}img{border-radius:50%}a{color:#00ff88}</style>"
    html += f"<h1>Ku soo dhawow {session['user']['username']} 👋</h1>"
    for g in session["guilds"]: html += f"<div class='g'><img src='{g['icon']}' width='50'><b>{g['name']}</b></div>"
    return html + "<br><a href='/'>Home</a>"
def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# --- BOT ---
class MidnimoBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self): await self.tree.sync()
client = MidnimoBot()

def load_db():
    if not os.path.exists("db.json"): return {"panels": {}, "tickets": {}, "settings": {}}
    with open("db.json") as f: return json.load(f)
def save_db(d):
    with open("db.json", "w") as f: json.dump(d, f, indent=4)

# Ticket Views
class TicketControlView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Claim", emoji="🙋", style=discord.ButtonStyle.green, custom_id="midnimo_claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ {interaction.user.mention} ayaa qaatay ticket-kan!")
    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.red, custom_id="midnimo_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Waa la xirayaa...")
        msgs=[]
        async for m in interaction.channel.history(limit=200): msgs.append(f"{m.author}: {m.content}")
        db=load_db()
        if str(interaction.channel.id) in db["tickets"]:
            db["tickets"][str(interaction.channel.id)]["open"]=False; save_db(db)
            log_id=db["settings"].get(str(interaction.guild_id),{}).get("log_channel")
            if log_id:
                lc=interaction.guild.get_channel(int(log_id))
                if lc:
                    file=discord.File(io.BytesIO("\n".join(reversed(msgs)).encode()), filename=f"transcript-{interaction.channel.name}.txt")
                    await lc.send(f"🔒 Ticket la xiray: {interaction.channel.name}", file=file)
        await asyncio.sleep(2); await interaction.channel.delete()

class TicketPanelView(discord.ui.View):
    def __init__(self, panel_id):
        super().__init__(timeout=None); self.panel_id=panel_id
        db=load_db(); panel=db["panels"].get(panel_id,{})
        for btn in panel.get("buttons",[]):
            b=discord.ui.Button(label=btn["label"], emoji=btn.get("emoji","🎫"), style=discord.ButtonStyle.blurple, custom_id=f"midnimo_open_{panel_id}_{btn['label']}")
            b.callback=self.make_cb(btn); self.add_item(b)
    def make_cb(self, btn_data):
        async def cb(interaction: discord.Interaction):
            guild=interaction.guild; user=interaction.user; db=load_db()
            for tid,t in db["tickets"].items():
                if t["owner"]==user.id and t["guild"]==guild.id and t["open"]:
                    ch=guild.get_channel(int(tid))
                    if ch: await interaction.response.send_message(f"❌ Hore waxaad u leedahay: {ch.mention}", ephemeral=True); return
            s=db["settings"].get(str(guild.id),{})
            ow={guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
            if s.get("staff_role"):
                staff=guild.get_role(int(s["staff_role"]))
                if staff: ow[staff]=discord.PermissionOverwrite(view_channel=True, send_messages=True)
            cat=guild.get_channel(int(s["category"])) if s.get("category") else None
            num=len([t for t in db["tickets"].values() if t["guild"]==guild.id])+1
            channel=await guild.create_text_channel(f"ticket-{num:04d}", category=cat, overwrites=ow)
            embed=discord.Embed(title=f"{btn_data.get('emoji','🎫')} {btn_data['label']}", description=f"Ku soo dhawow {user.mention}", color=0x00ff88)
            await channel.send(embed=embed, view=TicketControlView())
            db["tickets"][str(channel.id)]={"owner":user.id,"guild":guild.id,"type":btn_data["label"],"open":True}; save_db(db)
            await interaction.response.send_message(f"✅ Ticket: {channel.mention}", ephemeral=True)
        return cb

@client.tree.command(name="ticket-setup", description="Deji Ticket")
@app_commands.default_permissions(administrator=True)
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, staff_role: discord.Role, log_channel: discord.TextChannel):
    db=load_db(); db["settings"][str(interaction.guild_id)]={"category":str(category.id),"staff_role":str(staff_role.id),"log_channel":str(log_channel.id)}; save_db(db)
    await interaction.response.send_message(f"✅ Ticket Setup Dhammaaday!", ephemeral=True)
@client.tree.command(name="panel-create", description="Samee Panel")
@app_commands.default_permissions(administrator=True)
async def panel_create(interaction: discord.Interaction, magac: str):
    db=load_db(); pid=str(len(db["panels"])+1); db["panels"][pid]={"name":magac,"buttons":[]}; save_db(db)
    await interaction.response.send_message(f"✅ Panel: **{magac}** ID: `{pid}`", ephemeral=True)
@client.tree.command(name="panel-add-button", description="Ku dar button")
@app_commands.default_permissions(administrator=True)
async def panel_add_button(interaction: discord.Interaction, panel_id: str, label: str, emoji: str="🎫"):
    db=load_db()
    if panel_id not in db["panels"]: await interaction.response.send_message("❌ Panel lama helin!", ephemeral=True); return
    db["panels"][panel_id]["buttons"].append({"label":label,"emoji":emoji}); save_db(db)
    await interaction.response.send_message(f"✅ Button `{emoji} {label}` lagu daray!", ephemeral=True)
@client.tree.command(name="panel-send", description="Soo saar Panel")
@app_commands.default_permissions(administrator=True)
async def panel_send(interaction: discord.Interaction, panel_id: str):
    db=load_db(); panel=db["panels"].get(panel_id)
    if not panel: await interaction.response.send_message("❌ Panel lama helin!", ephemeral=True); return
    embed=discord.Embed(title=f"🎫 {panel['name']}", description="Dooro nooca ticket-ka:", color=0x00ff88)
    await interaction.response.send_message(embed=embed, view=TicketPanelView(panel_id))

# --- BACKUP ---
async def do_backup(guild):
    bid=''.join(random.choices(string.ascii_lowercase+string.digits, k=8))
    data={"backup_id":bid,"guild_name":guild.name,"guild_id":guild.id,"date":datetime.now().strftime("%d/%m/%Y %H:%M"),"settings":{"name":guild.name},"roles":[],"categories":[],"members":[],"emojis":[]}
    def get_ow(o):
        d={}
        for t,ov in o.overwrites.items(): d[str(t.id)]={"type":"role" if isinstance(t,discord.Role) else "member","allow":ov.pair()[0].value,"deny":ov.pair()[1].value}
        return d
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
        if not r.is_default() and not r.managed: data["roles"].append({"id":r.id,"name":r.name,"permissions":r.permissions.value,"color":r.color.value,"hoist":r.hoist,"mentionable":r.mentionable,"position":r.position})
    for cat in sorted(guild.categories, key=lambda c: c.position):
        cd={"id":cat.id,"name":cat.name,"position":cat.position,"overwrites":get_ow(cat),"channels":[]}
        for ch in sorted(cat.channels, key=lambda c: c.position):
            ct="text" if isinstance(ch,discord.TextChannel) else "voice" if isinstance(ch,discord.VoiceChannel) else "text"
            cd["channels"].append({"id":ch.id,"name":ch.name,"type":ct,"position":ch.position,"topic":getattr(ch,"topic",None),"overwrites":get_ow(ch)})
        data["categories"].append(cd)
    for m in guild.members:
        if not m.bot: data["members"].append({"name":m.name,"id":m.id,"roles":[r.id for r in m.roles if not r.is_default()]})
    for e in guild.emojis: data["emojis"].append({"name":e.name,"id":e.id,"url":str(e.url)})
    with open(f"backup_{bid}.json","w",encoding="utf-8") as f: json.dump(data,f,indent=4,ensure_ascii=False)
    lst=[]
    if os.path.exists("backup_list.json"):
        with open("backup_list.json") as f: lst=json.load(f)
    lst.append({"id":bid,"guild":guild.name,"date":data["date"],"roles":len(data["roles"])})
    with open("backup_list.json","w") as f: json.dump(lst,f,indent=4)
    return bid,data

@client.tree.command(name="kaydi", description="Kaydi server-ka")
async def kaydi(interaction: discord.Interaction):
    if interaction.user.id!=OWNER_ID: await interaction.response.send_message("❌ Adiga ku khuseeyo ma aha!", ephemeral=True); return
    await interaction.response.send_message("⏳ Midnimo Bot - Kaydinta...", ephemeral=True)
    bid,data=await do_backup(interaction.guild)
    await interaction.edit_original_response(content=f"✅ **Backup Guulaystay!** 🆔 ID: `{bid}`\n🛡️ Roles: {len(data['roles'])} | 📁 Categories: {len(data['categories'])} | 👥 Members: {len(data['members'])}")
@client.tree.command(name="backup-list", description="Liiska backup-yada")
async def backup_list(interaction: discord.Interaction):
    if interaction.user.id!=OWNER_ID: await interaction.response.send_message("❌ Adiga ku khuseeyo ma aha!", ephemeral=True); return
    if not os.path.exists("backup_list.json"): await interaction.response.send_message("❌ Backup ma jiro!", ephemeral=True); return
    with open("backup_list.json") as f: d=json.load(f)
    txt="📂 **Liiska Backup-yada:**\n\n"
    for b in d[-10:]: txt+=f"🆔 `{b['id']}` | {b['guild']} | {b['date']}\n"
    await interaction.response.send_message(txt, ephemeral=True)
@client.tree.command(name="soceli", description="Soo celi backup")
async def soceli(interaction: discord.Interaction, backup_id: str):
    if interaction.user.id!=OWNER_ID: await interaction.response.send_message("❌ Adiga ku khuseeyo ma aha!", ephemeral=True); return
    fn=f"backup_{backup_id}.json"
    if not os.path.exists(fn): await interaction.response.send_message("❌ Backup lama helin!", ephemeral=True); return
    with open(fn) as f: data=json.load(f)
    await interaction.response.send_message("⏳ Soo celinta...", ephemeral=True)
    guild=interaction.guild; role_map={}
    for r in sorted(data.get("roles",[]), key=lambda x: x["position"]):
        try:
            nr=await guild.create_role(name=r["name"], permissions=discord.Permissions(r["permissions"]), color=discord.Color(r["color"]))
            role_map[str(r["id"])]=nr
            try: await nr.edit(position=r["position"])
            except: pass
        except: pass
    for cat in sorted(data.get("categories",[]), key=lambda x: x["position"]):
        try:
            nc=await guild.create_category(cat["name"])
            for ch in sorted(cat["channels"], key=lambda x: x["position"]):
                try:
                    if ch["type"]=="voice": await guild.create_voice_channel(ch["name"], category=nc)
                    else: await guild.create_text_channel(ch["name"], category=nc, topic=ch.get("topic"))
                except: pass
        except: pass
    await interaction.edit_original_response(content="✅ **Restore Dhammaaday!**")

# --- TIRTIR - SIDII HORE ---
@client.tree.command(name="tirtir", description="Tirtir server-ka - Kaliya Owner + Code")
async def tirtir(interaction: discord.Interaction, code: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Adiga ku khuseeyo ma aha! Kaliya Owner ayaa tirtiri kara.", ephemeral=True)
        return
    if code != "HAA TIRTIR":
        await interaction.response.send_message("❌ Code waa khaldan yahay!\nSi aad u tirtirto qor: `/tirtir HAA TIRTIR`", ephemeral=True)
        return
    # Backup auto ah ka hor inta aan la tirin
    await interaction.response.send_message("⚠️ **DIGNIIN UGU DANBEYSA!**\nBackup ayaa la kaydinayaa kadibna server-ka waa la tirtiri doonaa...\n10 ilbiriqsi kadib wuu bilaabanayaa. Haddii aad ka laabatay, hadda Bot-ka ka saar server-ka!", ephemeral=True)
    try:
        bid, data = await do_backup(interaction.guild)
        print(f"Auto-backup before wipe: {bid}")
    except Exception as e:
        print(f"Backup failed before wipe: {e}")
    await asyncio.sleep(10)
    guild = interaction.guild
    # 1. Tirtir Channels
    for ch in list(guild.channels):
        try: await ch.delete()
        except: pass
    # 2. Tirtir Roles (marka laga reebo @everyone iyo bot-ka)
    for r in list(guild.roles):
        try:
            if not r.is_default() and not r.managed and r < guild.me.top_role:
                await r.delete()
        except: pass
    # 3. Tirtir Emojis
    for e in list(guild.emojis):
        try: await e.delete()
        except: pass
    # 4. Samee channel cusub oo caddeyn ah
    try:
        ch = await guild.create_text_channel("midnimo-tirtir")
        await ch.send(f"✅ Server-ka waa la tirtiray by {interaction.user.mention}\n🆔 Backup ID (hore loo kaydiyay): `{bid}`\nSi aad u soo celiso: `/soceli {bid}`")
    except: pass

@client.event
async def on_ready():
    print(f"Midnimo Bot Online: {client.user}")
    db=load_db()
    for pid in db["panels"]: client.add_view(TicketPanelView(pid))
    client.add_view(TicketControlView())

if __name__=="__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    client.run(os.getenv("DISCORD_TOKEN"))
