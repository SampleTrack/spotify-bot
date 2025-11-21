import os
import logging
import subprocess
import glob
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get('PORT', 5000)) # Render provides a PORT automatically

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DUMMY WEB SERVER (FOR RENDER) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive!"

def run_web_server():
    # This runs the fake website on the port Render assigns
    app.run(host='0.0.0.0', port=PORT)

# --- BOT CODE ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Spotify Downloader Bot (Render Edition)**\n\n"
        "Send me a Spotify link! (Processing takes 10-30s)"
    )

async def download_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_link = update.message.text.strip()

    # Basic validation
    if "open.spotify.com" not in user_link:
        await update.message.reply_text("❌ That doesn't look like a valid Spotify link.")
        return

    status_msg = await update.message.reply_text("⏳ **Searching and Downloading...**")

    try:
        # 1. Run spotdl
        command = ["spotdl", user_link]
        subprocess.run(command, check=True)

        # 2. Find the MP3
        list_of_files = glob.glob('*.mp3') 
        
        if not list_of_files:
            await status_msg.edit_text("❌ Download failed.")
            return
            
        latest_file = max(list_of_files, key=os.path.getctime)
        
        await status_msg.edit_text("⬆️ **Uploading...**")

        # 3. Send Audio
        chat_id = update.message.chat_id
        await context.bot.send_audio(chat_id=chat_id, audio=open(latest_file, 'rb'))

        # 4. Cleanup
        os.remove(latest_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ Error: {e}")

if __name__ == '__main__':
    # Check for Token
    if not TOKEN:
        print("Error: TOKEN not set!")
        exit(1)

    # 1. Start the dummy web server in the background
    # This keeps Render happy so it doesn't kill the bot
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    # 2. Start the Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_spotify))

    print(f"Bot is starting on Port {PORT}...")
    application.run_polling()
