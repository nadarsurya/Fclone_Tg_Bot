#!/usr/bin/python3
# -*- coding: utf-8 -*-
import copy
import logging

from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, Filters

from utils.config_loader import config
from utils.fire_save_files import thread_pool
from utils.restricted import restricted_admin

logger = logging.getLogger(__name__)


def init(dispatcher: Dispatcher):
    """Provide handlers initialization."""
    dispatcher.add_handler(CommandHandler('ban', ban, filters=Filters.chat(config.USER_IDS[0]), pass_args=True))
    dispatcher.add_handler(CommandHandler('unban', unban, filters=Filters.chat(config.USER_IDS[0]), pass_args=True))


@restricted_admin
def ban(update: Update, context: CallbackContext):
    if not context.args:
        if ban_list := context.bot_data.get('ban', None):
            update.message.reply_text('\n'.join(map(str, ban_list)))
        return
    if not context.args[0].isdigit:
        update.message.reply_text('/ban user_id')
        return
    user_id = int(context.args[0])
    if not context.bot_data.get('ban', None):
        context.bot_data['ban'] = [user_id]
    elif user_id not in context.bot_data['ban']:
        new_ban = copy.deepcopy(context.bot_data['ban'])
        new_ban.append(user_id)
        context.bot_data['ban'] = new_ban
    else:
        update.message.reply_text('Already exists on the blacklist.')
        return
    context.dispatcher.update_persistence()
    if tasks := thread_pool.get(user_id, None):
        for t in tasks:
            t.kill()
            logger.debug(f'Task {t.ident} was stopped due to user {user_id} is banned.')
            break
    update.message.reply_text('Added to the blacklist.')
    logger.info(f'{user_id} is banned.')
    return


@restricted_admin
def unban(update: Update, context: CallbackContext):
    if not context.args or not context.args[0].isdigit:
        update.message.reply_text('/unban user_id')
        return
    user_id = int(context.args[0])
    if user_id in context.bot_data.get('ban', []):
        new_ban = copy.deepcopy(context.bot_data['ban'])
        new_ban.remove(user_id)
        context.bot_data['ban'] = new_ban
        context.dispatcher.update_persistence()
        update.message.reply_text('Removed from the blacklist.')
        logger.info(f'{user_id} is unbanned.')
    else:
        update.message.reply_text('The user is not on the blacklist.')

    return
