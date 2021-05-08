# -*- coding: utf-8 -*-
# Delay Queue
import json
import time
import uuid
import redis


class DelayQueue(object):
    """Redis延时队列"""
    QUEUE_KEY = 'delay_queue'
    DATA_PREFIX = 'queue_data'

    def __init__(self, conf):
        host, port, db = conf['host'], conf['port'], conf['db']
        self.client = redis.Redis(host=host, port=port, db=db)

    def push(self, data):
        """
        在push数据时，执行如下几步：
            1、生成一个唯一key，这里使用uuid4生成（uuid4是根据随机数生成的，重复概率非常小）
            2、把数据序列化后存入这个唯一key的String结构中
            3、把这个唯一key加到SortedSet中，score是当前时间戳
            4、这里利用SortedSet记录添加数据的时间，便于在获取时根据时间获取之前的数据，达到延迟的效果。
            而真正的数据则存放在String结构中，等获取时先拿到数据的key再获取真正的数据。
        :param data:
        """
        # 唯一ID
        task_id = str(uuid.uuid4())
        data_key = '{}_{}'.format(self.DATA_PREFIX, task_id)
        # save string
        self.client.set(data_key, json.dumps(data))
        # add zset(queue_key=>data_key,ts)
        self.client.zadd(self.QUEUE_KEY, data_key, int(time.time()))

    def pop(self, num=5, previous=3):
        """
        此pop是可以获取多条数据的，默认是获取延迟队列中20分钟前的5条数据，具体思路如下：
            1、计算previous秒前的时间戳，使用SortedSet的zrangebysocre方法获取previous秒之前添加的唯一key
            2、如果SortedSet中有数据，则利用Redis删除的原子性，使用zrem依次删除SortedSet的元素，如果删除成功，则使用，防止多进程并发执行此方法，拿到相同的数据
            3、拿到可用的唯一key，从String中获取真正的数据即可
            ps: 这里最重要的是第二步，在拿出SortedSet的数据后，一定要防止其他进程并发获取到相同的数据，所以在这里使用zrem依次删除元素，保证只有删除成功的进程才能使用这条数据。
        :param num: pop多少个
        :param previous: 获取多少秒前push的数据
        """
        # 取出previous秒之前push的数据
        until_ts = int(time.time()) - previous
        # zrangebyscore()返回有序集key中，所有score值介于min和max之间(包括等于min或max)的成员。有序集成员按score值递增(从小到大)次序排列。
        task_ids = self.client.zrangebyscore(self.QUEUE_KEY, 0, until_ts, start=0, num=num)
        if not task_ids:
            return []

        # 利用删除的原子性,防止并发获取重复数据
        pipe = self.client.pipeline()
        for task_id in task_ids:
            pipe.zrem(self.QUEUE_KEY, task_id)

        data_keys = [data_key for data_key, flag in zip(task_ids, pipe.execute())if flag]
        if not data_keys:
            return []

        # load data
        data = [json.loads(item) for item in self.client.mget(data_keys)]
        # delete string key
        self.client.delete(*data_keys)
        return data


if __name__ == '__main__':
    redis_conf = {'host': '127.0.0.1', 'port': 6379, 'db': 0}
    queue = DelayQueue(redis_conf)
    # push 20条数据
    # for i in range(20):
    #     item = {'user_id': 'order_id_{}'.format(i)}
    #     queue.push(item)

    while True:
        # 轮循获取队列中的数据
        data = queue.pop(num=10)
        print(data)
        time.sleep(0.1)
