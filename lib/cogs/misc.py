from discord import Member
from discord.ext.commands import Cog, Greedy
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions

from ..db import db

class Misc(Cog):
	def __init__(self, bot):
		self.bot = bot

	@command(name="prefix")
	@has_permissions(manage_guild=True)
	async def change_prefix(self, ctx, new: str):
		if len(new) > 5:
			await ctx.send("The prefix can not be more than 5 characters in length.")

		else:
			db.execute("UPDATE guilds SET Prefix = ? WHERE GuildID = ?", new, ctx.guild.id)
			await ctx.send(f"Prefix set to {new}.")

	@change_prefix.error
	async def change_prefix_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("You need the Manage Server permission to do that.")

	@command(name="addban")
	@has_permissions(manage_guild=True)
	async def addban_command(self, ctx, targets: Greedy[Member]):
		if not targets:
			await ctx.send("No targets specified.")

		else:
			self.bot.banlist.extend([t.id for t in targets])
			await ctx.send("Done.")

	@command(name="delban", aliases=["rmban"])
	@has_permissions(manage_guild=True)
	async def delban_command(self, ctx, targets: Greedy[Member]):
		if not targets:
			await ctx.send("No targets specified.")

		else:
			for target in targets:
				self.bot.banlist.remove(target.id)
			await ctx.send("Done.")

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.bot.cogs_ready.ready_up("misc")


def setup(bot):
	bot.add_cog(Misc(bot))