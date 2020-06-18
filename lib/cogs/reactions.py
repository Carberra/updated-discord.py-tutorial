from discord.ext.commands import Cog


class Reactions(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("reactions")

	@Cog.listener()
	async def on_reaction_add(self, reaction, user):
		print(f"{user.display_name} reacted with {reaction.emoji.name}")

	@Cog.listener()
	async def on_reaction_remove(self, reaction, user):
		print(f"{user.display_name} removed their reaction of {reaction.emoji.name}")

	@Cog.listener()
	async def on_raw_reaction_add(self, payload):
		print(f"[RAW] {payload.member.display_name} reacted with {payload.emoji.name}")

	@Cog.listener()
	async def on_raw_reaction_remove(self, payload):
		member = self.bot.guild.get_member(payload.user_id)
		print(f"[RAW] {member.display_name} removed their reaction of {payload.emoji.name}")


def setup(bot):
	bot.add_cog(Reactions(bot))