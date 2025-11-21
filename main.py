import os
import logging
import subprocess
import glob
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
# Get the Token from the cloud environment, NOT hardcoded.
TOKEN = os.getenv("TOKEN")

# Enable logging (Helps you see errors in the cloud console)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message."""
    await update.message.reply_text(
        "🎵 **Spotify Downloader Bot**\n\n"
        "Send me a Spotify song link, and I'll download it for you!\n"
        "(Please wait a few seconds after sending a link, audio processing takes time.)"
    )

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the Spotify link and downloads the song."""
    user_link = update.message.text.strip()

    # Basic check if it's a Spotify link
    if "open.spotify.com" not in user_link:
        await update.message.reply_text("❌ That doesn't look like a valid Spotify link.")
        return

    status_msg = await update.message.reply_text("⏳ **Searching and Downloading...**\n(This might take up to 30 seconds)")

    try:
        # 1. Run spotdl command using subprocess
        # We use the command line tool because it's the most stable way to use spotdl
        command = ["spotdl", user_link]
        
        # Run the command and wait for it to finish
        subprocess.run(command, check=True)

        # 2. Find the downloaded MP3 file
        # spotdl downloads to the current folder. We look for the most recent .mp3
        list_of_files = glob.glob('*.mp3') 
        
        if not list_of_files:
            await status_msg.edit_text("❌ Download failed. Could not find the file.")
            return
            
        # Get the latest file (in case there are others)
        latest_file = max(list_of_files, key=os.path.getctime)
        
        await status_msg.edit_text("⬆️ **Uploading to Telegram...**")

        # 3. Send the Audio
        chat_id = update.message.chat_id
        await context.bot.send_audio(chat_id=chat_id, audio=open(latest_file, 'rb'))

        # 4. Clean up (Delete the file from the server to save space)
        os.remove(latest_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ An error occurred: {e}")

if __name__ == '__main__':
    # Check if Token is present
    if not TOKEN:
        print("Error: TOKEN environment variable not set!")
        exit(1)

    # Build the bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    # Filters ANY text that isn't a command
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_spotify))

    print("Bot is running...")
    application.run_polling()
