import aiohttp
import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# Log in settings
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

# Loading variables
load_dotenv()

TOKEN = os.getenv("USER_TOKEN")
CHANNEL_IDS = [id.strip() for id in os.getenv("CHANNEL_IDS").split(",")] if os.getenv("CHANNEL_IDS") else []
DEFAULT_REACTIONS = [r.strip() for r in os.getenv("REACTIONS").split(",")] if os.getenv("REACTIONS") else []
MIN_DELAY = float(os.getenv("MIN_DELAY", 1))
MAX_DELAY = float(os.getenv("MAX_DELAY", 3))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 2))

# Filter of authors
AUTHOR_FILTERS_STR = os.getenv("AUTHOR_FILTERS", "")
AUTHOR_REACTIONS = {}

# Parsing authors filters
if AUTHOR_FILTERS_STR:
    try:
        for filter_str in AUTHOR_FILTERS_STR.split("|"):
            if ":" in filter_str:
                user_id, reactions_str = filter_str.split(":", 1)
                user_id = user_id.strip()
                reactions = [r.strip() for r in reactions_str.split(",")]
                AUTHOR_REACTIONS[user_id] = reactions
                logging.info(f"🎯 Configured filter for {user_id}: {reactions}")
    except Exception as e:
        logging.error(f"❌ Error parsing AUTHOR_FILTERS: {e}")

headers = {
    "Authorization": TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json"
}

class AdvancedDiscordSelfBot:
    def __init__(self):
        self.session = None
        self.last_timestamps = {}
        self.message_queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(3)
        
        for channel_id in CHANNEL_IDS:
            self.last_timestamps[channel_id] = self.get_current_utc_time()
    
    def get_reactions_for_author(self, author_id):
        """Gives reactions for author or default one"""
        author_id_str = str(author_id)
        if author_id_str in AUTHOR_REACTIONS:
            return AUTHOR_REACTIONS[author_id_str]
        return DEFAULT_REACTIONS
    
    def should_process_message(self, message):
        """Chceck if message should be considered"""
        author_id = str(message['author']['id'])
        
        # IF authors filters are defined
        if AUTHOR_REACTIONS:
            # Chceck if author is on list
            if author_id in AUTHOR_REACTIONS:
                return True
            # If not on list, but default rections are present - proceed
            elif DEFAULT_REACTIONS:
                return True
            # IF not on list and default emojis aren't present - ignore
            else:
                return False
        
        # If filters aren't present, proceed all messages (if default reactions are defined)
        return bool(DEFAULT_REACTIONS)
    
    def get_current_utc_time(self):
        return datetime.now(timezone.utc).isoformat()
    
    def parse_discord_timestamp(self, timestamp_str):
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    
    async def init_session(self):
        self.session = aiohttp.ClientSession(headers=headers)
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def get_channel_messages(self, channel_id, limit=10):
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    messages = await response.json()
                    return sorted(messages, key=lambda x: x['timestamp'], reverse=True)
                return []
        except Exception as e:
            logging.error(f"❌ Error downloading message: {e}")
            return []
    
    async def add_reaction(self, channel_id, message_id, emoji):
        if emoji.startswith('<') and emoji.endswith('>'):
            emoji = emoji.replace(':', '%3A')
        
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        
        try:
            async with self.session.put(url) as response:
                if response.status in [200, 204]:
                    return True
                elif response.status == 429:
                    retry_after = float(response.headers.get('Retry-After', 5))
                    logging.warning(f"⏰ Rate limit, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self.add_reaction(channel_id, message_id, emoji)
                else:
                    return False
        except Exception as e:
            logging.error(f"❌ Error adding reaction: {e}")
            return False
    
    async def process_single_message(self, channel_id, message):
        """Proceed single message"""
        if not self.should_process_message(message):
            author = message['author']['username']
            logging.info(f"⏭️ Skipped message from {author} (no reaction to add)")
            return
        
        message_id = message['id']
        author = message['author']['username']
        author_id = message['author']['id']
        content_preview = message['content'][:50] + "..." if len(message['content']) > 50 else message['content']
        
        # Set reactions to add
        reactions_to_add = self.get_reactions_for_author(author_id)
        
        if not reactions_to_add:
            logging.info(f"⏭️ None reactions for {author}")
            return
        
        logging.info(f"🎯 Proceeding message from {author} ({author_id}): {content_preview}")
        logging.info(f"   🎭 Reactions: {reactions_to_add}")
        
        # Add reactions
        for reaction in reactions_to_add:
            async with self.semaphore:
                success = await self.add_reaction(channel_id, message_id, reaction)
                if success:
                    delay = random.uniform(MIN_DELAY, MAX_DELAY)
                    await asyncio.sleep(delay)
                else:
                    logging.error(f"❌ Failed adding reaction {reaction}")
    
    async def check_channel_for_new_messages(self, channel_id):
        messages = await self.get_channel_messages(channel_id, 20)
        
        if not messages:
            return
        
        new_messages = []
        current_last_timestamp = self.last_timestamps[channel_id]
        
        for message in messages:
            message_time = self.parse_discord_timestamp(message['timestamp'])
            last_time = self.parse_discord_timestamp(current_last_timestamp)
            
            if message_time > last_time:
                new_messages.append(message)
            else:
                break
        
        if new_messages:
            newest_message = max(new_messages, key=lambda x: self.parse_discord_timestamp(x['timestamp']))
            self.last_timestamps[channel_id] = newest_message['timestamp']
            
            for message in reversed(new_messages):
                if self.should_process_message(message):
                    await self.message_queue.put((channel_id, message))
                    logging.info(f"📥 Added to queue: {message['id']}")
                else:
                    author = message['author']['username']
                    logging.debug(f"📭 Skipped adding to queue: {author}")
    
    async def message_processor(self):
        while True:
            try:
                channel_id, message = await self.message_queue.get()
                await self.process_single_message(channel_id, message)
                self.message_queue.task_done()
            except Exception as e:
                logging.error(f"❌ Error from procession: {e}")
                await asyncio.sleep(5)
    
    async def monitor_loop(self):
        await self.init_session()
        
        processors = [asyncio.create_task(self.message_processor()) for _ in range(3)]
        
        try:
            logging.info("🚀 Launching inteligent monitoring with filters...")
            if AUTHOR_REACTIONS:
                logging.info(f"🎯 Active authors: {list(AUTHOR_REACTIONS.keys())}")
            if DEFAULT_REACTIONS:
                logging.info(f"🎯 Default reactions: {DEFAULT_REACTIONS}")
            
            while True:
                tasks = []
                for channel_id in CHANNEL_IDS:
                    tasks.append(self.check_channel_for_new_messages(channel_id))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(CHECK_INTERVAL)
                
        except asyncio.CancelledError:
            logging.info("⏹️ Stopping monitoring...")
        except Exception as e:
            logging.error(f"💥 Critical error: {e}")
        finally:
            for task in processors:
                task.cancel()
            await asyncio.gather(*processors, return_exceptions=True)
            await self.close_session()

async def main():
    bot = AdvancedDiscordSelfBot()
    try:
        await bot.monitor_loop()
    except KeyboardInterrupt:
        logging.info("👋 Stopping...")
    except Exception as e:
        logging.error(f"💥 Core error: {e}")

if __name__ == "__main__":
    # Token test
    import requests
    
    def test_token():
        test_headers = headers.copy()
        response = requests.get("https://discord.com/api/v9/users/@me", headers=test_headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            logging.info(f"✅ Token valid - user: {user_data['username']}")
            return True
        else:
            logging.error(f"❌ Token invalid - status: {response.status_code}")
            return False
    
    if test_token():
        asyncio.run(main())
    else:
        logging.error("❌ Not launching - invalid token!")