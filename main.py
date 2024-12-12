import requests
import mwparserfromhell
import discord
from discord.ext import commands

TOKEN = 'your token'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Funktio, joka hakee kaikki bossit Category:Bosses-kategoriasta
def get_all_bosses():
    custom_agent = {
        'User-Agent': 'pera',
        'From': 'perttu.simontaival@gmail.com'
    }
    # API-kyselyn parametrit Category:Bosses-sivulle
    parameters = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': 'Category:Bosses',
        'format': 'json',
        'cmtype': 'page',  # Vain sivut, ei alikategoriat
        'cmlimit': 'max'  # Hakee niin monta sivua kuin mahdollista
    }

    # API-kutsu
    result = requests.get("https://oldschool.runescape.wiki/api.php", headers=custom_agent, params=parameters).json()

    if 'query' not in result:
        return "Pyyntö ei tuottanut tuloksia."

    # Lista, johon tallennetaan kaikki bossit
    bosses = []

    for page in result['query']['categorymembers']:
        bosses.append(page['title'])


    return bosses


# Funktio, joka hakee bossit, jotka alkavat tietyllä kirjaimella
def get_bosses_by_letter(bosses, letter):
    # Suodatetaan kaikki bossit, jotka alkavat annetulla kirjaimella
    filtered_bosses = [boss for boss in bosses if boss.lower().startswith(letter.lower())]
    return filtered_bosses


def get_boss_details(boss_name):
    # Määritä käyttäjäagentti
    custom_agent = {
        'User-Agent': 'pera',
        'From': 'perttu.simontaival@gmail.com'
    }

    # Pienet sanat, jotka jätetään pieniksi
    small_words = {'of', 'the', 'archaeologist', 'deathless', 'twisted', 'maledictus', 'brothers', 'demon', 'kill', 'spirit', 'golem'}

    # Muokataan syöte niin, että ensimmäinen kirjain on isolla kaikissa sanoissa, mutta pienet sanat jätetään pieniksi
    boss = "_".join(
        word.lower() if word.lower() in small_words else word[0].upper() + word[1:].lower()
        for word in boss_name.strip().split()
    )

    # API-kyselyn parametrit
    parameters = {
        'action': 'parse',
        'prop': 'wikitext',
        'format': 'json',
        'page': boss  
    }

    # API-kutsu
    result = requests.get("https://oldschool.runescape.wiki/api.php", headers=custom_agent, params=parameters).json()

    if 'parse' not in result:
        return "Pyyntö ei tuottanut tuloksia."

    data = result['parse']['wikitext']['*'].encode('utf-8')

    wikicode = mwparserfromhell.parse(data)

    result_details = ""

    templates = wikicode.filter_templates()

    # Käytetään setiä estämään duplikaattien lisääminen
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



@bot.command()
async def boss(ctx):
    await ctx.send("Anna bossin alkukirjain:")

    def check(m):
        return m.author == ctx.author and len(m.content) == 1 and m.content.isalpha()

    try:
        letter_msg = await bot.wait_for('message', check=check, timeout=30)
        letter = letter_msg.content.lower()
        
        # Hae kaikki bossit ja suodata ne kirjaimen mukaan
        bosses = get_all_bosses()
        filtered_bosses = get_bosses_by_letter(bosses, letter)
        
        if not filtered_bosses:
            await ctx.send(f"Ei löytynyt bossia, joka alkaa kirjaimella {letter.upper()}.")
            return
        
        # Näytetään bossit, jaetaan useampaan viestiin, jos lista on liian pitkä
        message = f"Bossit, jotka alkavat kirjaimella {letter.upper()}:\n"
        for i, boss in enumerate(filtered_bosses, 1):
            message += f"{i}. {boss}\n"
            if len(message) > 2000:  # Jos viesti on liian pitkä, lähetetään se ja aloitetaan uusi
                await ctx.send(message)
                message = ""
        
        if message:
            await ctx.send(message)

        await ctx.send("Valitse bossi numerolla:")

        def number_check(m):
            return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(filtered_bosses)

        # Odotetaan valintaa
        number_msg = await bot.wait_for('message', check=number_check, timeout=30)
        boss_index = int(number_msg.content) - 1
        selected_boss = filtered_bosses[boss_index]
        
        # Haetaan valitun bossin tiedot
        boss_details = get_boss_details(selected_boss)
        if boss_details.startswith("Pyyntö ei tuottanut tuloksia"):
            await ctx.send(f"Virhe: {boss_details}")
        else:
            await ctx.send(f"Tiedot {selected_boss}:\n{boss_details}")
    
    except Exception as e:
        await ctx.send(f"Virhe: {e}")

#info command
@bot.command()
async def coms(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of commands for the bot", color=0x00ff00)
    embed.add_field(name="!boss", value="Get information about a boss by selecting it from a list", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
