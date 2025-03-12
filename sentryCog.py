import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, UTC

class Sentry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.check_status.start()
        self.last_status = None
        self.is_api_heavy = False
        self.status_messages = {}

    def cog_unload(self):
        self.check_status.cancel()
        self.bot.loop.create_task(self.session.close())

    @tasks.loop(minutes=1.0)
    async def check_status(self):
        status_url = "https://status.sentry.io/api/v2/status.json"

        try:
            async with self.session.get(status_url) as response:
                status_data = await response.json()
                if not isinstance(status_data, dict):
                    raise ValueError("Invalid status data format")
                
                status = status_data['status']['indicator']
                if status is None:
                    raise ValueError("Status not found")
                
                if status != "none" and not self.is_api_heavy:
                    self.is_api_heavy = True
                    await self.send_notification(status, status_data)
                    await self.start_status_updates()
                
                elif status == "none" and self.is_api_heavy:
                    self.is_api_heavy = False
                    await self.send_notification(status, status_data)
                    await self.stop_status_updates()

                if self.is_api_heavy:
                    await self.update_status_message(status_data)

        except Exception as e:
            print(f"Sentry status check error: {str(e)}")

    async def start_status_updates(self):
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.send("Sentry状態の監視を開始します...")
                self.status_messages[server_id] = message

    async def stop_status_updates(self):
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(content="Sentry状態が正常に戻りました。監視を終了します。")
        self.status_messages.clear()

    async def update_status_message(self, status_data):
        embed = discord.Embed(
            title="現在のSentry状態",
            description=status_data['status']['description'],
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(embed=embed)

    async def send_notification(self, status, data):
        color_map = {
            "critical": discord.Color.red(),
            "major": discord.Color.red(),
            "minor": discord.Color.gold(),
            "none": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="Sentry サーバー状態更新",
            description=f"現在のステータス: {status}",
            color=color_map.get(status, discord.Color.blue()),
            timestamp=datetime.now(UTC))
        
        embed.add_field(name="詳細", value=data['status']['description'], inline=False)
        embed.set_footer(text="Sentry Status Monitor")
        
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @check_status.before_loop
    async def before_check_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Sentry(bot))
