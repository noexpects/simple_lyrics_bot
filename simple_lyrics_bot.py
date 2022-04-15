import telebot
import config
import pickle
from lyrics_scrapper import LyricsParser

from telebot import types

scrapper = LyricsParser()
bot = telebot.TeleBot(config.TOKEN)

with open('data.pickle', 'rb') as f:
    data_new = pickle.load(f)

search_results = data_new[0]
father_function = data_new[1]
next_result_page_href = data_new[2]
name_of_artist = data_new[3]
previous_result_page_href = data_new[4]


def update_global_vars(chat_id, data, father_func, artist_name=None, next_page_link=None, current_page_link=None):
    search_results[chat_id].clear()
    search_results[chat_id] = data

    father_function[chat_id].clear()
    father_function[chat_id].append(father_func)

    if artist_name:
        name_of_artist[chat_id].clear()
        name_of_artist[chat_id].append(artist_name)

    if next_page_link:
        next_result_page_href[chat_id].clear()
        next_result_page_href[chat_id].append(next_page_link)

    if current_page_link:
        previous_result_page_href[chat_id].append(current_page_link)

    current_data = [search_results, father_function, next_result_page_href, name_of_artist, previous_result_page_href]
    with open('data.pickle', 'wb') as file:
        pickle.dump(current_data, file)


@bot.message_handler(commands=['start'])
def welcome(message):
    search_results[message.chat.id] = []
    father_function[message.chat.id] = []
    next_result_page_href[message.chat.id] = []
    name_of_artist[message.chat.id] = []
    previous_result_page_href[message.chat.id] = []

    bot.send_message(message.chat.id,
                     "Welcome, <b>{0.first_name}</b>!\nI am <b>{1.first_name}</b>, a bot designed to find lyrics. Just send "
                     "me song title, artist or lyrics and I'll try to find it. 🙂".format(message.from_user, bot.get_me()),
                     parse_mode='html')


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons is None:
        footer_buttons = [types.InlineKeyboardButton("❌", callback_data="close")]
    menu.append(footer_buttons)
    return menu


@bot.message_handler(content_types=['text'])
def song_search(message):
    if message.chat.type == 'private':
        results = scrapper.parse_search(message.text)
        previous_result_page_href[message.chat.id].clear()
        if type(results) == str:
            bot.send_message(message.chat.id, "Sorry, no results found")
        else:
            update_global_vars(chat_id=message.chat.id,
                               data=results,
                               father_func="song_search")
            reply_message = ""
            reply_message+= "<b>Best result:</b> \n"+results[0][0]+"\n\nTracks:\n"
            markup_items = []
            header_button = [types.InlineKeyboardButton("Best result", callback_data="best")]
            for x in results[1]:
                reply_message += "<b>"+str(results[1].index(x)+1)+'</b>. '+x[0]+"\n"
                markup_items.append(types.InlineKeyboardButton(str(results[1].index(x)+1), callback_data=str(results[1].index(x))))

            markup=types.InlineKeyboardMarkup(build_menu(markup_items, n_cols=5, header_buttons=header_button))
            bot.send_message(chat_id=message.chat.id,
                             text=reply_message,
                             parse_mode='html',
                             reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == "best":
                if search_results[call.message.chat.id][0][1] == search_results[call.message.chat.id][1][0][1]:
                    reply_message = parse_text(chat_id=call.message.chat.id,
                                               track_number=0)
                    if reply_message == 'Sorry, lyrics are not available.':
                        bot.answer_callback_query(callback_query_id=call.id,
                                                  show_alert=True,
                                                  text=reply_message)
                    else:
                        markup=types.InlineKeyboardMarkup(build_menu([],n_cols=1))
                        bot.send_message(chat_id=call.message.chat.id,
                                         text=reply_message,
                                         parse_mode="html",
                                         reply_markup=markup)
                    bot.answer_callback_query(call.id)
                else:
                    parse_artist_titles(artist_name=search_results[call.message.chat.id][0][0][:-8],
                                        artist_link=search_results[call.message.chat.id][0][1],
                                        call=call)
                    bot.answer_callback_query(call.id)
            elif call.data == "close":
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
            elif call.data == "forward_btn":
                parse_artist_titles(artist_name=name_of_artist[call.message.chat.id][0],
                                    artist_link=next_result_page_href[call.message.chat.id][0][0],
                                    call=call)
                bot.answer_callback_query(call.id)
            elif call.data == "back_btn":
                try:
                    parse_artist_titles(artist_name=name_of_artist[call.message.chat.id][0],
                                        artist_link=previous_result_page_href[call.message.chat.id][-2],
                                        call=call,
                                        button_caller="back_btn")
                    del previous_result_page_href[call.message.chat.id][-1]
                    bot.answer_callback_query(call.id)
                except IndexError:
                    bot.answer_callback_query(callback_query_id=call.id,
                                              show_alert=False,
                                              text="You are already on the first page.")
            else:
                reply_message = parse_text(call.message.chat.id, call.data)
                if reply_message == 'Sorry, lyrics are not available.':
                    bot.answer_callback_query(callback_query_id=call.id, show_alert=True, text=reply_message)
                else:
                    markup=types.InlineKeyboardMarkup(build_menu([],n_cols=1))
                    bot.send_message(chat_id=call.message.chat.id,
                                     text=reply_message,
                                     parse_mode="html",
                                     reply_markup=markup)
                    bot.answer_callback_query(call.id)
    except Exception as e:
        print(repr(e))


def parse_text(chat_id, track_number):
    reply_message = ""
    if father_function[chat_id][0] == "song_search":
        song_lyrics = scrapper.parse_text(search_results[chat_id][1][int(track_number)])
        reply_message += "<b>"+str(search_results[chat_id][1][int(track_number)][0])+"</b>\n\n"
    else:
        song_lyrics = scrapper.parse_text(search_results[chat_id][int(track_number)])
        reply_message += "<b>"+str(name_of_artist[chat_id][0])+"- "+str(search_results[chat_id][int(track_number)][0]) + "</b>\n\n"

    if song_lyrics == 'Sorry, lyrics are not available.':
        reply_message = song_lyrics
    else:
        if type(song_lyrics) == list:
            for x in song_lyrics:
                reply_message += x+"\n"
        else:
            reply_message += song_lyrics
    return reply_message


def parse_artist_titles(artist_name, artist_link, call, button_caller=None):
    artist_titles, next_page_adress = scrapper.parse_artist(artist_link)
    update_global_vars(data=artist_titles,
                       father_func="artist_search",
                       artist_name=artist_name,
                       next_page_link=next_page_adress,
                       current_page_link=artist_link if not button_caller else None,
                       chat_id=call.message.chat.id)
    reply_message = ""
    reply_message+= "<b>{0} tracks Page {1}:</b>\n".format(artist_name, int(previous_result_page_href[call.message.chat.id].index(artist_link))+1)
    markup_items = []

    for x in artist_titles:
        reply_message += "<b>"+str(artist_titles.index(x)+1)+'</b>. '+x[0]+"\n"
        markup_items.append(types.InlineKeyboardButton(str(artist_titles.index(x)+1),
                                                       callback_data=str(artist_titles.index(x))))

    footer_buttons = [types.InlineKeyboardButton("⬅️", callback_data="back_btn"),
                      types.InlineKeyboardButton("❌", callback_data="close"),
                      types.InlineKeyboardButton("➡️", callback_data="forward_btn")]
    markup=types.InlineKeyboardMarkup(build_menu(markup_items, n_cols=5, footer_buttons=footer_buttons))
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=reply_message,
                          parse_mode='html',
                          reply_markup=markup)


bot.polling(none_stop=True)  # RUN
