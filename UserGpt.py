# -*- coding: utf-8 -*-

from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
import asyncio
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Your credentials
API_ID = 23844616
API_HASH = '4aeca3680a20f9b8bc669f9897d5402f'
PHONE = '+919761085591'

# Target chat ID for forwarding messages
TARGET_CHAT_ID = -1002593995412

# Store for tracking message processing
processing_queue = []
current_processing = None

# Initialize the client
client = TelegramClient('user_session', API_ID, API_HASH)

# Log all messages from the target chat
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def log_target_chat_messages(event):
    logger.info(f"[TARGET CHAT] {event.sender_id}: {event.text}")

# Store pending responses: {sender_id: message_id_sent_to_target_chat}
pending_responses = {}

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_new_message(event):
    global current_processing
    
    # Ignore if we're already processing a message
    if current_processing is not None:
        return
    
    try:
        sender_id = event.sender_id
        if sender_id not in processing_queue:
            processing_queue.append(sender_id)
        current_processing = sender_id
        formatted_message = f"@CopilotOfficialBot {event.text} , reply in short"
        # Send to target chat
        sent_message = await client.send_message(TARGET_CHAT_ID, formatted_message)
        # Store the message id to match the reply
        pending_responses[sender_id] = sent_message.id
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        if current_processing in processing_queue:
            processing_queue.remove(current_processing)
        current_processing = None

# Listen for new messages in the target chat and forward them to the correct user
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def forward_response_to_user(event):
    global current_processing
    # Find which user is waiting for a response
    for sender_id, sent_msg_id in list(pending_responses.items()):
        # Only forward messages that come after the sent message
        if event.reply_to_msg_id == sent_msg_id or (event.id > sent_msg_id and current_processing == sender_id):
            try:
                await client.send_message(sender_id, event.text)
                logger.info(f"Forwarded response to user {sender_id}")
            except Exception as e:
                logger.error(f"Failed to forward response: {e}")
            # Clean up
            if sender_id in processing_queue:
                processing_queue.remove(sender_id)
            pending_responses.pop(sender_id, None)
            current_processing = None
            break

async def main():
    await client.start(phone=PHONE)
    logger.info("Bot is ready!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main()) 