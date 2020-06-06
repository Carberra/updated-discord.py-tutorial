from asyncio import sleep
from datetime import datetime, timedelta
from re import search
from typing import Optional

from better_profanity import profanity
from discord import Embed, Member
from discord.ext.commands import Cog, Greedy
from discord.ext.commands import CheckFailure
from discord.ext.commands import command, has_permissions, bot_has_permissions

from ..db import db

profanity.load_censor_words_from_file("./data/profanity.txt")


class Mod(Cog):
	def __init__(self, bot):
		self.bot = bot

		self.url_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
		self.links_allowed = (711223407911370812, 711246048756236348)
		self.images_allowed = (711223407911370812, 711246048756236348)

	@command(name="kick")
	@bot_has_permissions(kick_members=True)
	@has_permissions(kick_members=True)
	async def kick_members(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")

		else:
			for target in targets:
				if (ctx.guild.me.top_role.position > target.top_role.position 
					and not target.guild_permissions.administrator):
					await target.kick(reason=reason)

					embed = Embed(title="Member kicked",
								  colour=0xDD2222,
								  timestamp=datetime.utcnow())

					embed.set_thumbnail(url=target.avatar_url)

					fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False),
							  ("Actioned by", ctx.author.display_name, False),
							  ("Reason", reason, False)]

					for name, value, inline in fields:
						embed.add_field(name=name, value=value, inline=inline)
					
					await self.log_channel.send(embed=embed)

				else:
					await ctx.send(f"{target.display_name} could not be kicked.")

			await ctx.send("Action complete.")

	@kick_members.error
	async def kick_members_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("Insufficient permissions to perform that task.")

	@command(name="ban")
	@bot_has_permissions(ban_members=True)
	@has_permissions(ban_members=True)
	async def ban_members(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")

		else:
			for target in targets:
				if (ctx.guild.me.top_role.position > target.top_role.position 
					and not target.guild_permissions.administrator):
					await target.ban(reason=reason)

					embed = Embed(title="Member banned",
								  colour=0xDD2222,
								  timestamp=datetime.utcnow())

					embed.set_thumbnail(url=target.avatar_url)

					fields = [("Member", f"{target.name} a.k.a. {target.display_name}", False),
							  ("Actioned by", ctx.author.display_name, False),
							  ("Reason", reason, False)]

					for name, value, inline in fields:
						embed.add_field(name=name, value=value, inline=inline)
					
					await self.log_channel.send(embed=embed)

				else:
					await ctx.send(f"{target.display_name} could not be banned.")

			await ctx.send("Action complete.")

	@ban_members.error
	async def ban_members_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("Insufficient permissions to perform that task.")

	@command(name="clear", aliases=["purge"])
	@bot_has_permissions(manage_messages=True)
	@has_permissions(manage_messages=True)
	async def clear_messages(self, ctx, targets: Greedy[Member], limit: Optional[int] = 1):
		def _check(message):
			return not len(targets) or message.author in targets

		if 0 < limit <= 100:
			with ctx.channel.typing():
				await ctx.message.delete()
				deleted = await ctx.channel.purge(limit=limit, after=datetime.utcnow()-timedelta(days=14),
												  check=_check)

				await ctx.send(f"Deleted {len(deleted):,} messages.", delete_after=5)

		else:
			await ctx.send("The limit provided is not within acceptable bounds.")

	@command(name="mute")
	@bot_has_permissions(manage_roles=True)
	@has_permissions(manage_roles=True, manage_guild=True)
	async def mute_members(self, ctx, targets: Greedy[Member], hours: Optional[int], *,
						   reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments are missing.")

		else:
			unmutes = []

			for target in targets:
				if not self.mute_role in target.roles:
					if ctx.guild.me.top_role.position > target.top_role.position:
						role_ids = ",".join([str(r.id) for r in target.roles])
						end_time = datetime.utcnow() + timedelta(seconds=hours) if hours else None

						db.execute("INSERT INTO mutes VALUES (?, ?, ?)",
								   target.id, role_ids, getattr(end_time, "isoformat", lambda: None)())

						await target.edit(roles=[self.mute_role])

						embed = Embed(title="Member muted",
									  colour=0xDD2222,
									  timestamp=datetime.utcnow())

						embed.set_thumbnail(url=target.avatar_url)

						fields = [("Member", target.display_name, False),
								  ("Actioned by", ctx.author.display_name, False),
								  ("Duration", f"{hours:,} hour(s)" if hours else "Indefinite", False),
								  ("Reason", reason, False)]

						for name, value, inline in fields:
							embed.add_field(name=name, value=value, inline=inline)
						
						await self.log_channel.send(embed=embed)

						if hours:
							unmutes.append(target)

					else:
						await ctx.send(f"{target.display_name} could not be muted.")

				else:
					await ctx.send(f"{target.display_name} is already muted.")

			await ctx.send("Action complete.")

			if len(unmutes):
				await sleep(hours)
				await self.unmute(ctx.guild, targets)

	@mute_members.error
	async def mute_members_error(self, ctx, exc):
		if isinstance(exc, CheckFailure):
			await ctx.send("Insufficient permissions to perform that task.")

	async def unmute(self, guild, targets, *, reason="Mute time expired."):
		for target in targets:
			if self.mute_role in target.roles:
				role_ids = db.field("SELECT RoleIDs FROM mutes WHERE UserID = ?", target.id)
				roles = [guild.get_role(int(id_)) for id_ in role_ids.split(",") if len(id_)]

				db.execute("DELETE FROM mutes WHERE UserID = ?", target.id)

				await target.edit(roles=roles)

				embed = Embed(title="Member unmuted",
							  colour=0xDD2222,
							  timestamp=datetime.utcnow())

				embed.set_thumbnail(url=target.avatar_url)

				fields = [("Member", target.display_name, False),
						  ("Reason", reason, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)
				
				await self.log_channel.send(embed=embed)

	@command(name="unmute")
	@bot_has_permissions(manage_roles=True)
	@has_permissions(manage_roles=True, manage_guild=True)
	async def unmute_members(self, ctx, targets: Greedy[Member], *, reason: Optional[str] = "No reason provided."):
		if not len(targets):
			await ctx.send("One or more required arguments is missing.")

		else:
			await self.unmute(ctx.guild, targets, reason=reason)

	@command(name="addprofanity", aliases=["addswears", "addcurses"])
	@has_permissions(manage_guild=True)
	async def add_profanity(self, ctx, *words):
		with open("./data/profanity.txt", "a", encoding="utf-8") as f:
			f.write("".join([f"{w}\n" for w in words]))

		profanity.load_censor_words_from_file("./data/profanity.txt")
		await ctx.send("Action complete.")

	@command(name="delprofanity", aliases=["delswears", "delcurses"])
	@has_permissions(manage_guild=True)
	async def remove_profanity(self, ctx, *words):
		with open("./data/profanity.txt", "r", encoding="utf-8") as f:
			stored = [w.strip() for w in f.readlines()]

		with open("./data/profanity.txt", "w", encoding="utf-8") as f:
			f.write("".join([f"{w}\n" for w in stored if w not in words]))

		profanity.load_censor_words_from_file("./data/profanity.txt")
		await ctx.send("Action complete.")

	@Cog.listener()
	async def on_ready(self):
		if not self.bot.ready:
			self.log_channel = self.bot.get_channel(711246048756236348)
			self.mute_role = self.bot.guild.get_role(653941858128494600)

			unmutes = []
			active_mutes = db.records("SELECT UserID, EndTime FROM mutes")

			for userid, endtime in active_mutes:
				if endtime and datetime.utcnow() > (et := datetime.fromisoformat(endtime)):
					unmutes.append(self.bot.guild.get_member(userid))

				else:
					self.bot.scheduler.add_job(self.unmute, "date", run_date=et,
											   args=[self.bot.guild, [self.bot.guild.get_member(userid)]])

			if len(unmutes):
				await self.unmute(self.bot.guild, unmutes)

			self.bot.cogs_ready.ready_up("mod")

	@Cog.listener()
	async def on_message(self, message):
		if not message.author.bot:
			if profanity.contains_profanity(message.content):
				await message.delete()
				await message.channel.send("You can't use that word here.", delete_after=10)

			elif message.channel.id not in self.links_allowed and search(self.url_regex, message.content):
				await message.delete()
				await message.channel.send("You can't send links in this channel.", delete_after=10)

			if (message.channel.id not in self.images_allowed
				and any([hasattr(a, "width") for a in message.attachments])):
				await message.delete()
				await message.channel.send("You can't send images here.", delete_after=10)


def setup(bot):
	bot.add_cog(Mod(bot))