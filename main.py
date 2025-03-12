import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db import Database

#Cog load
from vrchatCog import VRchat
from lineCog import LINE
from openaiCog import OpenAI
from discordCog import Discord
from newrelicCog import NewRelic
from datadogCog import Datadog
from slackCog import Slack
from microsoftCog import Microsoft
from vercelCog import Vercel
from glitchCog import Glitch
from epicCog import Epic
from githubCog import GitHub
from StripeCog import Stripe
from akamaiCog  import Akamai
from onesignalCog import OneSignal
from rubygemsCog import RubyGems
from npmCog import npmjs
from bitbucketCog import Bitbucket
from circleciCog import CircleCI
from travisciCog import TravisCI
from codecovCog import Codecov
from sentryCog import Sentry
from cypressCog import Cypress
from AirbrakeCog import Airbrake
from zoomCog import Zoom
from figmaCog import Figma

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="/", intents=intents)
database = Database()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.config = database.get_notification_channels()
    await client.add_cog(VRchat(client))
    await client.add_cog(LINE(client))
    await client.add_cog(OpenAI(client))
    await client.add_cog(Discord(client))
    await client.add_cog(NewRelic(client))
    await client.add_cog(Datadog(client))
    await client.add_cog(Slack(client))
    await client.add_cog(Microsoft(client))
    await client.add_cog(Vercel(client))
    await client.add_cog(Glitch(client))
    await client.add_cog(Epic(client))
    await client.add_cog(GitHub(client))
    await client.add_cog(Stripe(client))
    await client.add_cog(Akamai(client))
    await client.add_cog(OneSignal(client))
    await client.add_cog(npmjs(client))
    await client.add_cog(RubyGems(client))
    await client.add_cog(Bitbucket(client))
    await client.add_cog(CircleCI(client))
    await client.add_cog(TravisCI(client))
    await client.add_cog(Codecov(client))
    await client.add_cog(Sentry(client))
    await client.add_cog(Cypress(client))
    await client.add_cog(Airbrake(client))
    await client.add_cog(Zoom(client))
    await client.add_cog(Figma(client))
    await client.tree.sync()

@client.tree.command(name="set_channel", description="何かのサービスに問題が発生したときに通知するチャンネルを設定します")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドを実行するには管理者権限が必要です", ephemeral=True)
        return
    
    current_channel = database.get_channel_id(interaction.guild.id)
    if current_channel:
        await interaction.response.send_message(
            f"通知チャンネルを {channel.mention} に上書き設定しました\n"
            f"(以前の設定: <#{current_channel}>)",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"通知チャンネルを {channel.mention} に設定しました",
            ephemeral=True
        )
    
    database.add_notification_channel(interaction.guild.id, channel.id)
    client.config = database.get_notification_channels()

@client.tree.command(name="check", description="現在設定されている通知チャンネルを表示します")
async def check(interaction: discord.Interaction):
    channel_id = database.get_channel_id(interaction.guild.id)
    if channel_id:
        await interaction.response.send_message(
            f"現在の通知チャンネル: <#{channel_id}>",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "通知チャンネルが設定されていません",
            ephemeral=True
        )

@client.tree.command(name="remove_channel", description="通知チャンネルを削除します")
async def remove_channel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("このコマンドを実行するには管理者権限が必要です", ephemeral=True)
        return
    
    database.remove_notification_channel(interaction.guild.id)
    client.config = database.get_notification_channels()
    await interaction.response.send_message("通知チャンネルを削除しました", ephemeral=True)

if __name__ == "__main__":
    client.run(os.getenv("DISCORD_BOT_TOKEN"))
