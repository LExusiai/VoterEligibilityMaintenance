# -*- coding: utf-8 -*-

import os

env = os.environ

family = 'wikipedia'
mylang = 'zh'
usernames['wikipedia']['zh'] = env['botusername']
authenticate['zh.wikipedia.org'] = (env['PWB_consumer_token'], env['PWB_consumer_secret'], env['PWB_access_token'],env['PWB_access_secret'])
