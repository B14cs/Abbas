import openai
import os
import glob
import logging


from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
)

from pydub import AudioSegment

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

telegram_token = ''
openai.api_key = ''

gpt_model = 'gpt-3.5-turbo'
speech_recognition_model = 'whisper-1'

messages_list = []


def append_history(content, role):
    messages_list.append({"role": role, "content": content})
    return messages_list


def clear_history():
    messages_list.clear()
    return messages_list


async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thinking = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🤔"
    )
    append_history(update.message.text, "user")

    response = generate_gpt_response()

    append_history(response, "assistant")
    await context.bot.deleteMessage(
        message_id=thinking.message_id, chat_id=update.message.chat_id
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def process_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transcript = await get_audio_transcription(update, context)
    append_history(transcript, "user")

    response = generate_gpt_response()

    append_history(response, "assistant")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

    fileList = glob.glob('*.oga')
    fileList2 = glob.glob('*.wav')
    for filePath, filePath2 in zip(fileList, fileList2):
        try:
            os.remove(filePath)
            os.remove(filePath2)
        except:
            print("Error while deleting file : ", filePath)


def generate_gpt_response():
    completion = openai.ChatCompletion.create(
        model=gpt_model, messages=messages_list)
    return completion.choices[0].message["content"]


async def get_audio_transcription(update, context):
    new_file = await download_audio(update, context)
    voice = convert_audio_to_wav(new_file)
    transcript = openai.Audio.transcribe(speech_recognition_model, voice)
    return transcript["text"]


async def reset_history(update, context):
    clear_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Messages history cleaned"
    )
    return messages_list


async def download_audio(update, context):
    file_id = update.message.voice.file_id
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(f"{file_id}.oga")
    return file_id


def convert_audio_to_wav(audio_file):
    with open(f"{audio_file}.oga", "rb") as f:
        voice = AudioSegment.from_ogg(f)
    voice_wav = voice.export(f"{audio_file}.wav", format="wav")
    return voice_wav


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_token).build()
    text_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), process_text_message
    )
    application.add_handler(text_handler)

    application.add_handler(CommandHandler("reset", reset_history))

    audio_handler = MessageHandler(filters.VOICE, process_audio_message)
    application.add_handler(audio_handler)

    application.run_polling()
