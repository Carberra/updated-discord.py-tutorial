from discord.ext.commands import Cog


class Reactions(Cog):
	def __init__(self, bot):
		self.bot = bot

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.colours = {
				"❤️": self.bot.guild.get_role(653940117680947232), # Red
				"💛": self.bot.guild.get_role(653940192780222515), # Yellow
				"💚": self.bot.guild.get_role(653940254293622794), # Green
				"💙": self.bot.guild.get_role(653940277761015809), # Blue
				"💜": self.bot.guild.get_role(653940305300815882), # Purple
				"🖤": self.bot.guild.get_role(653940328453373952), # Black
			}
			self.reaction_message = await self.bot.get_channel(723257328819896390).fetch_message(723258202090635285)
			self.bot.cogs_ready.ready_up("reactions")

	# @Cog.listener()
	# async def on_reaction_add(self, reaction, user):
	# 	print(f"{user.display_name} reacted with {reaction.emoji.name}")

	# @Cog.listener()
	# async def on_reaction_remove(self, reaction, user):
	# 	print(f"{user.display_name} removed their reaction of {reaction.emoji.name}")

	@Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if self.bot.ready and payload.message_id == self.reaction_message.id:
			current_colours = filter(lambda r: r in self.colours.values(), payload.member.roles)
			await payload.member.remove_roles(*current_colours, reason="Colour role reaction.")
			await payload.member.add_roles(self.colours[payload.emoji.name], reason="Colour role reaction.")
			await self.reaction_message.remove_reaction(payload.emoji, payload.member)

	# @Cog.listener()
	# async def on_raw_reaction_remove(self, payload):
	# 	if self.bot.ready and payload.message_id == self.reaction_message.id:
	# 		member = self.bot.guild.get_member(payload.user_id)
	# 		await member.remove_roles(self.colours[payload.emoji.name], reason="Colour role reaction.")


def setup(bot):
	bot.add_cog(Reactions(bot))