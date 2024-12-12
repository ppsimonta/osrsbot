import requests
import mwparserfromhell
import discord
from discord.ext import commands

TOKEN = 'Your token'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Funktio, joka hakee kaikki bossit Category:Bosses-kategoriasta
def get_all_bosses():
    custom_agent = {
        'User-Agent': 'pera',
        'From': 'perttu.simontaival@gmail.com'
    }
    parameters = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': 'Category:Bosses',
        'format': 'json',
        'cmtype': 'page',
        'cmlimit': 'max'
    }

    result = requests.get("https://oldschool.runescape.wiki/api.php", headers=custom_agent, params=parameters).json()

    if 'query' not in result:
        return "Pyyntö ei tuottanut tuloksia."

    bosses = []

    for page in result['query']['categorymembers']:
        bosses.append(page['title'])

    return bosses


# Funktio, joka hakee bossit, jotka alkavat tietyllä kirjaimella
def get_bosses_by_letter(bosses, letter):
    filtered_bosses = [boss for boss in bosses if boss.lower().startswith(letter.lower())]
    return filtered_bosses


def get_boss_details(boss_name):
    custom_agent = {
        'User-Agent': 'pera',
        'From': 'perttu.simontaival@gmail.com'
    }

    small_words = {'of', 'the', 'archaeologist', 'deathless', 'twisted', 'maledictus', 'brothers', 'demon', 'kill', 'spirit', 'golem'}

    boss = "_".join(
        word.lower() if word.lower() in small_words else word[0].upper() + word[1:].lower()
        for word in boss_name.strip().split()
    )

    parameters = {
        'action': 'parse',
        'prop': 'wikitext',
        'format': 'json',
        'page': boss
    }

    result = requests.get("https://oldschool.runescape.wiki/api.php", headers=custom_agent, params=parameters).json()

    if 'parse' not in result:
        return "Pyyntö ei tuottanut tuloksia."

    data = result['parse']['wikitext']['*'].encode('utf-8')

    wikicode = mwparserfromhell.parse(data)

    result_details = ""

    templates = wikicode.filter_templates()

    seen_attributes = set()

    for template in templates:
        template_name = template.name.strip().lower()

        if "infobox monster" in template_name:
            attributes = {
                "Stab": template.get("dstab").value.strip() if template.has("dstab") and template.get("dstab").value.strip() != "N/A" else None,
                "Slash": template.get("dslash").value.strip() if template.has("dslash") and template.get("dslash").value.strip() != "N/A" else None,
                "Crush": template.get("dcrush").value.strip() if template.has("dcrush") and template.get("dcrush").value.strip() != "N/A" else None,
                "Magic": template.get("dmagic").value.strip() if template.has("dmagic") and template.get("dmagic").value.strip() != "N/A" else None,
                "Range": template.get("drange").value.strip() if template.has("drange") and template.get("drange").value.strip() != "N/A" else None,
                "Poison Immunity": template.get("immunepoison").value.strip() if template.has("immunepoison") else None,
                "Venom Immunity": template.get("immunevenom").value.strip() if template.has("immunevenom") else None,
                "Cannon Immunity": template.get("immunecannon").value.strip() if template.has("immunecannon") else None,
                "Thrall Immunity": template.get("immunethrall").value.strip() if template.has("immunethrall") else None
            }

            for key, value in attributes.items():
                if value and key not in seen_attributes:
                    seen_attributes.add(key)
                    result_details += f"{key}: {value}\n"

    return result_details if result_details else "No relevant data found"


# State management for user
user_state = {}

@bot.command()
async def boss(ctx):
    """Start the boss selection process"""
    user_state[ctx.author.id] = {"step": "boss", "attempts": 0}
    await ctx.send("Anna bossin alkukirjain:")

@bot.event
async def on_message(user_message):
    if user_message.author.bot:
        return

    user_id = user_message.author.id
    if user_id in user_state:
        state = user_state[user_id]

        if state["step"] == "boss":
            # Tarkistetaan, onko syöte yksi kirjain
            letter = user_message.content.strip().lower()
            if len(letter) != 1 or not letter.isalpha():
                await user_message.channel.send("Virheellinen syöte! Syötä vain yksi kirjain. Keskustelu päättyi.")
                del user_state[user_id]
                return

            # Tallennetaan valittu kirjain tilaan
            state["letter"] = letter

            bosses = get_all_bosses()
            filtered_bosses = get_bosses_by_letter(bosses, letter)

            if not filtered_bosses:
                await user_message.channel.send(f"Ei löytynyt bossia, joka alkaa kirjaimella {letter.upper()}.")
                del user_state[user_id]
                return

            message = f"Bossit, jotka alkavat kirjaimella {letter.upper()}:\n"
            for i, boss in enumerate(filtered_bosses, 1):
                message += f"{i}. {boss}\n"
                if len(message) > 2000:  # Jos viesti on liian pitkä
                    await user_message.channel.send(message)
                    message = ""

            if message:
                await user_message.channel.send(message)

            await user_message.channel.send("Valitse bossi numerolla:")

            # Siirretään käyttäjä numerovaiheeseen
            state["step"] = "number"
            return

        elif state["step"] == "number":
            try:
                # Tarkistetaan, että syöte on kokonaisluku
                boss_index = int(user_message.content.strip()) - 1

                # Suodatetaan valitun numeron mukaan
                filtered_bosses = get_bosses_by_letter(get_all_bosses(), state["letter"])

                if boss_index < 0 or boss_index >= len(filtered_bosses):
                    await user_message.channel.send(f"Virheellinen numero! Valitse numero välillä 1 ja {len(filtered_bosses)}. Keskustelu päättyi.")
                    del user_state[user_id]
                    return

                selected_boss = filtered_bosses[boss_index]
                boss_details = get_boss_details(selected_boss)

                if boss_details.startswith("Pyyntö ei tuottanut tuloksia"):
                    await user_message.channel.send(f"Virhe: {boss_details}")
                else:
                    await user_message.channel.send(f"Tiedot {selected_boss}:\n{boss_details}")

                # Lopetetaan vuorovaikutus tämän käyttäjän kanssa
                del user_state[user_id]

            except ValueError:
                # Syöte ei ollut numero
                await user_message.channel.send("Virheellinen syöte! Syötä vain numero. Vuorovaikutus lopetetaan.")
                del user_state[user_id]

        return

    await bot.process_commands(user_message)





@bot.command()
async def coms(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of commands for the bot", color=0x00ff00)
    embed.add_field(name="!boss", value="Get information about a boss by selecting it from a list", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
