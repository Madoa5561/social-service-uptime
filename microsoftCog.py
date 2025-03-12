import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, UTC

class Microsoft(commands.Cog):
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
        status_url = "https://admin.microsoft.com/api/servicestatus/index"

        try:
            async with self.session.get(status_url) as response:
                status_data = await response.json()
                if not isinstance(status_data, dict):
                    raise ValueError("Invalid status data format")
                
                is_all_up = status_data.get('IsAllUp')
                if is_all_up is None:
                    raise ValueError("Status indicator not found")
                
                if not is_all_up and not self.is_api_heavy:
                    self.is_api_heavy = True
                    await self.send_notification(status_data)
                    await self.start_status_updates()
                
                elif is_all_up and self.is_api_heavy:
                    self.is_api_heavy = False
                    await self.send_notification(status_data)
                    await self.stop_status_updates()

                if self.is_api_heavy:
                    await self.update_status_message(status_data)

        except Exception as e:
            print(f"Microsoft status check error: {str(e)}")

    async def start_status_updates(self):
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.send("Microsoft状態の監視を開始します...")
                self.status_messages[server_id] = message

    async def stop_status_updates(self):
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(content="Microsoft状態が正常に戻りました。監視を終了します。")
        self.status_messages.clear()

    async def update_status_message(self, status_data):
        embed = discord.Embed(
            title="現在のMicrosoft状態",
            description=self.format_incidents(status_data),
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )
        
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(embed=embed)

    async def send_notification(self, data):
        color = discord.Color.red() if not data['IsAllUp'] else discord.Color.green()
        
        embed = discord.Embed(
            title="Microsoft サービス状態更新",
            description=f"現在のステータス: {'問題発生中' if not data['IsAllUp'] else '正常'}",
            color=color,
            timestamp=datetime.now(UTC)
        )
        
        if not data['IsAllUp']:
            embed.add_field(name="詳細", value=self.format_incidents(data), inline=False)
        embed.set_footer(text="Microsoft Status Monitor")
        
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    def format_incidents(self, data):
        if data['IsAllUp']:
            return "すべてのサービスが正常に動作しています"
        
        incidents = []
        for service in data['Services']:
            if not service['IsUp'] and service['Messages']:
                incident_info = f"**{service['Name']}**\n"
                latest_message = service['Messages'][0]
                incident_info += "\n".join(latest_message['Lines'])
                incidents.append(incident_info)
        
        return "\n\n".join(incidents) if incidents else "問題が発生していますが、詳細情報はありません"

    @check_status.before_loop
    async def before_check_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Microsoft(bot))
