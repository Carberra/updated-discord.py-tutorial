from datetime import datetime

from discord import Embed
from discord.ext.commands import Cog

from ..db import db


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
			self.starboard_channel = self.bot.get_channel(724367069004693591)
			self.bot.cogs_ready.ready_up("reactions")

	@Cog.listener()
	async def on_raw_reaction_add(self, payload):
		if self.bot.ready and payload.message_id == self.reaction_message.id:
			current_colours = filter(lambda r: r in self.colours.values(), payload.member.roles)
			await payload.member.remove_roles(*current_colours, reason="Colour role reaction.")
			await payload.member.add_roles(self.colours[payload.emoji.name], reason="Colour role reaction.")
			await self.reaction_message.remove_reaction(payload.emoji, payload.member)

		elif payload.emoji.name == "⭐":
			message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)

			if not message.author.bot and payload.member.id != message.author.id:
				msg_id, stars = db.record("SELECT StarMessageID, Stars FROM starboard WHERE RootMessageID = ?",
										  message.id) or (None, 0)

				embed = Embed(title="Starred message",
							  colour=message.author.colour,
							  timestamp=datetime.utcnow())

				fields = [("Author", message.author.mention, False),
						  ("Content", message.content or "See attachment", False),
						  ("Stars", stars+1, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				if len(message.attachments):
					embed.set_image(url=message.attachments[0].url)

				if not stars:
					star_message = await self.starboard_channel.send(embed=embed)
					db.execute("INSERT INTO starboard (RootMessageID, StarMessageID) VALUES (?, ?)",
							   message.id, star_message.id)

				else:
					star_message = await self.starboard_channel.fetch_message(msg_id)
					await star_message.edit(embed=embed)
					db.execute("UPDATE starboard SET Stars = Stars + 1 WHERE RootMessageID = ?", message.id)

			else:
				await message.remove_reaction(payload.emoji, payload.member)


def setup(bot):
	bot.add_cog(Reactions(bot))