#encoding: utf8

import pymorphy2

from telethon import TelegramClient, events
from datetime import datetime

from telethon.tl.functions import *
from telethon.tl.types import InputStickerSetID
from telethon import TelegramClient, events, utils, types

import threading
import os
import random
import sys
import logging
import asyncio

from variables import *

client = TelegramClient('zhabkabusyabot', API_ID, API_HASH).start(bot_token=BOT_TOKEN) # bot.session file will be created; do not delete!

logging.basicConfig(level=logging.ERROR)

# TODO: добавить команды боту

'''Функция, подставляющая слово в шаблонную фразу'''
def substitute(phrase, subs):
    res = ""
    morph = pymorphy2.MorphAnalyzer()
    print(morph.parse(subs))

    nom_grammems = set()
    nom_grammems.add(morph.parse(subs)[0].tag.gender)
    nom_grammems.add(morph.parse(subs)[0].tag.number)

    i = 0
    while i < len(phrase):
        if phrase[i] is 0:
            res += (morph.parse(subs)[0]).normalized.inflect(phrase[i+1]).word + " "
            i+=2
        elif phrase[i] is 1:
            grammems = phrase[i+1].copy()
            grammems.update(nom_grammems)
            print(grammems)
            print(morph.parse(phrase[i + 2])[0].inflect(grammems))
            res += morph.parse(phrase[i + 2])[0].inflect(grammems).word + " "
            i+=3
        else:
            res += phrase[i]+" "
            i+=1
    return res

''' Функция, исправляющая в строке-аргументе мелкие ошибки (напр., наличие пробела перед знаком препинания) '''
def correct(s):
    i = 0
    while i < len(s):
        if (s[i] in marks) and (i>0):
            if s[i-1] is " ":
                s = s[:i-1] + s[i:]
                i-=1
        i+=1
    return s

'''Получение ID последнего сообщения, отправленного в группу'''
def get_latest(_group):
    for group in groups:
        if group[0]==_group:
            return group[1]
    return 0

'''Обновление информации касательно ID последнего сообщения в конкретной группе'''
def update_group(_group, id):
    global groups
    for group in groups:
        if group[0]==_group:
            group[1]=id
            return
    groups.append([_group, id])

'''Жабофикация слова (например, дом => квом)'''
def froggify(word):
    up = word[0].isupper()
    whole_up = word.isupper()
    if up:
        word = word[0].lower() + word[1:]
    for ch in range(len(word)):
        if word[ch] in vowels:
            word = "кв" + word[ch:]
            break
    if up:
        word = word[0].upper() + word[1:]
    if whole_up:
        word = word.upper()
    return word

'''Обработчик события по получению нового сообщения:
    - обновить ID последнего сообщения в группе
    - проверить, загружен ли стикерпак, и загрузить в случае отсутствия
    - обновить сегодняшнюю дату
    - проверить на просьбу "Дай жабу" => ответить стикером
    - проверить на наличие подстроки "ква" => ответить кваканьем
    - проверить, ответил ли отправитель Жабке Бусе => жабофицировть его сообщение
    - рандом, определяющий, квакнет жаба просто так или нет
    - рандом, определяющий, скажет ли Жабка Буся умную фразу или нет 
'''
@client.on(events.NewMessage())
async def handlerNewMessage(event):
    global STICKER_SET, COUNTER, DATE, NOTIFIED
    update_group(event.message.to_id, event.message.id)

    morph = pymorphy2.MorphAnalyzer()
    words = event.message.message.split()

    if STICKER_SET is None:
        STICKER_SET = await client(messages.GetStickerSetRequest(
            stickerset=InputStickerSetID(
                id=STICKER_SET_ID,
                access_hash=STICKER_SET_HASH,
            )
        ))
        print(STICKER_SET)
    if event.message.date.day is not DATE:
        COUNTER=0
        NOTIFIED=0
        DATE=event.message.date.day

    try:
        if "Дай жабу" in event.message.message:
            await client.send_file(event.message.to_id, STICKER_SET.documents[0], reply_to=event.message.id)
        elif event.message.message == "Квакни":
            await client.send_file(entity=event.message.to_id, file=os.path.join(os.path.dirname(__file__), "croaks", "croak"+str(random.randint(0,0))+".mp3"),attributes=[types.DocumentAttributeAudio(
             duration=1,
             voice=True,
             waveform=utils.encode_waveform(bytes((1, 2, 4, 6, 8, 10, 20, 30, 40, 43, 44, 45, 44, 43, 40, 30, 20, 10, 8, 6, 4, 2, 1)) * 2))],reply_to=event.message.id)
        elif "ква" in (event.message.message).lower():
            await client.send_message(entity=event.message.to_id,
                                      message="Ква!")
        elif (event.message.reply_to_msg_id is not None) and (await client.get_messages(entity=event.message.to_id, ids=[event.message.reply_to_msg_id]))[0].from_id == ZHABKA_ID:
            reply = event.message.message.split(" ")
            await client.send_message(entity=event.message.to_id, message=" ".join([froggify(word) for word in reply]))
        elif random.randint(0,1000) < POSSIBILITY:
            await client.send_message(entity=event.message.to_id,
                                      message="Ква ква!",
                                      reply_to=event.message.id)
        elif random.randint(0,1000) < POSSIBILITY:
            target = "-"
            for w in words:
                if morph.parse(w)[0].tag.POS == "NOUN":
                    print(w + " - ")
                    print(morph.parse(w)[0].score)
                    target = w
                    break

            if target is not "-":
                mode = random.randint(0,1)
                print(target)
                if mode is 0:
                    phrase = random.randint(0,len(QUESTIONS)-1)
                    s = substitute(QUESTIONS[phrase], target)
                    print(s)
                else:
                    phrase = random.randint(0,len(EXCLAMAITIONS)-1)
                    s = substitute(EXCLAMAITIONS[phrase], target)
                    print(s)
                s = correct(s)
                print(s)
                await client.send_message(entity=event.message.to_id, message=s, reply_to=event.message.id)
    except Exception as e:
        print("Attention: the following error has occurred. \n ___________________________ \n")
        print(e)
        print("___________________________")
'''
Обработчик события по изменению сообщения
    - проверить давность отправки отредктированного сообщения
    - в случае давности отправить в группу предупреждение
'''
@client.on(events.MessageEdited())
async def handlerMessageEdited(event):
    print(event)
    _id = event.message.id
    _to_id = event.message.to_id
    _from_id = event.message.from_id
    _message = event.message.message
    print(_id - get_latest(_to_id), groups)
    if get_latest(_to_id) - _id > MAX_DIFFERENCE:
        await client.send_message(entity=_to_id, message="**ВНИМАНИЕ!** Вот это сообщение было отредактировано только что.", reply_to=event.message.id)

'''Запустить работу бота'''
client.start()
client.run_until_disconnected()
