
import discord
import aiohttp
import asyncio
import json

# Config
SELFBOT_TOKEN = "enter discord tokens here"  # Replace with your selfbot token
WEBHOOK_URL = "enter url here"      # Replace with your webhook URL
SOURCE_CHANNEL_ID =   # Channel to copy from   (Selfbot)
TARGET_CHANNEL_ID =   # Channel to paste into (webhook_URL)

CHECK_INTERVAL = 30  # cooldown (seconds)

class LatestMessageCopier(discord.Client):
    def __init__(self):
        super().__init__()
        self.last_message_id = None
        self.source_channel = None
        
    async def on_ready(self):
        print(f'Logged in as {self.user}')
        print(f'Monitoring channel ID: {SOURCE_CHANNEL_ID}')
        print(f'Checking every {CHECK_INTERVAL} seconds for new messages')
        
        self.source_channel = self.get_channel(SOURCE_CHANNEL_ID)
        if not self.source_channel:
            print(f"✗ Could not find channel with ID {SOURCE_CHANNEL_ID}")
            return
            
        await self.check_latest_message()
        
        self.loop.create_task(self.message_check_loop())
        
    async def check_latest_message(self):
        try:
            async for message in self.source_channel.history(limit=1):
                if message.author == self.user:
                    return
                    
                if self.last_message_id is None:
                    self.last_message_id = message.id
                    print(f"✓ Initialized with latest message ID: {message.id}")
                    return
                elif message.id != self.last_message_id:
                    self.last_message_id = message.id
                    await self.copy_message(message)
                else:
                    print(f"No new messages (latest: {message.id})")
                    
        except Exception as e:
            print(f"✗ Error checking latest message: {e}")
    
    async def message_check_loop(self):
        while not self.is_closed():
            await asyncio.sleep(CHECK_INTERVAL)
            await self.check_latest_message()
    
    async def copy_message(self, message):
        try:
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'content': message.content or '',
                    'username': message.author.display_name,
                    'avatar_url': str(message.author.avatar.url) if message.author.avatar else str(message.author.default_avatar.url)
                }
                
                if message.embeds:
                    webhook_data['embeds'] = []
                    for embed in message.embeds:
                        embed_dict = embed.to_dict()
                        webhook_data['embeds'].append(embed_dict)
                
                if message.attachments:
                    attachment_info = "\n" + "\n".join([f"📎 {att.filename} ({att.url})" for att in message.attachments])
                    webhook_data['content'] = f"{webhook_data['content']}{attachment_info}" if webhook_data['content'] else attachment_info.strip()
                
                async with session.post(WEBHOOK_URL, json=webhook_data) as resp:
                    if resp.status in [200, 204]:
                        content_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
                        print(f"NEW MESSAGE COPIED from {message.author.display_name}: {content_preview}")
                        print(f"   Message ID: {message.id}")
                        print(f"   Time: {message.created_at}")
                    else:
                        error_text = await resp.text()
                        print(f"✗ Webhook error: {resp.status} - {error_text}")
                            
        except Exception as e:
            print(f"✗ Error copying message: {e}")

class OneTimeCopier(discord.Client):
    def __init__(self):
        super().__init__()
        
    async def on_ready(self):
        print(f'✓ Logged in as {self.user}')
        
        source_channel = self.get_channel(SOURCE_CHANNEL_ID)
        if not source_channel:
            print(f"✗ Could not find channel with ID {SOURCE_CHANNEL_ID}")
            await self.close()
            return
            
        async for message in source_channel.history(limit=1):
            if message.author != self.user:
                await self.copy_message(message)
                break

        await self.close()
        
    async def copy_message(self, message):
        try:
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'content': message.content or '',
                    'username': message.author.display_name,
                    'avatar_url': str(message.author.avatar.url) if message.author.avatar else str(message.author.default_avatar.url)
                }
                
                if message.embeds:
                    webhook_data['embeds'] = [embed.to_dict() for embed in message.embeds]
                
                if message.attachments:
                    attachment_info = "\n" + "\n".join([f"📎 {att.filename}" for att in message.attachments])
                    webhook_data['content'] = f"{webhook_data['content']}{attachment_info}" if webhook_data['content'] else attachment_info.strip()
                
                async with session.post(WEBHOOK_URL, json=webhook_data) as resp:
                    if resp.status in [200, 204]:
                        print(f"Latest message copied from {message.author.display_name}")
                        print(f"   Content: {message.content}")
                        print(f"   Message ID: {message.id}")
                    else:
                        print(f"✗ Webhook error: {resp.status}")
                            
        except Exception as e:
            print(f"✗ Error copying message: {e}")

class ManualCopier(discord.Client):
    def __init__(self):
        super().__init__()
        self.source_channel = None
        
    async def on_ready(self):
        print(f'✓ Logged in as {self.user}')
        print(f'✓ Manual copier ready!')
        print(f'✓ Type "copy" in any channel to copy the latest message from the source channel')
        
        self.source_channel = self.get_channel(SOURCE_CHANNEL_ID)
        if not self.source_channel:
            print(f"✗ Could not find source channel with ID {SOURCE_CHANNEL_ID}")
    
    async def on_message(self, message):
        if message.author != self.user:
            return
            
        if message.content.lower().strip() == "copy":
            if self.source_channel:
                await self.copy_latest_message()
            else:
                print("✗ Source channel not found")
    
    async def copy_latest_message(self):
        try:
            async for message in self.source_channel.history(limit=1):
                if message.author != self.user:
                    await self.copy_message(message)
                    break
        except Exception as e:
            print(f"✗ Error getting latest message: {e}")
    
    async def copy_message(self, message):
        try:
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'content': message.content or '',
                    'username': message.author.display_name,
                    'avatar_url': str(message.author.avatar.url) if message.author.avatar else str(message.author.default_avatar.url)
                }
                
                if message.embeds:
                    webhook_data['embeds'] = [embed.to_dict() for embed in message.embeds]
                
                if message.attachments:
                    attachment_info = "\n" + "\n".join([f"📎 {att.filename}" for att in message.attachments])
                    webhook_data['content'] = f"{webhook_data['content']}{attachment_info}" if webhook_data['content'] else attachment_info.strip()
                
                async with session.post(WEBHOOK_URL, json=webhook_data) as resp:
                    if resp.status in [200, 204]:
                        print(f"Latest message copied from {message.author.display_name}")
                    else:
                        print(f"✗ Webhook error: {resp.status}")
                            
        except Exception as e:
            print(f"✗ Error copying message: {e}")

if __name__ == "__main__":
    print("Discord Latest Message Copier")
    print("=" * 35)
    print("Choose mode:")
    print("1. Continuous monitoring (checks every 30 seconds)")
    print("2. One-time copy (copies latest message once)")
    print("3. Manual trigger (type 'copy' to copy latest)")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice == "1":
        client = LatestMessageCopier()
        print("Starting continuous monitoring...")
    elif choice == "2":
        client = OneTimeCopier()
        print("Copying latest message...")
    elif choice == "3":
        client = ManualCopier()
        print("Starting manual trigger mode...")
    else:
        print("Invalid choice, using continuous monitoring...")
        client = LatestMessageCopier()
    
    try:
        client.run(SELFBOT_TOKEN)
    except discord.LoginFailure:
        print("✗ Invalid token provided!")
    except Exception as e:
        print(f"✗ Error running client: {e}")
