import discord
import requests
import json
import math
from modules import zz_init
import time
from os import path
from shutil import copyfile

IDgrpverificate = zz_init.config().get_IDgrpverificate()
IDgrpnotify = zz_init.config().get_IDgrpnotify()

async def cmndhelp(message):
    await message.channel.send("""```
!mc [Name] - Registriere deinen Minecraft-Account
!mcname [Name] - Gibt deinen aktuellen Minecraft-Account wieder
!rank [Name] - Gibt Erfahrung wieder
!anfrage - Schreibe dem Bot eine Anfrage, die direkt an die Moderatoren privat weitergeleitet werden```""")
    return

async def newjoin(member):
    #hier sollte ein embed erzeugt werden
    return

async def question(message, client):
#    print(message.author.dm_channel.me)
#    print("Test1")
#    print(message.author)
    await message.author.create_dm()
#    print(message.author.dm_channel)
    await message.author.dm_channel.send(content="Bitte schreiben Sie mir Ihre Anfrage in einer Nachricht:")
#    print("Test2")
    author = message.author
    def check(m):
        return m.author == message.author
    Nachricht = await client.wait_for('message', check=check)
#    print(Nachricht.content);
    await message.author.dm_channel.send("Vielen Dank für Ihre Anfrage!")
    VolleNachricht= str(message.author) + ":  " + Nachricht.content
    return VolleNachricht

async def cmndmc(message, client, name=None):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    if not name:
        await message.channel.send("Bitte Minecraftname eingeben")
        author = message.author
        def check(m):
            return m.author == message.author
        mcname = await client.wait_for('message', check=check)
        name = mcname.content

    mcsite = requests.get('https://api.mojang.com/users/profiles/minecraft/' + name)

    if mcsite.text:
        mcinfo = mcsite.json()
        uuid = mcinfo['id']
        uuid = uuid[0:8] + "-" + uuid[8:12] + "-" + uuid[12:16] + "-" + uuid[16:20] + "-" + uuid[20:32]
        #await message.channel.send(uuid)
        sql = "SELECT * FROM mcnames WHERE discord_id ='" + str(message.author.id) + "'"

        mycursor.execute(sql)

        myresult = mycursor.fetchall()
        if(myresult):
            sql = "UPDATE mcnames SET minecraft_name = %s, uuid = %s WHERE discord_id = %s"
            val = (mcinfo['name'], uuid, message.author.id)
            await message.channel.send("Dein Minecraftname **" + name + "** wurde erfolgreich aktualisiert.")
        else:
            sql = "INSERT INTO mcnames (discord_id, minecraft_name, uuid, isWhitelistedYoutube, isWhitelistedTwitch) VALUES (%s, %s, %s, %s, %s)"
            val = (message.author.id, mcinfo['name'], uuid, False, False)
            await message.channel.send("Dein Minecraftname **" + name + "** wurde erfolgreich hinzugefügt.")
        mycursor.execute(sql, val)
        mydb.commit()
    else:
        await message.channel.send("Der Minecraftname **" + name + "** existiert nicht.")
    return

async def cmndnotify(message, guild):
    grpnotify = guild.get_role(IDgrpnotify)
    if await checkrole(message.author.roles, IDgrpnotify):
        await message.author.remove_roles(grpnotify)
        #NIMM GRUPPE WEG
    else:
        await message.author.add_roles(grpnotify)
        #GIB GRUPPE HER
    return

async def cmndmcname(message, name=None):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    if message.raw_mentions:
        ID = message.raw_mentions[0]
        sql = "SELECT minecraft_name FROM mcnames WHERE discord_id ='" + str(ID) + "'"
    elif name:
        ID = await getmemberid(message, name)
        sql = "SELECT minecraft_name FROM mcnames WHERE discord_id ='" + str(ID) + "'"
    else:
        sql = "SELECT minecraft_name FROM mcnames WHERE discord_id ='" + str(message.author.id) + "'"
    mycursor.execute(sql)
    myresult = mycursor.fetchone()
    if myresult:
        if name or message.raw_mentions:
            if message.raw_mentions:
                name = message.guild.get_member(ID).name
            embed = discord.Embed(title=name, color=0xedbc5d)
            embed.set_thumbnail(url=message.guild.get_member(ID).avatar_url)
        else:
            embed = discord.Embed(title=message.author.name, color=0xedbc5d)
            embed.set_thumbnail(url=message.author.avatar_url)

        embed.add_field(name="Minecraft-Name", value=str(myresult[0]), inline=True)
        await message.channel.send(embed=embed)
    else:
        await message.channel.send("Dein Minecraft Name konnte nicht gefunden werden")
    return

async def switchrank(payload, bot):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    Rang = None
    Ziel = None
    Zielname = None
    Zielexp = None
    Rangexists = True
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embed = message.embeds[0]
    if(embed.title == "Rangfunktion"):
        for field in message.embeds[0].fields:
            if field.name == "Rang":
                Rang = int(field.value)
        if payload.emoji.id == 780172418781675531:
            if(Rang > 1):
                Ziel = Rang -1
            else:
                Rangexists = False
        if payload.emoji.id == 780171887619473458:
            Ziel = Rang +1

    if(Rangexists):
        sql = "SELECT points, discord_id FROM ranking ORDER BY points DESC"
        mycursor.execute(sql)
        myresult2 = mycursor.fetchall()

        i = 1
        for p in myresult2:
            if(i == Ziel):
                Zielexp = p[0]
                Zielname = await bot.fetch_user(int(p[1]))
            i = i+1
        embed.set_thumbnail(url=Zielname.avatar_url)
        embed.set_field_at(0, name="Benutzer", value=Zielname.name, inline=False)
        embed.set_field_at(1, name="Rang", value=Ziel, inline=True)
        embed.set_field_at(2, name="Exp", value=Zielexp, inline=True)
        await message.edit(embed=embed)

    await message.remove_reaction(payload.emoji, payload.member)
        #print(Zielname)
        #print(Zielexp)

    return

async def cmndrank(message, name=None):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    if message.raw_mentions:
        ID = message.raw_mentions[0]
        sql = "SELECT points FROM ranking WHERE discord_id ='" + str(ID) + "'"
    elif name:
        ID = await getmemberid(message, name)
        sql = "SELECT points FROM ranking WHERE discord_id ='" + str(ID) + "'"
    else:
        sql = "SELECT points FROM ranking WHERE discord_id ='" + str(message.author.id) + "'"
    mycursor.execute(sql)
    myresult = mycursor.fetchone()

    sql = "SELECT points, discord_id FROM ranking ORDER BY points DESC"
    mycursor.execute(sql)
    myresult2 = mycursor.fetchall()
    count = 1
    rank = 0
    thumbnailurl = None
    if name or message.raw_mentions:
        for p in myresult2:
            if p[1] == ID:
                rank = count
            count += 1
    else:
        for p in myresult2:
            if p[1] == message.author.id:
                rank = count
            count += 1

    if myresult:
        if name or message.raw_mentions:
            if message.raw_mentions:
                name = message.guild.get_member(ID).name
            thumbnailurl = message.guild.get_member(ID).avatar_url
        else:
            name = message.author.name
            thumbnailurl = message.author.avatar_url


        embed = discord.Embed(title="Rangfunktion", color=0xedbc5d)
        embed.set_thumbnail(url=thumbnailurl)
        embed.add_field(name="Benutzer", value=name, inline=False)
        embed.add_field(name="Rang", value=str(rank), inline=True)
        embed.add_field(name="Exp", value=str(myresult[0]), inline=True)
        temp = await message.channel.send(embed=embed)
        await temp.add_reaction('<:ZZleft:780172418781675531>')
        await temp.add_reaction('<:ZZright:780171887619473458>')

    else:
        await message.channel.send("Benutzer nicht in Datenbank vorhanden")

    return

async def cmndranking(message):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()

    sql = "SELECT points, discord_id FROM ranking ORDER BY points DESC"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    count = 1
    rank = 0
    color = 00
    text="```\n"
    for p in myresult:
        if count <= 10:
            embed = discord.Embed(title=message.guild.get_member(p[1]).name, color=0xedbc5d + color)
            embed.set_thumbnail(url=message.guild.get_member(p[1]).avatar_url)
            text += message.guild.get_member(p[1]).name + "\n"
            embed.add_field(name="Rang", value=str(count), inline=True)
            embed.add_field(name="Exp", value=str(p[0]), inline=True)
            color += 10
            await message.channel.send(embed=embed)

        count += 1

    return

async def cmndshutdown(bot):
    await bot.logout()
    bot.clear()
    exit()

async def cmndcheckdb(message, client):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    sql = "SHOW TABLES"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    count = 0
    text = "```"
    for x in myresult:
        text += (str(count) + " " + x[0] + "\n")
        count = count + 1
    text += "```"
    await message.channel.send(text)
    author = message.author
    def check(m):
        return m.author == message.author
    table = await client.wait_for('message', check=check)
    content = int(table.content)
    count = 0
    tablename = "Platzhalter"
    for x in myresult:
        if int(table.content) == count:
            sql = "SELECT * FROM " + x[0]
            tablename = x[0]
        count = count + 1
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    sql2 = "SHOW FIELDS FROM " + tablename
    mycursor.execute(sql2)
    myresult2 = mycursor.fetchall()
    list = []
    for t in myresult2:
        list.append(t[0])
    text = ""

    for p in myresult:
        count = 0
        for q in p:
            if list[count] != "id": #id ausblenden
                spaces = ""
                for x in range(len(list[count]), 20): #leerzeichen hinzufügen
                    spaces += " "
                text+=(list[count] + spaces + str(q) + "\n") #Zeile ausgeben
            count += 1

    if len(text) >= 1800:
        circles = len(text) / 1800
        for x in range(0, math.ceil(circles)):
            part = x * 1800
            await message.channel.send("```" + text[part:(part+1800)] + "```")
    else:
        await message.channel.send("```" + text + "```")
    return

async def cmndstreamchannel(message):
    channels = (message.author.guild.voice_channels)
    emptychannels = False
    cpchannel = channels[0]
    for j in channels:
        if j.category.id == zz_init.config().get_IDcategoryvoice(): # Wenn Kategory richtig ist
            cpchannel = j
    await cpchannel.clone(name="Stream-Channel")
    channels = (message.author.guild.voice_channels)
    anzahl = len(channels) - 1 # -1, da Liste ab 0 beginnt
    #print(anzahl)
    await message.author.move_to(channels[anzahl])

    return

async def cmndwhitelist(message):
    with open('whitelist/whitelist.json') as json_file:
        data = json.load(json_file)
        text = "**Datei-Inhalt: **\n"
        for p in data:
            text+=("Minecraft Name: **" + p['name'] + "**\n")
            text+=("UUID: **" + p['uuid'] +"**\n\n")
        if len(text) >= 2000:
            circles = len(text) / 2000
            for x in range(0, math.ceil(circles)):
                part = x * 2000
                await message.channel.send(text[part:(part+2000)])
        else:
            await message.channel.send(text)
    return

async def getexp(message):
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    sql = "SELECT points FROM ranking WHERE discord_id ='" + str(message.author.id) + "'"
    #Berechnung EXP
    exp = (len(message.content)-2)/5
    if(exp > 10):
        exp = 10
    mycursor.execute(sql)
    myresult = mycursor.fetchone()

    if myresult:
        sql = "UPDATE ranking SET points = %s WHERE discord_id = %s"
        val = ((myresult[0] + exp), message.author.id)
    else:
        sql = "INSERT INTO ranking (discord_id, points) VALUES (%s, %s)"
        val = (message.author.id, exp)
    mycursor.execute(sql, val)
    mydb.commit()
    return

async def resetrank(message, name=None):

    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    if message.raw_mentions:
        ID = message.raw_mentions[0]
        sql = "UPDATE ranking SET points = %s WHERE discord_id = %s"
        val = (0, str(ID))

    elif name:
        ID = await getmemberid(message, name)
        sql = "UPDATE ranking SET points = %s WHERE discord_id = %s"
        val = (0, str(ID))
    mycursor.execute(sql, val)
    mydb.commit()

    return

async def resetuser(message, name=None):

    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    sql = "DELETE FROM mcnames WHERE discord_id = " + str(name)

    mycursor.execute(sql)
    mydb.commit()

    sql = "DELETE FROM ranking WHERE discord_id = " + str(name)

    mycursor.execute(sql)
    mydb.commit()

    return

async def customdbcommand(message, command):

    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    mycursor.execute(command)
    mydb.commit()

    return

async def syncwhitelist():
    mydb = zz_init.getdb()
    mycursor = mydb.cursor()
    sql = "SELECT minecraft_name,uuid,isWhitelistedYoutube,isWhitelistedTwitch FROM mcnames"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    whitelistyoutube = []
    whitelisttwitch = []
    for x in myresult:
        if x[2]:
            whitelistyoutube.append({
                'uuid': x[1],
                'name': x[0]
                })

    with open('whitelist/youtube/whitelist.json', 'w') as outfile:
        json.dump(whitelistyoutube,outfile, indent=2)

    #Kopiere Whitelist in verschiedene Ordner
    paths = open("whitelist/youtube/paths.txt", "r")
    for line in paths:
        copyfile('whitelist/youtube/whitelist.json', str(line.rstrip()) + 'whitelist.json')
    paths.close()

    for x in myresult:
        if x[3]:
            whitelisttwitch.append({
                'uuid': x[1],
                'name': x[0]
                })

    with open('whitelist/twitch/whitelist.json', 'w') as outfile:
        json.dump(whitelisttwitch,outfile, indent=2)

    #Kopiere Whitelist in verschiedene Ordner
    paths = open("whitelist/twitch/paths.txt", "r")
    for line in paths:
        copyfile('whitelist/twitch/whitelist.json', str(line.rstrip()) + 'whitelist.json')
    paths.close()

    return

async def getmemberid(message, name):
    guild = message.author.guild
    ID = 0
    for member in guild.members:

    #for member in get_all_members():
        if member.name == name:
            ID = member.id
    return ID

async def checkrole(roles, roleid):
    for i in roles:
        if i.id == roleid:
            return True
    return False

async def checkwords(message):

    words = open("blacklist/discord/badwords.txt", "r")
    for line in words:
        if str(line.strip()).lower() in message.content.strip().lower():
            return True
    words.close()

    return False

async def addblacklistword(message, arg):

    words = open("blacklist/discord/badwords.txt", "a")

    words.write(arg.strip() + "\n")

    words.close()

    return False

async def removeblacklistword(message, arg):

    newfile = ""
    words = open("blacklist/discord/badwords.txt", "r")
    for line in words:
        if line != arg.strip()+"\n":
            newfile += line
    words.close()

    words = open("blacklist/discord/badwords.txt", "w")
    words.write(newfile)

    words.close()


    return False

async def blacklist():

    file =(open("blacklist/discord/badwords.txt", "r"))
    content = ""
    for line in file:
        content += line

    return content


#async def is_verified(ctx):
#    check = await checkrole(ctx.author.roles, IDgrpverificate)
#    return check
