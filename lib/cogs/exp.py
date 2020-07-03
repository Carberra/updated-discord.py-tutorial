from datetime import datetime, timedelta
from random import randint
from typing import Optional

from discord import Member
from discord.ext.commands import Cog
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions

from ..db import db

class Exp(Cog):
	def __init__(self, bot):
		self.bot = bot

	async def process_xp(self, message):
		xp, lvl, xplock = db.record("SELECT XP, Level, XPLock FROM exp WHERE UserID = ?", message.author.id)

		if datetime.utcnow() > datetime.fromisoformat(xplock):
			await self.add_xp(message, xp, lvl)

	async def add_xp(self, message, xp, lvl):
		xp_to_add = randint(10, 20)
		new_lvl = int(((xp+xp_to_add)//42) ** 0.55)

		db.execute("UPDATE exp SET XP = XP + ?, Level = ?, XPLock = ? WHERE UserID = ?",
				   xp_to_add, new_lvl, (datetime.utcnow()+timedelta(seconds=60)).isoformat(), message.author.id)

		if new_lvl > lvl:
			await self.levelup_channel.send(f"Congrats {message.author.mention} - you reached level {new_lvl:,}!")

	@command(name="level")
	async def display_level(self, ctx, target: Optional[Member]):
		target = target or ctx.author

		xp, lvl = db.record("SELECT XP, Level FROM exp WHERE UserID = ?", target.id) or (None, None)

		if lvl is not None:
			await ctx.send(f"{target.display_name} is on level {lvl:,} with {xp:,} XP.")

		else:
			await ctx.send("That member is not tracked by the experience system.")

	@command(name="rank")
	async def display_rank(self, ctx, target: Optional[Member]):
		target = target or ctx.author

		ids = db.column("SELECT UserID FROM exp ORDER BY XP DESC")

		try:
			await ctx.send(f"{target.display_name} is rank {ids.index(target.id)+1} of {len(ids)}.")

		except ValueError:
			await ctx.send("That member is not tracked by the experience system.")

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.levelup_channel = self.bot.get_channel(728350312154398740)
			self.bot.cogs_ready.ready_up("exp")

	@Cog.listener()
	async def on_message(self, message):
		if not message.author.bot:
			await self.process_xp(message)


def setup(bot):
	bot.add_cog(Exp(bot))