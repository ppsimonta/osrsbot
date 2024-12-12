import requests
import re
import discord
from discord.ext import commands

TOKEN = 'asdasd'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
    response = requests.get("https://oldschool.runescape.wiki/api.php", headers=custom_agent, params=parameters)

    if response.status_code == 200:
        data = response.json()
        
        if 'parse' not in data:
            return "Pyyntö ei tuottanut tuloksia. Tarkista nimen oikeinkirjoitus."

        wikitext = data['parse']['wikitext']['*']  # Poimitaan wikitext

        # Regex Infobox Monster -osion tunnistamiseen
        infobox_match = re.search(r'{{Infobox Monster.*?}}', wikitext, re.DOTALL)

        if infobox_match:
            infobox_content = infobox_match.group(0)  # Poimitaan Infobox Monster
            
            # Regex haluttujen kenttien poimimiseen
            fields_to_extract = [
                r'\|dstab = .*',
                r'\|dslash = .*',
                r'\|dcrush = .*',
                r'\|dmagic = .*',
                r'\|drange = .*',
                r'\|elementalweaknesstype = .*',
                r'\|elementalweaknesspercent = .*',
                r'\|immunepoison = .*',
                r'\|immunevenom = .*',
                r'\|immunecannon = .*',
                r'\|immunethrall = .*',
                r'\|freezeresistance = .*'
            ]
            
            extracted_data = []
            for field in fields_to_extract:
                match = re.search(field, infobox_content)
                if match:
                    # Poistetaan alkaviiva ja "d" edestä
                    result = match.group(0).replace('|', '').replace('d', '', 1).strip()

                    # Muutetaan ensimmäinen kirjain isoksi ja loput pieniksi
                    result = result[0].upper() + result[1:].lower()

                    extracted_data.append(result)

            return "\n".join(extracted_data)
        else:
            return "Infobox Monsteria ei löytynyt wikitextistä."
    else:
        return f"API-kutsu epäonnistui. Statuskoodi: {response.status_code}"

@bot.command()
async def boss(ctx, *, arg):
    try:
        boss_name = arg.strip()

        boss_details = get_boss_details(boss_name)
        
        if boss_details.startswith("Pyyntö ei tuottanut tuloksia"):
            await ctx.send(f"Virhe: {boss_details}")
        else:
            await ctx.send(f"Tiedot {boss_name}:\n{boss_details}")
    
    except Exception as e:
        await ctx.send(f"Virhe: {e}")

#info command
@bot.command()
async def coms(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of commands for the bot", color=0x00ff00)
    embed.add_field(name="!boss <boss_name>", value="Get information about a boss", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        try:
            # Pyydetään käyttäjältä syöte konsolista
            boss_name = input("Anna haettavan bossin nimi: ")
            print(boss_name)

            # Hae bossin tiedot ja tulosta ne konsoliin
            result = get_boss_details(boss_name)
            print(f"Tulos:\n{result}\n")

        except Exception as e:
            print("Tapahtui virhe:", e)
    else:
        # Jos ei ole "test"-komentoa, suoritetaan Discord-botti
        bot.run(TOKEN)