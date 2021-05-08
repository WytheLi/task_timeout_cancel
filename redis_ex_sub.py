# -*- coding: utf-8 -*-
# 基于redis过期key实现订单超时取消，返还库存
# vim /etc/redis/redis.conf
# notify-keyspace-events Ex
from redis import StrictRedis
import time

redis_conn = StrictRedis()
pubsub = redis_conn.pubsub()


def event_handler(msg):
    """
    key失效回调函数
    ps: {'type': 'pmessage', 'pattern': b'__keyevent@0__:expired',
            'channel': b'__keyevent@0__:expired', 'data': b'user_id+order_id'}
    获取失效消息中的order_id，查询订单表，返还库存，将订单记录状态设置为`取消态`
    :param msg:
    :return:
    """
    print(msg)


pubsub.psubscribe(**{'__keyevent@0__:expired': event_handler})


while True:
    pubsub.get_message()

    time.sleep(0.1)
