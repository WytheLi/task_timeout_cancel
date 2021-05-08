### 订单30分钟未支付,系统自动超时关闭有哪些实现方案?
1. 基于任务调度实现,效率是非常低,耗服务器性能
2. 基于redis过期key实现.用户下单的时候,生成一个令牌(有效期)30分钟,存放到我们redis;
redis.set(orderToken ,orderID) 下单时候存放到redis,并存储id入库,30分钟过期,
redis客户端监听,过期获取到orderId,拿orderId去查订单,没有支付则,订单关闭,库存增加
缺点:非常冗余 ,会在表中存放一个冗余字段 https://blog.csdn.net/zhangshengqiang168/article/details/104925649

3. 基于redis延迟队列   https://blog.csdn.net/zhangshengqiang168/article/details/100130523
4. 基于MQ的延迟队列实现(最佳)    死信队列(延迟队列)
原理:当我们在下单的时候,往MQ投递一个消息设置有效期为30分钟,但该消息失效的时候(没有被消费的情况下),
执行我们客户端一个方法告诉我们该消息已经失效,这时候查询这笔订单是否有支付.     

MQ的延迟队列实现原理(消息过期投递到死信队列)
原理:下单投放消息到A交换机(过期时间30分钟),消息到aa队列(绑定死信交换机),不设置aa队列的消费者(故此消息一直未消费).
30分钟后,过期消息投递到死信交换机,死信队列,由死信消费者消费,判断订单id是否支付,执行业务逻辑,支付->return 
未支付->关闭订单,返还库存
————————————————
版权声明：本文为CSDN博主「zhangshengqiang168」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/zhangshengqiang168/article/details/104718979


### 参考文档
- [RabbitMQ实现订单30分钟超时自动关闭](https://blog.csdn.net/zhangshengqiang168/article/details/104718979)
- [使用Redis的Key过期回调 ,实现订单超时关闭](https://blog.csdn.net/zhangshengqiang168/article/details/104925649)
- [redis延迟队列,处理正常订单超时自动关闭](https://blog.csdn.net/zhangshengqiang168/article/details/100130523)
- [Python实现订单超时自动取消](https://blog.csdn.net/itcast_cn/article/details/93215416)
