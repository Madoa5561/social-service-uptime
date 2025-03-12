# social-service-uptime
Notifies discord when the status of any service changes, as long as the service has a status.json on its status page

> [!IMPORTANT]
> このbotの不具合が起きる可能性は微レ存です
> エラーハンドリングを細かくしてないので改善の余地があります
> There is a possibility that this bot may have glitches.
> Error handling is not detailed enough, so there is room for improvement.


## install bot
> bot install Link
> https://discord.com/oauth2/authorize?client_id=1349062284961644545&permissions=84992&integration_type=0&scope=bot
> 
> use slashCommand
> /set_channel <Textchannel>
> Embedded notification if there is a problem with the service
> Since status.json is obtained every minute, the information is updated every minute.

## install selfHosting
its example OS:Ubuntu
### first
`python3 -m venv env`

### second
Activate venv

### third
`pip install requests`
`pip install discord`

### Lets Go Runnning
`python3 main.py`
