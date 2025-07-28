import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import io
import qrcode
from flask import Flask
from threading import Thread
import asyncio

# ========== FLASK KEEP-ALIVE ==========
app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== CONFIG DISCORD ==========
TOKEN = os.getenv("DISCORD_TOKEN") or "COLOQUE_SEU_TOKEN_AQUI"

CANAIS_AUTORIZADOS = [1399145102185726034, 1399164514359971944]
CANAL_COMPROVANTES_ID = 1399155880024473733
CANAL_STATUS_ID = 1399463056479617147

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

PRODUTOS = {
    "Keylogger": {
        "preco": "R$15",
        "pix": "00020101021126580014br.gov.bcb.pix0136ebd60a75-b873-4296-bd9a-d1d477d926ca520400005303986540515.005802BR5917DAVI E S CARVALHO6007RESENDE62070503***6304A198",
        "link_produto": "https://www.mediafire.com/file/u7ou6immuoadz1b/SISTEMA+DE+SEGURAN%C3%87A.rar/file"
    },
    "Bot para lojas": {
        "preco": "R$20",
        "pix": "00020101021126580014br.gov.bcb.pix0136ebd60a75-b873-4296-bd9a-d1d477d926ca520400005303986540520.005802BR5917DAVI E S CARVALHO6007RESENDE62070503***6304C870",
        "link_produto": "https://www.mediafire.com/file/2f7nk9mg884xkvw/BOT+DISCORD.rar/file"
    }
}

bot.produtos_comprados = {}

class LojaView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProdutoSelect())

class ProdutoSelect(Select):
    def __init__(self):
        options = [discord.SelectOption(label=produto, description=f"{dados['preco']}") for produto, dados in PRODUTOS.items()]
        super().__init__(placeholder="Selecione um produto", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        produto = self.values[0]
        dados = PRODUTOS[produto]
        bot.produtos_comprados[interaction.user.id] = produto

        await interaction.user.send(
            f"✅ Você escolheu o produto **{produto}** por **{dados['preco']}**\n\n"
            f"💳 Chave Pix: `{dados['pix']}`\n\n"
            f"📸 Após o pagamento, envie o comprovante no canal da loja."
        )
        await interaction.response.send_message("✅ As instruções foram enviadas para sua DM.", ephemeral=True)

def criar_embed_loja():
    embed = discord.Embed(
        title="🛍️ Loja Oficial",
        description="Selecione um produto abaixo para comprar!",
        color=0x00ff00
    )
    for nome, dados in PRODUTOS.items():
        embed.add_field(name=f"💎 {nome}", value=f"💵 {dados['preco']}", inline=False)
    embed.set_footer(text="Após escolher, siga as instruções via DM.")
    return embed

class ConfirmarPagamentoView(View):
    def __init__(self, comprador: discord.User):
        super().__init__(timeout=None)
        self.comprador = comprador

    @discord.ui.button(label="✅ Confirmar Pagamento", style=discord.ButtonStyle.success)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você não tem permissão para confirmar.", ephemeral=True)
            return

        produto_escolhido = bot.produtos_comprados.get(self.comprador.id)
        if not produto_escolhido:
            await interaction.response.send_message("⚠️ Nenhum produto selecionado pelo comprador.", ephemeral=True)
            return

        dados = PRODUTOS.get(produto_escolhido)
        try:
            await self.comprador.send(
                f"✅ Seu pagamento foi confirmado!\n🔓 Aqui está seu produto **{produto_escolhido}**:\n{dados['link_produto']}"
            )
            await interaction.response.send_message("📦 Produto enviado ao comprador!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Não consegui enviar a DM para o comprador.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

    canal_status = bot.get_channel(CANAL_STATUS_ID)
    if canal_status:
        try:
            await canal_status.send("✅ Bot está online e monitorado!")
        except:
            pass

    for guild in bot.guilds:
        for canal_id in CANAIS_AUTORIZADOS:
            canal = bot.get_channel(canal_id)
            if canal:
                try:
                    await canal.purge(limit=100)
                    embed = criar_embed_loja()
                    view = LojaView()
                    await canal.send(embed=embed, view=view)
                except Exception as e:
                    print(f"Erro ao enviar embed no canal {canal_id}: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in CANAIS_AUTORIZADOS and message.attachments:
        canal_comprovantes = bot.get_channel(CANAL_COMPROVANTES_ID)
        if canal_comprovantes:
            view = ConfirmarPagamentoView(message.author)
            try:
                await canal_comprovantes.send(
                    content=f"📥 Novo comprovante de {message.author.mention}",
                    file=await message.attachments[0].to_file(),
                    view=view
                )
                await message.channel.send("📸 Comprovante enviado com sucesso!", delete_after=10)
                await message.delete()
            except Exception as e:
                print(f"Erro ao enviar comprovante: {e}")

    await bot.process_commands(message)

# ========== EXECUTA KEEP ALIVE E RECONNECT ==========
keep_alive()

async def start_bot():
    while True:
        try:
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ Bot caiu com erro: {e}")
            print("⏳ Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

try:
    asyncio.run(start_bot())
except KeyboardInterrupt:
    print("⛔ Bot desligado manualmente.")