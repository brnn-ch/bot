import discord
import os
import asyncio
from discord.ext import commands
from keep_alive import keep_alive

# --- AYARLAR ---
TOKEN = os.environ.get("TOKEN")

# --- ÖNEMLİ: YETKİLİ ROL LİSTESİ ---
# Buraya gizli odaları görmesini istediğin rollerin ID'lerini virgülle ayırarak yaz.
# Örnek: [111111111, 222222222] (Yönetim ve Üst Yetkili ID'leri)
# Sunucu sahibi zaten her şeyi görür, onu eklemene gerek yok.
YETKILI_ROLLER = [1465050726576427263, 1465056480871845949] 

# --- KATEGORİ AYARI ---
# Destek kanallarının açılacağı Ana Kategori ID'si
TEK_KATEGORI_ID = 1466020562219302952 
# -------------------------------

# --- KANAL KAPATMA BUTONU ---
class TicketKapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Talebi Kapat & Sil", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="btn_ticket_kapat")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Kanal 5 saniye içinde siliniyor...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- KANAL AÇMA FONKSİYONU ---
async def kanal_ac(interaction, baslik_kodu, konu, icerik, renk):
    # 1. Hedef Kategoriyi Bul
    kategori = interaction.guild.get_channel(TEK_KATEGORI_ID)
    
    if kategori is None:
        await interaction.response.send_message(f"❌ HATA: Kategori ID'si ({TEK_KATEGORI_ID}) bulunamadı!", ephemeral=True)
        return

    # 2. İzinleri Ayarla
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), # Herkese kapat
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True) # Kullanıcıya aç
    }
    
    # LİSTEDEKİ TÜM YETKİLİ ROLLERE İZİN VER
    # Listedeki her bir ID için döngü kuruyoruz
    for rol_id in YETKILI_ROLLER:
        role = interaction.guild.get_role(rol_id)
        if role:
            # Bu role mesajları okuma ve yazma izni ver
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    # 3. Kanalı Oluştur
    channel_name = f"{baslik_kodu}-{interaction.user.name}"
    channel = await interaction.guild.create_text_channel(name=channel_name, category=kategori, overwrites=overwrites)
    
    # 4. Bilgilendirme
    await interaction.response.send_message(f"✅ Destek kanalı açıldı: {channel.mention}", ephemeral=True)
    
    # 5. İçerik Mesajı
    embed = discord.Embed(title=f"📩 Yeni Talep: {baslik_kodu.upper()}", description=f"**Konu:** {konu}\n**İçerik:** {icerik}", color=renk)
    embed.set_footer(text="Yetkililer en kısa sürede dönüş yapacaktır.")
    
    # Etiketlenecek rollerin metnini hazırla
    etiketler = ""
    for rol_id in YETKILI_ROLLER:
        etiketler += f"<@&{rol_id}> "

    await channel.send(f"{interaction.user.mention} {etiketler}", embed=embed, view=TicketKapatView())

# --- MODALLAR ---

class SikayetModal(discord.ui.Modal, title='Şikayet Bildirimi'):
    kisi = discord.ui.TextInput(label='Şikayet Edilen', style=discord.TextStyle.short, required=True)
    sebep = discord.ui.TextInput(label='Olayın Detayı', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await kanal_ac(interaction, "sikayet", f"Şikayet Edilen: {self.kisi.value}", self.sebep.value, discord.Color.red())

class BanModal(discord.ui.Modal, title='Ban İtirazı'):
    sebep = discord.ui.TextInput(label='Ban Sebebiniz', style=discord.TextStyle.short, required=True)
    savunma = discord.ui.TextInput(label='Savunmanız', style=discord.TextStyle.paragraph, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await kanal_ac(interaction, "ban-itiraz", f"Ban Sebebi: {self.sebep.value}", self.savunma.value, discord.Color.dark_red())

class OneriModal(discord.ui.Modal, title='İstek ve Öneri'):
    konu = discord.ui.TextInput(label='Konu', style=discord.TextStyle.short, required=True)
    det
