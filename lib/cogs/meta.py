from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType
from discord.ext.commands import Cog
from discord.ext.commands import command


class Meta(Cog):
	def __init__(self, bot):
		self.bot = bot

		self._message = "watching +help | {users:,} users in {guilds:,} servers"

		bot.scheduler.add_job(self.set, CronTrigger(second=0))

	@property
	def message(self):
		return self._message.format(users=len(self.bot.users), guilds=len(self.bot.guilds))

	@message.setter
	def message(self, value):
		if value.split(" ")[0] not in ("playing", "watching", "listening", "streaming"):
			raise ValueError("Invalid activity type.")

		self._message = value

	async def set(self):
		_type, _name = self.message.split(" ", maxsplit=1)

		await self.bot.change_presence(activity=Activity(
			name=_name, type=getattr(ActivityType, _type, ActivityType.playing)
		))

	@command(name="setactivity")
	async def set_activity_message(self, ctx, *, text: str):
		self.message = text
		await self.set()

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("meta")


def setup(bot):
	bot.add_cog(Meta(bot))