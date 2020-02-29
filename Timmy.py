import discord
import asyncio
import time
import random
import heapq

client = discord.Client()


class War:
    def __init__(self, name, user, start_time, end_time):
        self.name = name
        self.user = user
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        message = f'War: {self.name.strip()}. '
        if self.start_time > time.time():
            converted_time = convert_time_difference_to_str(self.start_time - time.time())
            message += f'Starting in {converted_time}'
        else:
            converted_time = convert_time_difference_to_str(self.end_time - time.time())
            message += f'{converted_time} remaining'
        return message


class Event:
    def __init__(self, name, channel):
        self.name = name
        self.channel = channel
        self.events = []
        heapq.heapify(self.events)
        self.current = []

    def __contains__(self, item):
        if item in self.events or item in self.current:
            return True
        return False

    def __str__(self):
        msg = ''
        for event in self.current:
            msg += f'Event {self.name} in {convert_time_difference_to_str(event-time.time())} \n'
        for event in self.events:
            msg += f'Event {self.name} in {convert_time_difference_to_str(event-time.time())} \n'
        return msg

    def push(self, item):
        heapq.heappush(self.events, item)

    async def run_event(self):
        while len(self.events) > 0 and events[self.name] == self:
            event_time = heapq.heappop(self.events)
            self.current.append(event_time)
            wait = event_time - time.time()
            await asyncio.sleep(wait)
            self.current.remove(event_time)
            await post_message(self.channel, self.name)


@client.event
async def on_message(message):
    message_string = message.content.lower()

    # Wars
    if message_string.startswith('!startwar') and in_slagmark(message):
        msgin = message.content.split()
        war_ins, str_start = split_input_variables(msgin[1:], war_defaults)

        name = get_name_string(msgin[str_start:], message)
        if name in wars:
            await message.channel.send('A war with that name already exists, please use a different name or end the current war.')
            return

        war_len = war_ins[0] * minute_length
        wait_len = war_ins[1] * minute_length
        this_war = War(name, message.author, time.time() + wait_len, time.time() + wait_len + war_len)
        wars[name] = this_war

        await post_message(message.channel, f'War: {name} is starting in {convert_time_difference_to_str(wait_len)}')
        if wait_len >= 5 * minute_length:
            delay_countdown = minute_length/2
            await asyncio.sleep(wait_len - delay_countdown)
            if in_war(name, this_war):
                user_mentions = await get_reactions_as_mentions(message, False)
                await post_message(message.channel, f'War: {name} starts in {convert_time_difference_to_str(delay_countdown)}'
                                                    f' Get ready! {user_mentions}')
                await asyncio.sleep(delay_countdown)
        else:
            await asyncio.sleep(wait_len)

        if in_war(name, this_war):
            user_mentions = await get_reactions_as_mentions(message, False)
            await post_message(message.channel, f'Start! War: {name} is on for {convert_time_difference_to_str(war_len)}'
                                                f' {user_mentions}')

            for interval in war_len_intervals:
                if not in_war(name, this_war):
                    return
                if war_len <= minute_length:
                    await asyncio.sleep(war_len)
                    break
                if war_len > interval:
                    diff = war_len - interval
                    await asyncio.sleep(diff)
                    if not in_war(name, this_war):
                        return
                    war_len = interval
                    user_mentions = await get_reactions_as_mentions(message, True)
                    await post_message(message.channel, f'War: {name} has {convert_time_difference_to_str(war_len)}'
                                                        f' remaining. {user_mentions}')

            if in_war(name, this_war):
                user_mentions = await get_reactions_as_mentions(message, False)
                await post_message(message.channel, f'War: {name} has ended! {user_mentions}')
                wars.pop(name)

    if message_string.startswith('!endwar') and in_slagmark(message):
        name = message.content.split()
        name = get_name_string(name[1:], message)
        if name in wars:
            if wars[name].user == message.author:
                wars.pop(name)
                msgout = f'War {name} cancelled'
            else:
                msgout = 'You can only end your own wars.'
        else:
            msgout = 'No war with that name.'
        await post_message(message.channel, msgout)

    # TODO: consolidate listing
    if message_string.startswith('!listwars'):
        if len(wars) > 0:
            msg = ''
            for key in wars:
                msg += wars[key].__str__() + '\n'
            await post_message(message.channel, msg)
        else:
            await message.channel.send('No wars at this time')

    if message_string.startswith('!no-countdown'):
        if is_role(message.author, ['No-Countdown']):
            await message.author.remove_roles(discord.utils.get(message.author.guild.roles, name='No-Countdown'))
        else:
            await message.author.add_roles(discord.utils.get(message.author.guild.roles, name='No-Countdown'))

    # Wordcount
    if message_string.startswith('!words'):
        msgin = message.content.split()
        msgout = ''

        try:
            user_wordcount = int(msgin[1])
            if message.author in user_wordcounts:
                words_written = user_wordcount - user_wordcounts[message.author]
                msgout += f'{message.author.mention}. You wrote {words_written} words. '
                user_wordcounts.pop(message.author)
                try:
                    session_len = int(msgin[2])
                    wpm = float(words_written/session_len)
                    msgout += f'Your wpm is {round(wpm)}. '
                except (IndexError, ValueError):
                    pass

                diff_to_goal = 0
                has_alt_goal = True
                try:
                    alt_goal = int(msgin[3])
                    diff_to_goal = user_wordcount - alt_goal
                except ValueError:
                    has_alt_goal = False
                except IndexError:
                    day = time.localtime()
                    if day[1] == november:
                        diff_to_goal = user_wordcount - get_word_count()
                    else:
                        has_alt_goal = False
                finally:
                    if has_alt_goal:
                        msgout += "You're "
                        if diff_to_goal == 0:
                            msgout += 'exactly on target'
                        else:
                            msgout += str(abs(diff_to_goal))
                            if diff_to_goal > 0:
                                msgout += ' ahead of'
                            elif diff_to_goal < 0:
                                msgout += ' behind'
                            msgout += ' the goal for the day'

            else:
                user_wordcounts[message.author] = user_wordcount

        except (IndexError, ValueError):
            msgout += 'Please provide a valid wordcount'

        await post_message(message.channel, msgout)

    # Roll
    if message_string.startswith('!d') and not message_string.endswith('n') and not in_slagmark(message):
        # TODO: make this check if string.startswith('!d ') or ends with number?
        try:
            num = int(message.content[2:])
        except (ValueError, IndexError):
            num = 6
        ran_num = random.randint(1, num)
        await message.channel.send(ran_num)

    # Throw
    if message_string.startswith('!foof') and not in_slagmark(message):
        await message.channel.send('Righto... ')
        await asyncio.sleep(1.5)
        await message.channel.send('**Timmy** surreptitiously works his way over to the couch, looking ever so casual...')
        await asyncio.sleep(5)
        ran = random.randint(0, len(pillows) - 1)
        try:
            mention = message.mentions[0].mention
        except IndexError:
            mention = message.author.mention
        await message.channel.send(f'**Timmy** grabs a {pillows[ran]} pillow, and throws it at {mention},'
                                   ' hitting them squarely in the back of the head.')

    # Events
    if message_string.startswith('!makeevent') and is_role(message.author, admin_roles) and not in_slagmark(message):
        if '{' in message.content and message.content.endswith('}'):
            msgin = message.content.split('{')
            msg = (msgin[0]).split()
            msg = get_name_string(msg[1:], message)

            if msg != '':
                time_in = str(msgin[1]).replace('}', '')
                time_in = time_in.split(', ')

                for date in time_in:
                    try:
                        converted_time = (time.mktime(time.strptime(date, '%Y-%m-%d %H:%M')))
                        if converted_time > time.time():
                            if msg in events:
                                if converted_time in events[msg]:
                                    await post_message(message.channel, f'Date {date} is already set for this event.')
                                else:
                                    events[msg].push(converted_time)
                                    await post_message(message.channel, f'Event {msg} set for {date}')
                            else:
                                events[msg] = Event(msg, message.channel)
                                events[msg].push(converted_time)
                                await post_message(message.channel, f'Event {msg} set for {date}')
                        else:
                            await post_message(message.channel, f'Date {date} is in the past. Make sure you format it'
                                                                f' correctly')
                    except ValueError:
                        await post_message(message.channel, f'Date {date} was formatted incorrectly')
                await events[msg].run_event()
                return
        await message.channel.send('Events must be formatted as !MakeEvent <message> <{YYYY-MM-DD HH:MM}>')

    if message_string.startswith('!listevents') and is_role(message.author, admin_roles) and not in_slagmark(message):
        if len(events) > 0:
            msg = ''
            for key in events:
                msg += events[key].__str__()
            await post_message(message.channel, msg)
        else:
            await message.channel.send('No events at this time')

    # Spam
    if message_string.startswith('!spam') and is_role(message.author, admin_roles) and not in_slagmark(message):
        msgin = message.content.split()
        freq_list, str_start = split_input_variables(msgin[1:], spam_defaults)

        freq = freq_list[0] * minute_length
        try:
            if msgin[str_start]:
                msg = get_name_string(msgin[str_start:], message)
                if msg != '':
                    spam_dict[msg] = freq
                    await post_ml(message, msg)
        except IndexError:
            await message.channel.send('Please include a message')

    if message_string.startswith('!listspam') and is_role(message.author, admin_roles) and not in_slagmark(message):
        if len(spam_dict) > 0:
            msg = ''
            for spam in spam_dict:
                msg += f'{spam} every {convert_time_difference_to_str(spam_dict[spam])} \n'
            await post_message(message.channel, msg)
        else:
            await message.channel.send('No ongoing spam')

    # stopping
    if message_string.startswith('!stop') and is_role(message.author, admin_roles):
        msgin = message.content.split()
        msg = get_name_string(msgin[1:], message)
        msgout = ''
        for param in params:
            if msg in params[param]:
                params[param].pop(msg)
                msgout += f'{param}: {msg} stopped \n'
        if msgout == '':
            msgout += 'No spam or event with that name'
        await post_message(message.channel, msgout)

    if message_string.startswith('!nuke') and is_role(message.author, admin_roles):
        msgin = message.content.split()
        params_in = msgin[1:]
        msgout = ''

        if len(params_in) == 0:
            params_in = ['wars', 'spam', 'events']
        if params_in[0] not in params:
            return
        for in_param in params_in:
            for param in params:
                if in_param == param:
                    msgout += f'All {param} ended \n'
                    params[param].clear()
                    break
        await message.channel.send(msgout)

    # Hydra
    if message_string.startswith('!hydra'):
        msgin = message.content.split()
        try:
            year = int(msgin[1])
        except (ValueError, IndexError):
            year = 0

        if year in year_end:
            if year - 1 == year_before_first:
                value_bottom = 0
            else:
                value_bottom = year_end[year-1]
            value = random.randint(value_bottom, year_end[year])
        else:
            value = random.randint(0, len(hydras)-1)

        await post_message(message.channel, hydras[value])

    if message_string.startswith('!abuse') and is_role(message.author, admin_roles):
        k = 0
        msg = ''
        for i in range(6000):
            msg += str(k)
            k += 1
            if k == 9:
                k = 0
        await post_message(message.channel, msg)

    # !reply
    elif message_string.startswith('!'):
        incommand = message.content.lower().split('!')
        if incommand[1] in commands:
            if type(commands[incommand[1]]) is list:
                await message.channel.send(content=commands[incommand[1]][0], file=commands[incommand[1]][1])
                return
            try:
                await post_message(message.channel, commands[incommand[1]]())
            except TypeError:
                await post_message(message.channel, (commands[incommand[1]]))


async def post_message(channel, msgin):
    if msgin == '':
        return
    if len(msgin) < char_limit:
        await channel.send(msgin)
    else:
        messages = []
        amount, remainder = divmod(len(msgin), char_limit)
        for i in range(amount):
            messages.append(msgin[0:char_limit])
            msgin = msgin[char_limit:len(msgin)]
        messages.append(msgin)  # TODO: Does this work?
        for msgout in messages:
            await channel.send(msgout)


async def post_ml(message, spam):
    while spam in spam_dict:
        await post_message(message.channel, spam)
        await asyncio.sleep(spam_dict[spam])


async def get_reactions_as_mentions(message, no_countdown):
    if no_countdown and is_role(message.author, ['No-Countdown']):
        user_mention = ''
    else:
        user_mention = message.author.mention
    for r in message.reactions:
        async for user in r.users():
            if no_countdown and is_role(user, ['No-Countdown']):
                continue
            user_mention += ' ' + str(user.mention)
    return user_mention


def get_name_string(msg_list, message):
    msg = ''
    for i in msg_list:
        msg = msg + i + ' '

    if msg == '' and message.content.lower().startswith('!startwar'):
        msg += get_prompt()

    return msg.strip()


def is_role(user, roles):
    for role in roles:
        if role in [role.name for role in user.roles]:
            return True
    return False


def in_slagmark(message):
    if message.channel.name == '🔱slagmark':
        return True
    return False


def convert_time_difference_to_str(diff):
        msg = ''
        for duration in duration_lengths:
            if int(diff) >= duration[0]:
                amount, diff = divmod(diff, duration[0])
                msg += f'{int(amount)} {duration[1]}'
                if amount > 1:
                    msg += 's'
                if diff >= 1:
                    msg += ', '
        return msg


def split_input_variables(list_of_strings, list_of_vars):
    num_vars = len(list_of_vars) + 1
    return_list = []
    for i in range(0, len(list_of_vars)):
        try:
            return_list.append(float(list_of_strings[i]))
        except (ValueError, IndexError):
            return_list.append(list_of_vars[i][1])
            num_vars -= 1
    return return_list, num_vars


def in_war(name, war):
    if name in wars:
        if wars[name] == war:
            return True
    return False


def get_prompt():
    ran = random.randint(0, len(prompts) - 1)
    return prompts[ran]


def get_word_count():
    day = time.localtime()
    if day[1] == november:
            return nano_wordcounts[day[2] - 1]


@client.event
async def on_ready():
    while True:
        day = time.localtime()
        if day[1] == november:
            status = f'Goal: {get_word_count()}'
        else:
            status = get_prompt()

        await client.change_presence(activity=discord.Game(name=status))
        print('Yay')
        print(day)
        time_past_midnight = day[3]*3600 + day[4]*60 + day[5]
        print(time_past_midnight)
        time_to_midnight = 86400 - time_past_midnight
        print(time_to_midnight)
        await asyncio.sleep(time_to_midnight)


wars = {}
spam_dict = {}
events = {}
params = {'wars': wars, 'spam': spam_dict, 'events': events}
user_wordcounts = {}

char_limit = 2000
november = 11
minute_length = 60
spam_defaults = [('freq', 30)]
war_defaults = [('war_len', 10), ('wait_len', 1)]
war_len_intervals = [120, 60, 30, 20, 10, 5, 1,  0]
war_len_intervals = [interval * minute_length for interval in war_len_intervals]
duration_lengths = [(86400, 'day'), (3600, 'hour'), (60, 'minute'), (1, 'second')]
nano_wordcounts = [1667, 3333, 5000, 6667, 8333, 10000, 11667, 13333, 15000, 16667, 18333, 20000, 21667, 23333, 25000,
                   26667, 28333, 30000, 31667, 33333, 35000, 36667, 38333, 40000, 41667, 43333, 45000, 46667, 48333, 50000]

pillows = []
reading = open('pillowlist.txt', 'r')
for pillow in reading:
    pillows.append(pillow.strip())
reading.close()

prompts = []
reading = open('prompts.txt', 'r')
for prompt in reading:
    prompts.append(prompt)
reading.close()

commands = {'starwar': 'A long time ago, in a galaxy far far away.',
            'cheer': 'You can do it! '
                     'https://38.media.tumblr.com/91599091501f182b0fbffab90e115895/tumblr_nq2o6lc0Kp1s7widdo1_250.gif',
            'woot': 'cheers! Hooray!',
            'help': 'Check the pinned message in #🤖skrivebot',  # TODO: fix this link
            'count word': 'https://cdn.discordapp.com/attachments/526175173867732993/636293153229373470/IMG_20191022_220137.jpg',
            'bart i sjela': 'så da er det bart i sjela, komma i hjertet, tastatur i fingrene, fyllepenn i milten og lommer på skjørtet. '
                            'snart har vi en full person med dette',
            'pisk': '<:pisk:556560214590095361>',
            'crawl': 'https://docs.google.com/spreadsheets/d/12gmpjrQtaOqE7xwaVExiyYbfUZ1QjY4cJFPRZ0NRrj0/edit?usp=sharing%22',
            'jeg har trua på deg': "I've threatened you",
            'belinda': 'https://www.amazon.com/dp/B07D1JQ664/?tag=097-20&ascsubtag=v7_1_29_g_4j8r_4_x01_-srt5- \n'
                       'https://www.flickr.com/photos/caroslines/760491974',
            'domherren': 'https://www.fuglelyder.net/dompap/',
            'paven': 'http://m.ocdn.eu/_m/a68e24c99236c40d6f9d01823a4b7ebe,14,1.jpg',
            'prompt': get_prompt,
            'wordcount': get_word_count,
            'ml': ':lizard:',
            'møbelet': ['Det er et møbel. Med ansikt. Og det hater meg.', discord.File('møbelet.jpg')]
            }

year_before_first = 2018
year_end = {2019: 16}  # , 2020: 90}
hydras = []
reading = open('hydras.txt', encoding="utf8")
for hydra in reading:
    hydras.append(hydra)
reading.close()

admin_roles = ['ML', 'Local Wolfboy']

reading = open('key.txt', 'r')
TOKEN = reading.readline().strip()
reading.close()

client.run(TOKEN)