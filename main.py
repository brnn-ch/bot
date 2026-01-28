import discord
import os
import asyncio
from discord.ext import commands
from keep_alive import keep_alive

# --- AYARLAR ---
TOKEN = os.environ.get("TOKEN")

# Şikayet ve Ban İtirazlarının düşeceği TEK kanal ID'si
LOG_KANALI_ID = 111111111111111111

# Açılan gizli odaları (Öneri/Soru) görebilecek Yetkili Rol ID'si
# (Eğer yoksa 0 bırak, sadece Yöneticiler görür)
YETKILI_ROL_ID = 0
# ---------------

# --- YARDIMCI FONKSİYONLAR ---

# A) Log Kanalına Mesaj Atan Fonksiyon (Şikayet ve Ban için)
async def loga_gonder(interaction, baslik, alanlar, renk):
    channel = interaction.guild.get_channel(LOG_KANALI_ID)
    if channel:
        embed = discord.Embed(title=baslik, color=renk, timestamp=interaction.created_at)
        embed.set_author(name=f"{interaction.user.display_name} ({interaction.user.id})", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        for ad, deger in alanlar:
            embed.add_field(name=ad, value=deger, inline=False)
            
        embed.set_footer(text="Destek Sistemi")
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Bildiriminiz yetkililere iletildi.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Log kanalı bulunamadı.", ephemeral=True)

# B) Özel Kanal (Ticket) Açan Fonksiyon (Öneri ve Soru için)
class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat & Sil", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_ticket_kapat")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kanal 5 saniye içinde siliniyor...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

async def kanal_ac(interaction, baslik, konu, icerik, renk):
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), # Herkese kapat
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True) # Kullanıcıya aç
    }
    
    # Yetkili rolü varsa ona da aç
    if YETKILI_ROL_ID != 0:
        role = interaction.guild.get_role(YETKILI_ROL_ID)
        if role:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    channel_name = f"{baslik}-{interaction.user.name}"
    channel = await interaction.guild.create_text_channel(name=channel_name, overwrites=overwrites)
    
    await interaction.response.send_message(f"✅ Sizin için özel kanal açıldı: {channel.mention}", ephemeral=True)
    
    embed = discord.Embed(title=f"📩 Yeni {baslik}", description=f"**Konu:** {konu}\n**İçerik:** {icerik}", color=renk)
    embed.set_footer(text="İşiniz bitince aşağıdaki butona basarak odayı kapatabilirsiniz.")
    
    await channel.send(f"{interaction.user.mention}", embed=embed, view=TicketKapatView())

# --- MODALLAR (FORMLAR) ---

# 1. Şikayet (Loga Gider)
class SikayetModal(discord.ui.Modal, title='Şikayet Bildirimi'):
    kisi = discord.ui.TextInput(label='Şikayet Edilen Kişi/Durum', style=discord.TextStyle.short, required=True)
    sebep = discord.ui.TextInput(label='Olayın Detayı', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await loga_gonder(interaction, "🚨 Yeni Şikayet", [("Şikayet Edilen", self.kisi.value), ("Sebep", self.sebep.value)], discord.Color.red())

# 2. Ban İtiraz (Loga Gider)
class BanModal(discord.ui.Modal, title='Ban İtirazı'):
    sebep = discord.ui.TextInput(label='Ban Sebebiniz', style=discord.TextStyle.short, required=True)
    savunma = discord.ui.TextInput(label='Savunmanız', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await loga_gonder(interaction, "⚖️ Ban İtirazı", [("Ban Sebebi", self.sebep.value), ("Savunma", self.savunma.value)], discord.Color.dark_red())

# 3. İstek & Öneri (KANAL AÇAR)
class OneriModal(discord.ui.Modal, title='İstek ve Öneri'):
    konu = discord.ui.TextInput(label='Öneri Konusu', style=discord.TextStyle.short, required=True)
    detay = discord.ui.TextInput(label='Detaylı Açıklama', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await kanal_ac(interaction, "oneri", self.konu.value, self.detay.value, discord.Color.green())

# 4. Ekstra Soru (KANAL AÇAR)
class SoruModal(discord.ui.Modal, title='Yetkiliye Soru'):
    soru = discord.ui.TextInput(label='Sorunuz Nedir?', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await kanal_ac(interaction, "soru", "Genel Soru", self.soru.value, discord.Color.blue())

# --- ANA PANEL BUTONLARI ---
class AnaPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Üst Satır: Loga Gidenler (Şikayet & Ban)
    @discord.ui.button(label="Şikayet Et", style=discord.ButtonStyle.danger, emoji="🚨", custom_id="btn_sikayet", row=0)
    async def sikayet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SikayetModal())

    @discord.ui.button(label="Ban İtiraz", style=discord.ButtonStyle.danger, emoji="⚖️", custom_id="btn_ban", row=0)
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BanModal())

    # Alt Satır: Kanal Açanlar (Öneri & Soru)
    @discord.ui.button(label="İstek & Öneri", style=discord.ButtonStyle.success, emoji="💡", custom_id="btn_oneri", row=1)
    async def oneri_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OneriModal())

    @discord.ui.button(label="Ekstra Soru", style=discord.ButtonStyle.primary, emoji="❓", custom_id="btn_soru", row=1)
    async def soru_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SoruModal())

# --- BOT BAŞLATMA ---
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f'{self.user} hazır!')
        self.add_view(AnaPanel())
        self.add_view(TicketKapatView())

bot = Bot()

@bot.command()
async def panel_kur(ctx):
    embed = discord.Embed(
        title="Destek Merkezi",
        description="Aşağıdaki butonları kullanarak işlem yapabilirsiniz.\n\n"
                    "🚨 **Şikayet & Ban:** Form doldurulur, yetkililere log düşer.\n"
                    "💬 **Öneri & Soru:** Size özel **canlı destek kanalı** açar.",
        color=discord.Color.dark_theme()
    )
    await ctx.send(embed=embed, view=AnaPanel())

# Web sunucusunu başlat ve botu çalıştır
keep_alive()
bot.run(TOKEN)