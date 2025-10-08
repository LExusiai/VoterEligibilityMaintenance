# -*- coding: utf-8 -*-

import os

env = os.environ

family = 'wikipedia'
mylang = 'zh'
usernames['wikipedia']['zh'] = env['WPB_BOTUSERNAME']
authenticate['zh.wikipedia.org'] = (env['PWB_CONSUMER_TOKEN'], env['PWB_CONSUMER_SECRET'], env['PWB_ACCESS_TOKEN'],env['PWB_ACCESS_SECRET'])
