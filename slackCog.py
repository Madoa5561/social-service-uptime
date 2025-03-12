import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, UTC

class Slack(commands.Cog):
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
        status_url = "https://slack-status.com/api/v2.0.0/current"

        try:
            async with self.session.get(status_url) as response:
                status_data = await response.json()
                if not isinstance(status_data, dict):
                    raise ValueError("Invalid status data format")
                
                status = status_data.get('status')
                if status is None:
                    raise ValueError("Status not found")
                
                if status != "ok" and not self.is_api_heavy:
                    self.is_api_heavy = True
                    await self.send_notification(status, status_data)
                    await self.start_status_updates()
                
                elif status == "ok" and self.is_api_heavy:
                    self.is_api_heavy = False
                    await self.send_notification(status, status_data)
                    await self.stop_status_updates()

                if self.is_api_heavy:
                    await self.update_status_message(status_data)

        except Exception as e:
            print(f"Slack status check error: {str(e)}")

    async def start_status_updates(self):
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.send("Slack状態の監視を開始します...")
                self.status_messages[server_id] = message

    async def stop_status_updates(self):
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(content="Slack状態が正常に戻りました。監視を終了します。")
        self.status_messages.clear()

    async def update_status_message(self, status_data):
        embed = discord.Embed(
            title="現在のSlack状態",
            description=self.format_incidents(status_data),
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )
        
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(embed=embed)

    async def send_notification(self, status, data):
        color_map = {
            "active": discord.Color.red(),
            "resolved": discord.Color.green(),
            "ok": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="Slack サーバー状態更新",
            description=f"現在のステータス: {status}",
            color=color_map.get(status, discord.Color.blue()),
            timestamp=datetime.now(UTC)
        )
        
        if status != "ok":
            embed.add_field(name="詳細", value=self.format_incidents(data), inline=False)
        embed.set_footer(text="Slack Status Monitor")
        
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    def format_incidents(self, data):
        if not data.get('active_incidents'):
            return "すべてのサービスが正常に動作しています"
        
        incidents = []
        for incident in data['active_incidents']:
            incident_info = f"**{incident['title']}**\n"
            incident_info += f"種類: {incident['type']}\n"
            incident_info += f"影響範囲: {', '.join(incident['services'])}\n"
            if incident.get('notes'):
                incident_info += f"最新情報: {incident['notes'][-1]['body']}\n"
            incidents.append(incident_info)
        
        return "\n\n".join(incidents)

    @check_status.before_loop
    async def before_check_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Slack(bot))
