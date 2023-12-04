import nextcord
from nextcord.ext import commands
from nextcord import Interaction
from urllib import response
from nextcord import Member, Embed, Color
from nextcord.ext import commands, application_checks
from nextcord import Interaction, SlashOption, slash_command
from nextcord.ext.commands import command, Cog, cooldown, BucketType
import asyncio
import requests
import random
from random import randint
import humanfriendly
import aiohttp
from urllib3 import Retry
from resources.functions import *
from resources.iio import *
from lib import console
import aiosqlite
from resources.marriage import * 


class Marriage(commands.Cog):
  def __init__(self, bot):
      self.bot = bot

  @Cog.listener()
  async def on_ready(self):
    self.marriage_db = await aiosqlite.connect("resources/data/marriage.db")
    await self.marriage_db.execute("CREATE TABLE IF NOT EXISTS marriage (user1 INTERGER, user2 INTERGER, married BOOLEAN, married_since TEXT)")
    await self.marriage_db.commit()
    console.info("Marriage database connected")

  @command(name="marry", description="Marry someone")
  async def marry(self, ctx: commands.Context, user:Member):
    if user == ctx.author:
      return await ctx.send("i pronounce you... lonely asf")
    if user.bot:
      return await ctx.send("bots cant consent!")
    if B_CheckBlacklist(self, user):
      return await ctx.send("you cant marry a blacklisted user!")
    if B_CheckBlacklist(self, ctx.author):
      return await ctx.send("you blacklisted")

    if user.id == await get_marriage_partner(self, user=ctx.author):
      embed = Embed(title="Wait a minute", description=f"you're Already married to {user.mention}")
      await ctx.reply(embed=embed)
      return
    if await get_marriage(self, ctx.author) != False:
      partner = await get_marriage_partner(self, ctx.author)
      partner = self.bot.get_user(partner)
      em = Embed(title="📸", description=f"you are already married to {partner.mention}", color=Color.red())
      try: await partner.send(f"yo homie, {ctx.author.mention} is trying to marry someone else in <#{ctx.channel.id}>!")
      except: pass
      return await ctx.send(embed=em)
    if await get_marriage(self, user) != False:
      partner = await get_marriage_partner(self, user)
      partner = self.bot.get_user(partner)
      return await ctx.send(f"{user.mention} is already married to {partner.mention}")
    
    embed = Embed(title="Proposal!", description=f"{ctx.author.mention} has proposed to {user.mention}! Do you accept?", color=Color.orange())
    msg = await ctx.send(user.mention,embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    usr = user
    try:
      def check(reaction, user):
        return user == usr and str(reaction.emoji) in ["✅", "❌"]
      reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
    except asyncio.TimeoutError:
      embed = Embed(title="yikes", description=f"{user.mention} didnt respond to your proposal {ctx.author.mention}!", color=Color.red())
      await msg.edit(embed=embed)
      return
    if str(reaction.emoji) == "✅":
      await marry(self, ctx.author, user)
      embed = Embed(title="yay", description=f"{user.mention} accepted your proposal {ctx.author.mention}!", color=Color.green())
      embed.set_footer(text="Clap it up everyone!")
      await msg.edit(embed=embed)
      embed = Embed(description="congrats!, you're married now", color=Color.green())
      await ctx.send(ctx.author.mention, embed=embed)
      return
    else:
      embed = Embed(title="yikes", description=f"{user.mention} rejected your proposal, {ctx.author.mention}!", color=Color.red())
      await msg.edit(ctx.author.mention,embed=embed)
      embed = Embed(description="better luck next time!", color=Color.red())
      await ctx.send(ctx.author.mention, embed=embed)
      return

  @command(name="divorce", description="Divorce your partner")
  async def divorce(self, ctx: commands.Context):
    if await get_marriage(self, ctx.author) == False:
      return await ctx.send("you are not married!")
    partner = await get_marriage_partner(self, ctx.author)
    partner = self.bot.get_user(partner)
    try: await divorce(self, ctx.author, partner)
    except: await divorce(self, partner, ctx.author)
    embed = Embed(description="you are now divorced", color=Color.red())
    await ctx.send(ctx.author.mention, embed=embed)
    embed = Embed(description=f"{ctx.author.mention} has divorced you!", color=Color.red())
    await ctx.send(partner.mention, embed=embed)
    return
  @command(name="marriage", description="Check your marriage status")
  async def marriage(self, ctx: commands.Context, user:Member=None):
    if user == None:
      user = ctx.author
    if await get_marriage(self, user) == False:
      return await ctx.send(f"{user.mention} is not married!")
    partner = await get_marriage_partner(self, user)
    partner = self.bot.get_user(partner)
    married_since = await get_marriage_since(self, partner)
    embed = Embed(title="Marriage 📜", description=f"{user.mention} is married to {partner.mention}\n\n Married since: {married_since} ", color=Color.green())
    await ctx.send(user.mention, embed=embed)
    return
  
  @command(name="marriageleaderboard", description="Check the marriage leaderboard")
  async def marriageleaderboard(self, ctx: commands.Context):
    async with self.db.cursor() as cursor:
      await cursor.execute("SELECT user1 FROM marriage")
      result = await cursor.fetchall()
      if result is None:
        return await ctx.send("no one is married!")
      married = result
      married = len(married)
      embed = Embed(title="Marriage Leaderboard 📜", description=f"there are {married} married couples!", color=Color.green())
      await ctx.send(embed=embed)
      return
  
  @command(name="marriagelist", description="Check the marriage list")
  async def marriagelist(self, ctx: commands.Context):
    async with self.db.cursor() as cursor:
      await cursor.execute("SELECT user1 FROM marriage")
      result = await cursor.fetchall()
      if result is None:
        return await ctx.send("no one is married!")
      married = result
      embed = Embed(title="Marriage List 📜", description=f"here are the married couples!", color=Color.green())
      for i in married:
        user = self.bot.get_user(i[0])
        partner = await get_marriage_partner(self, user)
        partner = self.bot.get_user(partner)
        embed.add_field(name=f"{user.name}", value=f"{partner.mention}", inline=False)
      await ctx.send(embed=embed)
      return

      
    

def setup(bot):
    bot.add_cog(Marriage(bot)) 