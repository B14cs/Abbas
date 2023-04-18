import requests
import json
import os
import threading


api_key = ''
telegram_token = ''
gpt_model = 'gpt-3.5-turbo'
chatbot_handle = '@xxxxxxxBOT'


def openAI(prompt):
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'model': gpt_model, 'messages': [
            {"role": "user", "content": prompt}], 'temperature': 0.5, 'max_tokens': 300}
    )

    result = response.json()

    final_result = ''
    for i in range(0, len(result['choices'])):
        final_result += result['choices'][i]['message']['content']

    return final_result


def telegram_bot_sendtext(bot_message, chat_id, msg_id):
    data = {
        'chat_id': chat_id,
        'text': bot_message,
        'reply_to_message_id': msg_id
    }
    response = requests.post(
        'https://api.telegram.org/bot' + telegram_token + '/sendMessage',
        json=data
    )
    return response.json()


def Chatbot():
    cwd = os.getcwd()
    filename = cwd + '/chatgpt.txt'
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("1")
    else:
        does_file_exist = "File Exists"

    with open(filename) as f:
        last_update = f.read()
    f.close()

    url = f'https://api.telegram.org/bot{telegram_token}/getUpdates?offset={last_update}'
    response = requests.get(url)
    data = json.loads(response.content)
    # data = response.json()
    for result in data['result']:
        try:
            if float(result['update_id']) > float(last_update):
                if not result['message']['from']['is_bot']:
                    last_update = str(int(result['update_id']))

                    msg_id = str(int(result['message']['message_id']))

                    chat_id = str(result['message']['chat']['id'])

                    prompt = result['message']['text']
                    # print(prompt)

                    if chatbot_handle in result['message']['text']:
                        prompt = result['message']['text'].replace(
                            chatbot_handle, "")

                    if 'reply_to_message' in result['message']:
                        if result['message']['reply_to_message']['from']['is_bot']:
                            prompt = result['message']['text']

                    bot_response = openAI(f"{prompt}")
                    # print(bot_response)

                    print(telegram_bot_sendtext(
                        bot_response, chat_id, msg_id))

        except Exception as e:
            print(e)

    with open(filename, 'w') as f:
        f.write(last_update)

    return "done"


def main():
    timertime = 5
    Chatbot()
    threading.Timer(timertime, main).start()


if __name__ == "__main__":
    main()
