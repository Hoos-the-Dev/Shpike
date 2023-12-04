# basic functions for the economy cog
# ---------------------------------------------
async def create_balance(self, user):
    """Creates a balance for a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("INSERT INTO bank VALUES(? ,? ,? ,?)", (0, 100, 500, user.id))
    await self.db.commit()

async def get_balance(self, user):
    """Returns the wallet, bank and maxbank balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank, maxbank FROM bank WHERE user = ?", (user.id,))
        result = await cursor.fetchone()
        if result is None:
            await create_balance(self, user)
            return 0, 100, 500
        wallet, bank, maxbank = result[0], result[1], result[2]
        return wallet, bank, maxbank

# update_balance, update_bank, update_maxbank
# -------------------------------------------
async def update_balance(self, user, amount: int):
    """Update the wallet balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT wallet FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ? WHERE user = ?", (data[0] + amount, user.id))
    await self.db.commit()

async def update_maxbank(self, user, amount: int):
    """Update the maxbank balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT maxbank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET maxbank = ? WHERE user = ?", (data[0] + amount, user.id))
    await self.db.commit()

async def update_bank(self, user, amount: int):
    """Update the bank balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET bank = ? WHERE user = ?", (data[0] + amount, user.id))
    await self.db.commit()

async def set_bank(self, user, amount:int):
    """Set the users bank (only should be used for owner commands)"""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET bank = ? WHERE user = ?", (amount, user.id))
    await self.db.commit()

async def set_maxbank(self, user, amount:int):
    """Set the users bank (only should be used for owner commands)"""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET maxbank = ? WHERE user = ?", (amount, user.id))
    await self.db.commit()

async def get_maxbank(self, user):
    """Returns the maxbank balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT maxbank FROM bank WHERE user = ?", (user.id,))
        result = await cursor.fetchone()
        if result is None:
            await create_balance(self, user)
            return 500
        maxbank = result[0]
        return maxbank
async def get_bank(self, user):
    """Returns the bank balance of a user."""
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT bank FROM bank WHERE user = ?", (user.id,))
        result = await cursor.fetchone()
        if result is None:
            await create_balance(self, user)
            return 100
        bank = result[0]
        return bank


# withdraw, deposit
# -----------------
async def withdraw(self, user, amount: int):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ?, bank = ? WHERE user = ?", (data[0] + amount, data[1] - amount, user.id))
    await self.db.commit()

async def deposit(self, user, amount: int):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ?, bank = ? WHERE user = ?", (data[0] - amount, data[1] + amount, user.id))
    await self.db.commit()

# transfer
# --------
async def transfer(self, user, target, amount: int):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT wallet, bank FROM bank WHERE user = ?", (user.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, user)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ? WHERE user = ?", (data[0] - amount, user.id))
        await cursor.execute("SELECT wallet, bank FROM bank WHERE user = ?", (target.id,))
        data = await cursor.fetchone()
        if data is None:
            await create_balance(self, target)
            return 0
        await cursor.execute("UPDATE bank SET wallet = ? WHERE user = ?", (data[0] + amount, target.id))
    await self.db.commit()
    
    
# get_inventory, add_item, remove_item
# ------------------------------------

async def create_inventory(self, user):
    async with self.db.cursor() as cursor:
        await cursor.execute("INSERT INTO inventory VALUES(?, ?, ?)", (user.id, "apple", 0))
    await self.db.commit()

async def get_inventory(self, user):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT item, amount FROM inventory WHERE user = ?", (user.id,))
        result = await cursor.fetchall()
        if result is None:
            await create_inventory(self, user)
            return {}
        inventory = {}
        for item in result:
            inventory[item[0]] = item[1]
        return inventory

async def add_item(self, user, item: str, amount: int):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT amount FROM inventory WHERE user = ? AND item = ?", (user.id, item))
        data = await cursor.fetchone()
        if data is None:
            await cursor.execute("INSERT INTO inventory VALUES(?, ?, ?)", (user.id, item, amount))
        else:
            await cursor.execute("UPDATE inventory SET amount = ? WHERE user = ? AND item = ?", (data[0] + amount, user.id, item))
    await self.db.commit()

async def remove_item(self, user, item: str, amount: int):
    async with self.db.cursor() as cursor:
        await cursor.execute("SELECT amount FROM inventory WHERE user = ? AND item = ?", (user.id, item))
        data = await cursor.fetchone()
        if data is None:
            await cursor.execute("INSERT INTO inventory VALUES(?, ?, ?)", (user.id, item, -amount))
        else:
            await cursor.execute("UPDATE inventory SET amount = ? WHERE user = ? AND item = ?", (data[0] - amount, user.id, item))
    await self.db.commit()



async def prevent_overflow(self, user, amount):
    async with self.db.cursor() as cursor:
        wallet, bank, maxbank = await get_balance(self, user)
        amount = int(wallet + bank) - int(maxbank)
        return amount


# conversions

async def get_user(self, user):
    """Returns a discord user object from a user id."""
    return self.bot.get_user(user)

async def convert_abbreviations(ctx, amount: str):
    if "b" in amount:
      amount = amount.replace("b", "")
      try: amount = int(amount) * 1000000000
      except: await ctx.reply("does that look valid to you?")
    if "m" in amount:
      amount = amount.replace("m", "")
      try: amount = int(amount) * 1000000
      except: await ctx.reply("does that look valid to you?")
    if "k" in amount:
      amount = amount.replace("k", "")
      try: amount = int(amount) * 1000
      except: await ctx.reply("does that look valid to you?")  

