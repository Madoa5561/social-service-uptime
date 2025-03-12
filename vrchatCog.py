import discord
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime, UTC

class VRchat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.check_status.start()
        self.last_status = None
        self.last_metrics = {
            'online_users': None,
            'api_latency': None,
            'api_requests': None,
            'api_errors': None
        }
        self.is_api_heavy = False
        self.status_messages = {}

    def cog_unload(self):
        self.check_status.cancel()
        self.bot.loop.create_task(self.session.close())

    async def fetch_metric(self, url):
        async with self.session.get(url) as response:
            data = await response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[-1]
            return None

    @tasks.loop(minutes=1.0)
    async def check_status(self):
        status_url = "https://status.vrchat.com/api/v2/status.json"
        metrics_urls = {
            'online_users': "https://d31qqo63tn8lj0.cloudfront.net/visits.json",
            'api_latency': "https://d31qqo63tn8lj0.cloudfront.net/apilatency.json",
            'api_requests': "https://d31qqo63tn8lj0.cloudfront.net/apirequests.json",
            'api_errors': "https://d31qqo63tn8lj0.cloudfront.net/apierrors.json"
        }

        try:
            async with self.session.get(status_url) as response:
                status_data = await response.json()
                if not isinstance(status_data, dict):
                    raise ValueError("Invalid status data format")
                
                status = status_data.get('status', {}).get('indicator')
                if status is None:
                    raise ValueError("Status indicator not found")
                
                metrics = {}
                for metric_name, url in metrics_urls.items():
                    metric_data = await self.fetch_metric(url)
                    if metric_data and isinstance(metric_data, dict):
                        value = metric_data.get('value')
                        if value is None:
                            continue
                            
                        if metric_name == 'api_latency':
                            metrics[metric_name] = f"{round(value * 1000, 2)}ms"
                        elif metric_name == 'api_errors':
                            metrics[metric_name] = round(value, 6)
                        elif metric_name == 'api_requests':
                            metrics[metric_name] = f"{round(value):,}"
                        else:
                            metrics[metric_name] = value
                
                if status in ["major", "minor"] and not self.is_api_heavy:
                    self.is_api_heavy = True
                    await self.send_notification(status, status_data, metrics)
                    await self.start_status_updates()
                
                elif status == "none" and self.is_api_heavy:
                    self.is_api_heavy = False
                    await self.send_notification(status, status_data, metrics)
                    await self.stop_status_updates()

                if self.is_api_heavy:
                    await self.update_status_message(status_data, metrics)

        except Exception as e:
            print(f"VRchat status check error: {str(e)}")

    async def start_status_updates(self):
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = await channel.send("API状態の監視を開始します...")
                self.status_messages[server_id] = message

    async def stop_status_updates(self):
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(content="API状態が正常に戻りました。監視を終了します。")
        self.status_messages.clear()

    async def update_status_message(self, status_data, metrics):
        embed = discord.Embed(
            title="現在のAPI状態",
            description=status_data['status']['description'],
            color=discord.Color.blue(),
            timestamp=datetime.now(UTC)
        )
        
        embed.add_field(name="オンラインユーザー", value=metrics['online_users'], inline=True)
        embed.add_field(name="APIレイテンシ", value=metrics['api_latency'], inline=True)
        embed.add_field(name="APIリクエスト", value=metrics['api_requests'], inline=True)
        embed.add_field(name="APIエラー率", value=metrics['api_errors'], inline=True)
        
        for server_id, message in self.status_messages.items():
            if message:
                await message.edit(embed=embed)

    async def send_notification(self, status, data, metrics):
        color_map = {
            "major": discord.Color.red(),
            "minor": discord.Color.gold(),
            "none": discord.Color.green()
        }
        
        embed = discord.Embed(
            title="VRchat サーバー状態更新",
            description=f"現在のステータス: {status}",
            color=color_map.get(status, discord.Color.blue()),
            timestamp=datetime.now(UTC)
        )
        
        embed.add_field(name="詳細", value=data['status']['description'], inline=False)
        embed.add_field(name="オンラインユーザー", value=metrics['online_users'], inline=True)
        embed.add_field(name="APIレイテンシ", value=metrics['api_latency'], inline=True)
        embed.add_field(name="APIリクエスト", value=metrics['api_requests'], inline=True)
        embed.add_field(name="APIエラー率", value=metrics['api_errors'], inline=True)
        embed.set_footer(text="VRchat Status Monitor")
        
        for server_id, channel_id in self.bot.config.items():
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    @check_status.before_loop
    async def before_check_status(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(VRchat(bot))
