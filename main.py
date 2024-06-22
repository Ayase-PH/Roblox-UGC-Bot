import os, re, json, discord, requests, traceback, datetime, iso8601, random
from discord.ext.commands import cooldown, BucketType
from discord.ext import commands
from functools import wraps

class CustomBot(commands.Bot):
    assettypes = {
        1: "Image", 2: "T-Shirt", 3: "Audio", 4: "Mesh", 5: "Lua", 6: "HTML", 7: "Text", 8: "Hat", 9: "Place", 
        10: "Model", 11: "Shirt", 12: "Pants", 13: "Decal", 16: "Avatar", 17: "Head", 18: "Face", 19: "Gear", 
        21: "Badge", 22: "Group Emblem", 24: "Animation", 25: "Arms", 26: "Legs", 27: "Torso", 28: "Right Arm", 
        29: "Left Arm", 30: "Left Leg", 31: "Right Leg", 32: "Package", 33: "YouTube Video", 34: "GamePass", 
        35: "App", 37: "Code", 38: "Plugin", 39: "Solid Model", 40: "Mesh Part", 41: "Hair Accessory", 
        42: "Face Accessory", 43: "Neck Accessory", 44: "Shoulder Accessory", 45: "Front Accessory", 
        46: "Back Accessory", 47: "Waist Accessory", 48: "Climb Animation", 49: "Death Animation", 
        50: "Fall Animation", 51: "Idle Animation", 52: "Jump Animation", 53: "Run Animation", 
        54: "Swim Animation", 55: "Walk Animation", 56: "Pose Animation", 57: "Ear Accessory", 
        58: "Eye Accessory", 59: "Localization Table Manifest", 60: "Localization Table Translation", 
        61: "Emote Animation", 62: "Video", 63: "Texture Pack", 64: "T-Shirt Accessory", 65: "Shirt Accessory", 
        66: "Pants Accessory", 67: "Jacket Accessory", 68: "Sweater Accessory", 69: "Shorts Accessory", 
        70: "Left Shoe Accessory", 71: "Right Shoe Accessory", 72: "Dress Skirt Accessory", 73: "Font Family", 
        74: "Font Face", 75: "Mesh Hidden Surface Removal", 76: "Eyebrow Accessory", 77: "Eyelash Accessory", 
        78: "Mood Animation", 79: "Dynamic Head", 80: "Code Snippet",
    }

    def __init__(self):
        self.config = self.load_config('configuration.json')
        self.prefix = self.config["command_prefix"]
        self.token = self.config["token"]

        self.session = requests.session()
        self.session.cookies['.ROBLOSECURITY'] = self.config["cookie"]

        super().__init__(command_prefix=self.prefix, intents=discord.Intents.all())

    def load_config(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    
    def item_embed(self, details_data, item_id):
        name = details_data.get("Name")
        creator = details_data.get("Creator", {}).get("Name")
        price_in_robux = details_data.get("PriceInRobux")
        descriptionitem = details_data.get("Description")
        
        creation = details_data.get("Created")
        creationdiscord_timestampTR = self.format_timestamp(creation)
        creationdiscord_timestampT = self.format_timestamp(creation)
        update = details_data.get("Updated")
        updatediscord_timestampTR = self.format_timestamp(update)
        updatediscord_timestampT = self.format_timestamp(update)

        total_quantity = details_data.get("CollectiblesItemDetails", {}).get("TotalQuantity", 0) if details_data.get("CollectiblesItemDetails") else None
        remaining = details_data.get("Remaining")
        
        asset_type = self.assettypes.get(details_data.get('AssetTypeId'))
        quantity_limit = details_data.get('CollectiblesItemDetails', {}).get('CollectibleQuantityLimitPerUser', "None") if details_data.get('CollectiblesItemDetails') else None
        
        embed = discord.Embed(description=f"# [{name}](https://www.roblox.com/catalog/{item_id}/) \n**Creator:** {creator} \n**Accessory Type:** {asset_type} \n**Description:** \n ```{descriptionitem} ```")
        embed.set_thumbnail(url=self.get_thumbnail_url(item_id))
        embed.set_footer(text=self.footer_text(), icon_url=bot.user.avatar.with_format('png'))
        embed.timestamp = datetime.datetime.now()
        
        embed.add_field(
            name="**Price Information**",
            value=f"> **Original Price**: {price_in_robux} \n> **Lowest Resale Price**: {details_data.get('CollectiblesItemDetails', {}).get('CollectibleLowestResalePrice', 0)}" if details_data.get('CollectiblesItemDetails') else "",
            inline=False
        )
        
        embed.add_field(
            name="**Time Information**",
            value=f"> **Created**: {creationdiscord_timestampTR} | {creationdiscord_timestampT} \n> **Last Updated**: {updatediscord_timestampTR} | {updatediscord_timestampT}",
            inline=False
        )
        
        if asset_type == "Place" and not remaining is None and not total_quantity is None and total_quantity != 0:
            given_percent, remaining_percent = self.calculate_percentages(remaining, total_quantity)
            embed.add_field(
                name="**Stock Info**",
                value=f"> Remaining: {remaining}/{total_quantity} \n> Percentage Left: {given_percent:.1f}% | ({remaining} left) \n> Percentage Sold: {remaining_percent:.1f}% | ({total_quantity - remaining} sold)",
                inline=False
            )
        
        return embed 
    
    def get_thumbnail_url(self, item_id):
        thumbnail_url = f"https://thumbnails.roblox.com/v1/assets?assetIds={item_id}&returnPolicy=PlaceHolder&size=150x150&format=Png"
        response = self.session.get(thumbnail_url)
        if response.status_code == 200:
            thumbnail_data = response.json()
            return thumbnail_data["data"][0]["imageUrl"]
        return ""
    
    def get_item_details(self, item_id):
        details_url = f"https://economy.roblox.com/v2/assets/{item_id}/details"
        response = self.session.get(details_url)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_game_data(self, game_id):
        gameuniverse_url = f"https://games.roblox.com/v1/games?universeIds={game_id}"
        response = self.session.get(gameuniverse_url)
        if response.status_code == 200:
            game_data = response.json()
            return game_data
        return None

    def parse_item_id(self, item_id1):
        if "catalog/" in item_id1:
            item_id = item_id1.split("/catalog/")[1].split("/")[0]
        elif "item/" in item_id1:
            item_id = item_id1.split("/item/")[1].split("/")[0]
        elif "games/" in item_id1:
            item_id = item_id1.split("/games/")[1].split("/")[0]
        else:
            item_id = item_id1

        return item_id
    
    # def uwu_converter(self, message):
    #     uwu_message = (
    #         re.sub(r'(r|l)', 'w', message, flags=re.IGNORECASE)
    #         .replace('n([aeiou])', 'ny$1')
    #         .replace('N([aeiou])', 'Ny$1')
    #         .replace('N', 'Ny')
    #         .replace('n', 'ny')
    #         .replace(r'([.!?])\s', r'\1~')
    #         .replace(r'([.!?])\n', r'\1~\n')
    #     )
    #     uwu_emojis = [":3", ";3", "OwO", "UwU", "OvO", "ÒwÓ", "0v0", "ÕwÕ", "0w0", "~v~", "~w~"]
    #     random_emoji = random.choice(uwu_emojis)
    #     uwu_message += f'~ {random_emoji}'
    #     return uwu_message
    
    def format_timestamp(self, timestamp):
        dt_object = iso8601.parse_date(timestamp)
        return f"<t:{int(dt_object.timestamp())}:R> | <t:{int(dt_object.timestamp())}>"

    def footer_text(self):
        return 'Footer Placeholder'
    
    @staticmethod
    def cmd_logger(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            try:
                await func(ctx, *args, **kwargs)
                print(f"> [SUCCESS] {ctx.author} used the `{ctx.command}` command in {ctx.guild.name}")
            except Exception as e:
                print(f"> [FAILED] {ctx.author} used the `{ctx.command}` command in {ctx.guild.name}")
                traceback.print_exc()
        return wrapper
    
    async def error_embed(self, ctx, message):
            embed = discord.Embed(description=message, color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)

    async def on_ready(self):
        print(f"Logged in as `{self.user}`")
        print(f'Total Guilds: {len(self.guilds)}')
        print('Guilds:')
        for guild in self.guilds:
            print(f'- {guild.name} ({len(guild.members)} members)')
            
bot = CustomBot()

## Information Command
@bot.command()
@commands.cooldown(1, 14, commands.BucketType.user)
@CustomBot.cmd_logger
async def info(ctx, *, item_id1: str):
    try:
        item_id = bot.parse_item_id(item_id1)

        if not item_id:
            await bot.error_embed("Please provide an item link or item ID...")
            return

        details_data = bot.get_item_details(item_id)

        if details_data:
            embed = bot.item_embed(details_data, item_id)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await bot.error_embed("Failed to retrieve item details.")

    except Exception as e:
        traceback.print_exc()
        await bot.error_embed("Error occurred or invalid item ID. ")


## Stock Command
@bot.command()
@commands.cooldown(1, 14, commands.BucketType.user)
@CustomBot.cmd_logger
async def stock(ctx, *, item_id1: str):
    def calculate_percentages(value, total):
        if total != 0:
            given_percentage = (value / total) * 100
            remaining_percentage = 100 - given_percentage
            return given_percentage, remaining_percentage

    try:
        item_id = bot.parse_item_id(item_id1)

        if not item_id:
            await bot.error_embed(ctx, "Please provide an item link or item ID...")
            return

        details_data = bot.get_item_details(item_id)

        if details_data:
            name = details_data.get("Name")
            creator = details_data.get("Creator", {}).get("Name")
            total_quantity = details_data.get("CollectiblesItemDetails", {}).get("TotalQuantity", 0)
            remaining = details_data.get("Remaining", 0)

            embed = discord.Embed(
                description=f"# [{name}](https://www.roblox.com/catalog/{item_id}/) \n**Creator:** {creator}"
            )    
            embed.set_footer(text=bot.footer_text(), icon_url=bot.user.avatar.with_format('png'))
            embed.set_thumbnail(url=bot.get_thumbnail_url(item_id))
            embed.timestamp = datetime.datetime.now()
            
            if total_quantity:
                given_percent, remaining_percent = calculate_percentages(remaining, total_quantity)
                embed.add_field(
                    name="**Stock Info**",
                    value=f"> Remaining: {remaining}/{total_quantity}\n" +
                          f"> Left: {given_percent:.1f}% | ({str(remaining)} left)\n" +
                          f"> Sold: {remaining_percent:.1f}% | ({str(total_quantity-remaining)} sold)",
                    inline=False
                )

            await ctx.reply(embed=embed, mention_author=False)
        else:
            await bot.error_embed(ctx, "Failed to retrieve item details.")

    except Exception as e:
        traceback.print_exc()
        await bot.error_embed("Error occurred or invalid item ID.")


## VIP Command
@bot.command()
@commands.cooldown(1, 14, commands.BucketType.user)
@CustomBot.cmd_logger
async def convertvip(ctx, vip_link: str):
    url = str(vip_link)
    response = bot.session.get(url)
    embed = discord.Embed(
        title="For Mobile Players",
        description=f"Your Final Link for The VIP: [Click Here](<" + str(response.url) + ">)",
    )
    embed.set_footer(text=bot.footer_text(), icon_url=bot.user.avatar.with_format('png'))
    embed.timestamp = datetime.datetime.now()

    await ctx.reply(embed=embed, mention_author=False)
  
    if vip_link is None: 
        await bot.error_embed(ctx, "Please put a VIP Link with the new format.")


# Global Error Handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await bot.error_embed(ctx, "You do not have permission to use this command.")
        
    elif isinstance(error, commands.BotMissingPermissions):
        await bot.error_embed(ctx, "I do not have permission to perform this action.")

    elif isinstance(error, commands.CommandOnCooldown):
        await bot.error_embed(ctx, f'This command is on cooldown. Please try again in {error.retry_after:.0f}s.')
    

    elif isinstance(error, commands.MissingRequiredArgument):
        await bot.error_embed(ctx, f"Missing a required argument for this command. Check `{bot.prefix}help {ctx.command}` for more info.")
        
    elif isinstance(error, commands.BadArgument):
        await bot.error_embed(ctx, f"Invalid argument format. Check `{bot.prefix}help {ctx.command}` for more info.")

bot.run(bot.token)