from datetime import datetime, timedelta
from random import randint
from typing import Optional

from discord import Member, Embed
from discord.ext.commands import Cog
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions
from discord.ext.menus import MenuPages, ListPageSource

from ..db import db


class HelpMenu(ListPageSource):
	def __init__(self, ctx, data):
		self.ctx = ctx

		super().__init__(data, per_page=10)

	async def write_page(self, menu, offset, fields=[]):
		len_data = len(self.entries)

		embed = Embed(title="XP Leaderboard",
					  colour=self.ctx.author.colour)
		embed.set_thumbnail(url=self.ctx.guild.icon_url)
		embed.set_footer(text=f"{offset:,} - {min(len_data, offset+self.per_page-1):,} of {len_data:,} members.")

		for name, value in fields:
			embed.add_field(name=name, value=value, inline=False)

		return embed

	async def format_page(self, menu, entries):
		offset = (menu.current_page*self.per_page) + 1

		fields = []
		table = ("\n".join(f"{idx+offset}. {self.ctx.bot.guild.get_member(entry[0]).display_name} (XP: {entry[1]} | Level: {entry[2]})"
				for idx, entry in enumerate(entries)))

		fields.append(("Ranks", table))

		return await self.write_page(menu, offset, fields)


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
			await self.check_lvl_rewards(message, new_lvl)

	async def check_lvl_rewards(self, message, lvl):
		if lvl >= 50: # Red
			if (new_role := message.guild.get_role(653940117680947232)) not in message.author.roles:
				await message.author.add_roles(new_role)
				await message.author.remove_roles(message.guild.get_role(653940192780222515))

		elif 40 <= lvl < 50: # Yellow
			if (new_role := message.guild.get_role(653940192780222515)) not in message.author.roles:
				await message.author.add_roles(new_role)
				await message.author.remove_roles(message.guild.get_role(653940254293622794))

		elif 30 <= lvl < 40: # Green
			if (new_role := message.guild.get_role(653940254293622794)) not in message.author.roles:
				await message.author.add_roles(new_role)
				await message.author.remove_roles(message.guild.get_role(653940277761015809))

		elif 20 <= lvl < 30: # Blue
			if (new_role := message.guild.get_role(653940277761015809)) not in message.author.roles:
				await message.author.add_roles(new_role)
				await message.author.remove_roles(message.guild.get_role(653940305300815882))

		elif 10 <= lvl < 20: # Purple
			if (new_role := message.guild.get_role(653940305300815882)) not in message.author.roles:
				await message.author.add_roles(new_role)
				await message.author.remove_roles(message.guild.get_role(653940328453373952))

		elif 5 <= lvl < 9: # Black
			if (new_role := message.guild.get_role(653940328453373952)) not in message.author.roles:
				await message.author.add_roles(new_role)

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

	@command(name="leaderboard", aliases=["lb"])
	async def display_leaderboard(self, ctx):
		records = db.records("SELECT UserID, XP, Level FROM exp ORDER BY XP DESC")

		menu = MenuPages(source=HelpMenu(ctx, records),
						 clear_reactions_after=True,
						 timeout=60.0)
		await menu.start(ctx)

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.levelup_channel = self.bot.get_channel(759432499221889034)
			self.bot.cogs_ready.ready_up("exp")

	@Cog.listener()
	async def on_message(self, message):
		if not message.author.bot:
			await self.process_xp(message)


def setup(bot):
	bot.add_cog(Exp(bot))