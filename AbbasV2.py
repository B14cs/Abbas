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

    # Get a list of all the file paths that ends with .txt from in specified directory
    fileList = glob.glob('*.oga')
    fileList2 = glob.glob('*.wav')
    # Iterate over the list of filepaths & remove each file.
    for filePath, filePath2 in zip(fileList, fileList2):
        try:
            os.remove(filePath)
            os.remove(filePath2)
        except:
            print("Error while deleting file : ", filePath)

    # os.remove('*.oga')
    # os.remove('*.wav')


listOfNames = ["\"مساعد\"", "\"`ذكي`\"", "\"محادث\"", "\"مساعد\" أو \"ذكي\" أو \"محادث\""]
listOfNamesEN = ["\"OpenAI\"", "\"AI assistant\"", "OpenAI", "\'AI\'"]


def generate_gpt_response():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages_list)

    result = completion.choices[0].message["content"]


    if "created by" in result:
        result = result.replace("OpenAI", "@B14_cs")
    if "تم إنشاؤي" in result:
        result = result.replace("OpenAI", "@B14_cs")
    if "name" in result:
        for substring in listOfNamesEN:
            if substring in result:
                result = result.replace(substring, "Abbas")
    elif "اسم" in result:
        for substring in listOfNames:
            if substring in result:
                result = result.replace(substring, "عباس")

    return result


async def get_audio_transcription(update, context):
    new_file = await download_audio(update, context)
    voice = convert_audio_to_wav(new_file)
    transcript = openai.Audio.transcribe("whisper-1", voice)
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
    # os.remove(audio_file + ".wav")
    # os.remove(audio_file + ".oga")
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
