import nextcord
from nextcord.ext import commands
from api import truewallet
import json
import asyncio

bot = commands.Bot(intents=nextcord.Intents.all())
phone = "0802630402" # เบอร์

@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Streaming(name="EXE LUA SHOP !",url="https://www.twitch.tv/ananda_praosri"))
    print(f"Login as {bot.user}")





class Topup_input(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(title="เติมเงินออโต้",timeout=False)  
        self.one = nextcord.ui.TextInput(
            label="ลิงค์อั่งเปา",
            placeholder="https://gift.truemoney.com/campaign/?v=XXXXXXXX-XXXX",
            max_length=200,
            required=True
        )
        self.add_item(self.one)
    async def callback(self, interaction: nextcord.Interaction):
        try:
            linkgift = self.one.value.split("?v=")[1]

            status,data = truewallet(phone,linkgift)
            
            if status:
                money = int(float(data["data"]["voucher"]["redeemed_amount_baht"]))
                embed = nextcord.Embed(title="System Info",description=f"📊 Status :\n```arm\nSuccessfully\n```\n\n📜 หมายเหตุ :\n```arm\nคุณได้ทำการเติมเงินเข้าบัญชีเป็นจำนวน {money} บาท\n```",colour=0xfa7900)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                embed.set_footer(text="exeluac2.",
                icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                await interaction.send(embed=embed,ephemeral=True)

                embedss = nextcord.Embed(title="Log - เติมเงิน",description=f"📊 Status :\n```arm\nSuccessfully\n```\n\n📜 หมายเหตุ :\n```arm\n{interaction.user} ได้ทำการเติมเงินเข้าบัญชีเป็นจำนวน {money} บาท\n```",colour=0xfa7900)
                embedss.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                embedss.set_footer(text="exeluac2.",
                icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                await bot.get_channel().send(embed=embedss)# ใส่เลขห้องตรงนี้

                with open("data.json", "r") as json_file:
                    datas = json.load(json_file)

                # ตรวจสอบว่ามีข้อมูลสำหรับผู้ใช้นี้หรือไม่
                user_id = str(interaction.user.id)

                if user_id not in datas:
                    datas[user_id] = "0"

                # บวกตัวเลขใหม่กับค่าที่มีอยู่แล้ว
                datas[user_id] = str(int(datas[user_id]) + money)

                # เขียนข้อมูลกลับลงในไฟล์ JSON
                with open("data.json", "w") as json_file:
                    json.dump(datas, json_file)
                
                print(self.one.value.split("?v=")[1])
            else:
                embed = nextcord.Embed(
                    title="System Info",
                    description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nลิงค์อั่งเปาของคุณใช้ง่านไม่ได้\n```",
                    colour=0xff0000
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                embed.set_footer(text="exeluac2.",
                icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                await interaction.send(embed=embed, ephemeral=True)
        except Exception as e:
            # Catch any other exceptions and send a default error message
            default_embed = nextcord.Embed(
                title="System Info",
                description=f"📊 Status :\n```arm\nผิดพลาด {type(e).__name__}\n```\n\n📜 หมายเหตุ :\n```arm\nไม่ใช้ประเภทลิงค์อั่งเปา\n```",
                colour=0xff0000
            )
            default_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            default_embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=default_embed, ephemeral=True)

############################################################################    




class Nuclear_SMS(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @nextcord.ui.button(label="✅ ยืนยัน", style=nextcord.ButtonStyle.green)
    async def on_confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # ตรวจสอบว่ามีข้อมูลสำหรับผู้ใช้นี้หรือไม่
        user_id = str(interaction.user.id)

        with open("data.json", "r") as json_file:
            data = json.load(json_file)

        if user_id not in data:
            embed = nextcord.Embed(title="System Info",description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nคุณยังไม่มีบัญชี สามารถเติมเงินครั่งแรกเพื่อสร้างบัญชีได้\n```",colour=0xff0000)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed, ephemeral=True)
            return  # Exit the function if the user doesn't have an account

        current_num = int(data[user_id])

        if current_num > 35:
            new_num = max(0, current_num - 35)
            data[user_id] = str(new_num)

            # เขียนข้อมูลกลับลงในไฟล์ JSON
            with open("data.json", "w") as json_file:
                json.dump(data, json_file)

            await interaction.user.add_roles(interaction.guild.get_role(1175669246521507950))
            embed = nextcord.Embed(title="System Info",description="📊 Status :\n```arm\nSsusedfully\n```\n\n📜 หมายเหตุ :\n```arm\nซื้อสินค้าสำเร็จ\n```\n\n📑 วิธีใช้ง่าน :\n```arm\nสามารถไปที่ 〈📞〉sᴘᴀᴍ-sᴍs\nเพื่อใช้งานได้เลย\n```",colour=0xfa7900)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed,ephemeral=True)
            user = interaction.user
            embeds = nextcord.Embed(title="คุณได้ทำการซื้อสินค้าจากร้าน EXE LUA SHOP",description="🛒 สินค้าที่คุณซื้อ :\n```arm\nSMS\n```\n\n💰 จำนวนเงิน :\n```arm\n35 บาท\n```\n\n📑 คำชี้แจงจาก exeluac2. :\n```arm\nขอบคุณที่ใช้บริการร้านเรา หวังว่าสินค้าทางร้านจะภูมิใจกับราคาที่ท่านได้ซื้อ หากมีปัญหาอะไรอย่ารอช้าที่จะเข้ามาติดต่อ (:\n```\nขอบคุณที่ใช้บริการ / เเละนอกจากนี้ร้านเรารับเขียนบอทอีกด้วยไม่ว่าจะเป็นบอทหลายระบบต่างๆ สนใจสามารถติดต่อได้ที่ @exeluac2. หรือ กด ⁠Ticket",colour=0xfa7900)
            embeds.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embeds.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")   
            await user.send(embed=embeds)
        else:
            embed = nextcord.Embed(
                title="System Info",
                description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nจำนวนเงินของคุณไม่เพียงพอในบัญชี\n```",
                colour=0xff0000
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed, ephemeral=True)


class Nuclear_Flood(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.value = None

    @nextcord.ui.button(label="✅ ยืนยัน", style=nextcord.ButtonStyle.green)
    async def on_confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # ตรวจสอบว่ามีข้อมูลสำหรับผู้ใช้นี้หรือไม่
        user_id = str(interaction.user.id)

        with open("data.json", "r") as json_file:
            data = json.load(json_file)

        if user_id not in data:
            embed = nextcord.Embed(title="System Info",description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nคุณยังไม่มีบัญชี สามารถเติมเงินครั่งแรกเพื่อสร้างบัญชีได้\n```",colour=0xff0000)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed, ephemeral=True)
            return  # Exit the function if the user doesn't have an account

        current_num = int(data[user_id])

        if current_num > 99:
            new_num = max(0, current_num - 99)
            data[user_id] = str(new_num)

            # เขียนข้อมูลกลับลงในไฟล์ JSON
            with open("data.json", "w") as json_file:
                json.dump(data, json_file)

            await interaction.user.add_roles(interaction.guild.get_role(1125264956485546055))
            embed = nextcord.Embed(title="System Info",description="📊 Status :\n```arm\nSsusedfully\n```\n\n📜 หมายเหตุ :\n```arm\nซื้อสินค้าสำเร็จ\n```\n\n📑 วิธีใช้ง่าน :\n```arm\nเราได้ส่งลิงค์ดาวร์โหลดโปรแกรมใน DM คุณแลัว!\n```",colour=0xfa7900)
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed,ephemeral=True)
            users = interaction.user
            embeds = nextcord.Embed(title="คุณได้ทำการซื้อสินค้าจากร้าน EXE LUA SHOP",description="🛒 สินค้าที่คุณซื้อ :\n```arm\nexeluac2.\n```\n\n💰 จำนวนเงิน :\n```arm\n99 บาท\n```\n\n📑 คำชี้แจงจาก exeluac2. :\n```arm\nขอบคุณที่ใช้บริการร้านเรา หวังว่าสินค้าทางร้านจะภูมิใจกับราคาที่ท่านได้ซื้อ หากมีปัญหาอะไรอย่ารอช้าที่จะเข้ามาติดต่อ (:\n```\n\n📌 ลิงค์ดาวน์โหลดโปรแกรม :\n||dfgdfgdfgdgdfgdfgd||\n\nขอบคุณที่ใช้บริการ / เเละนอกจากนี้ร้านเรารับเขียนบอทอีกด้วยไม่ว่าจะเป็นบอทหลายระบบต่างๆ สนใจสามารถติดต่อได้ที่ @exeluac2. หรือ กด ⁠Ticket",colour=0xfa7900)
            embeds.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embeds.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")   
            await users.send(embed=embeds)
        else:
            embed = nextcord.Embed(
                title="System Info",
                description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nจำนวนเงินของคุณไม่เพียงพอในบัญชี\n```",
                colour=0xff0000
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed, ephemeral=True)


class MyDropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="📞 Sms", description="ยศใช้งานยิงเบอร์ในดิสคอร์ดทางร้าน [35 บาท]"),
            nextcord.SelectOption(label="📂 exeluac2.", description="โปรแกรม 2in1 สามารถใช้ยิงดิสและยิงเบอร์ [99 บาท]"),
        ]
        super().__init__(placeholder='🛒 เลือกสินค้าที่ต้องการ', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        if self.values[0] == '📞 Sms':
            view = Nuclear_SMS()
            embed = nextcord.Embed(
                title="System Info",
                description="🛒 สินค้า :\n```arm\nMS\n```\n\n💰 ราคา :\n```arm\n35 บาท\n```",
                colour=0xffc800
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.edit_original_message(embed=embed,view=view, ephemeral=True)
        elif self.values[0] == "📂 exeluac2.":
            view = Nuclear_Flood()
            embed = nextcord.Embed(
                title="System Info",
                description="🛒 สินค้า :\n```arm\nNuclear Flood\n```\n\n💰 ราคา :\n```arm\n99 บาท\n```",
                colour=0xffc800
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            embed.set_footer(text="exeluac2.",
            icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
            await interaction.send(embed=embed,view=view, ephemeral=True)
        else:
            await interaction.response.send_message(f'exeluac2.',ephemeral=True)





class Button_Topup(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="🧧 เติมเงิน", style=nextcord.ButtonStyle.blurple)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(Topup_input())

        

class Button_Check(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="💰 เช็คยอดเงิน", style=nextcord.ButtonStyle.green)

    async def callback(self, interaction: nextcord.Interaction):
        # Get the user ID of the interaction user
        user_id = str(interaction.user.id)

        try:
            # Load data from the JSON file
            with open("data.json", "r") as json_file:
                data = json.load(json_file)

            # Check if the user ID is in the data dictionary
            if user_id not in data:
                embed = nextcord.Embed(
                    title="System Info",
                    description="📊 Status :\n```arm\nผิดพลาด 404\n```\n\n📜 หมายเหตุ :\n```arm\nคุณยังไม่มีบัญชี สามารถเติมเงินครั่งแรกเพื่อสร้างบัญชีได้\n```",
                    colour=0xff0000
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                embed.set_footer(text="exeluac2.",
                icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                await interaction.send(embed=embed,ephemeral=True)
            else:
                # Get the balance for the user ID
                balance = data[user_id]
                await interaction.send(embed=create_balance_embed(user_id, balance),ephemeral=True)
        except Exception as e:
            await interaction.send(f"เกิดข้อผิดพลาดขณะดึงข้อมูล: {str(e)}")

def create_balance_embed(user_id, balance):
    # You can customize the appearance of the embed message here
    embed = nextcord.Embed(title="System Info",
                        description=f"จำนวนเงินของคุณในบัญชี :\n```arm\n💸 {balance} บาท\n```",
                        colour=0xfa7900)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
    embed.set_footer(text="exeluac2.",
    icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
    return embed


############################################################################################
@bot.slash_command(description="เซ็ทข้อความเติมเงิน",guild_ids=[])
async def setup(ctx: nextcord.Interaction):
    required_role_id =   # ตั้งค่าเลขบทบาทที่ต้องการเช็ค
    required_permissions = nextcord.Permissions(administrator=False)
    if required_role_id in [role.id for role in ctx.user.roles] and ctx.user.guild_permissions >= required_permissions:
        combined_view = nextcord.ui.View(timeout=None)
        combined_view.add_item(MyDropdown())
        combined_view.add_item(Button_Topup())
        combined_view.add_item(Button_Check())
        combined_view.add_item(nextcord.ui.Button(style=nextcord.ButtonStyle.link, url='fgdfgdghdhfgbnfgb', label="วิธีใช้งาน"))
        embed = nextcord.Embed(title="───                    EXE LUA SHOP                ───",description="```\n🧧 บอทเติมเงิน 24 ชั่วโมง \n\n💳・ ระบบเติมเงินด้วยอั่งเปา\n🔧・ใช้สะดวกรับของรวดเร็ว\n🛒・ซื้อแลัวไม่สามารถแลกเป็นเงินจริงได้ทุกกรณี\n```",colour=0xfa7900)
        embed.set_image(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
        embed.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
        await ctx.send("เราได้ทำการสร้างระบบเติมเงินแลัว",ephemeral=True)
        await bot.get_channel().send(embed=embed,view=combined_view)# ใส่เลขห้องตรงนี้
        await combined_view.wait()
    else:
        await ctx.send("คุณไม่มีสิทธิ์ในการเรียกใช้คำสั่งนี้", ephemeral=True)
    









    
@bot.slash_command(guild_ids=[])
async def add_json(ctx, num: int, user_ids: str):
    required_role_id = 
    required_permissions = nextcord.Permissions(administrator=False)

    if (required_role_id in [role.id for role in ctx.user.roles]and ctx.user.guild_permissions >= required_permissions):
        try:
            # ตรวจสอบว่า user_ids ไม่ว่างเปล่า
            if user_ids:
                # ใช้ user_ids ที่ผู้ใช้ป้อนเป็น user_id
                user_id = user_ids

                with open("data.json", "r") as json_file:
                    data = json.load(json_file)

                if user_id not in data:
                    data[user_id] = "0"

                data[user_id] = str(int(data[user_id]) + num)

                with open("data.json", "w") as json_file:
                    json.dump(data, json_file)
                embed = nextcord.Embed(title="System Info",description=f"📊 Status :\n```arm\nSsusedfully\n```\n\n📜 หมายเหตุ :\n```arm\nเราได้ทำการเติมเงินให้กับ {user_id}\n\nเป็นจำนวน {data[user_id]}\n```",colour=0xfa7900)
                embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                embed.set_footer(text="exeluac2.",icon_url="https://cdn.discordapp.com/attachments/1267065063676579891/1312311128768118844/standard_1.gif?ex=676e4f7a&is=676cfdfa&hm=45bb675f4810aff5f53713108a6ed69bd13fa984479bdf1dae17a0f8c881031a&")
                await ctx.send(embed=embed,ephemeral=True)
            else:
                await ctx.send("Please enter a valid user ID.",ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error adding numbers: {str(e)}",ephemeral=True)
    else:
        await ctx.send("คุณไม่มีสิทธิ์ใช้งานคำสั่งนี้", ephemeral=True)

@bot.slash_command(guild_ids=[1124620993835585606])
async def delet_num(ctx, num: int):
    required_role_id = 1125264373619896371  # ตั้งค่าเลขบทบาทที่ต้องการเช็ค
    required_permissions = nextcord.Permissions(administrator=False)
    if required_role_id in [role.id for role in ctx.user.roles] and ctx.user.guild_permissions >= required_permissions:
        try:
            with open("data.json", "r") as json_file:
                data = json.load(json_file)

            # ตรวจสอบว่ามีข้อมูลสำหรับผู้ใช้นี้หรือไม่
            user_id = str(ctx.user.id)

            if user_id in data:
                # ลบตัวเลขตามจำนวนที่ผู้ใช้ระบุ
                current_num = int(data[user_id])
                new_num = max(0, current_num - num)
                data[user_id] = str(new_num)

                # เขียนข้อมูลกลับลงในไฟล์ JSON
                with open("data.json", "w") as json_file:
                    json.dump(data, json_file)

                await ctx.send(f"Deleted {num} numbers for user {user_id}. Remaining: {data[user_id]}")
            else:
                await ctx.send(f"No numbers found for user {user_id}")
        except Exception as e:
            await ctx.send(f"Error deleting numbers: {str(e)}")
    else:
        await ctx.send("คุณไม่มีสิทธิ์ในการเรียกใช้คำสั่งนี้", ephemeral=True)

bot.run("")