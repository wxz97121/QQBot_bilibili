# -*-coding:utf8-*-


import nonebot
from aiocqhttp.exceptions import Error as CQHttpError
from datetime import datetime,date,timedelta
import random
import requests
import json,collections,xml
from lxml import etree
import time

#TODO：Config file, data file.


# 用户看这里
# 你只需要改这里的配置，就可以让你的 Bot 在指定QQ群发送指定 B站UP主 的消息
# 如下面所示，提供了两个 B站用户的消息推送
# 第一个用户是 虚拟主播轴伊，她的 B站uid 是 423728837，她的消息会被推送到 950253287,849437495 这两个QQ群
# 第二个用户是 虚幻引擎官方账号，它的 B站uid 138827797， 它的消息会被推送到 456247757 这个QQ群
VR_uid_list=[423728837,138827797]
VR_group_list=[
    [950253287,849437495],[456247757]]
VR_name_list=['轴伊','虚幻引擎']

# 你只需要改这里的配置，就可以让你的 Bot 在指定QQ群发送指定 微博用户 的消息
wb_uid_list=[7287111107,6880809286]
wb_group_list=[[950253287],[950253287,849437495]]
wb_name_list=['Epic Games Store','轴伊']

#我也知道这个配置方式有点蠢，有时间重写一个吧_(:з」∠)_

@nonebot.scheduler.scheduled_job('interval',minutes=1)
async def _():
    bot = nonebot.get_bot()
    for i in range(min(len(VR_uid_list),len(VR_group_list))):
        res=''
        dynamic_content = GetDynamicStatus(VR_uid_list[i], i)
        for content in dynamic_content:
            try:
                for groupnum in VR_group_list[i]:
                    res = await bot.send_group_msg(group_id=groupnum, message=content)
            except CQHttpError as e:
                pass
        room_id = get_live_room_id(VR_uid_list[i])
        live_status = GetLiveStatus(room_id)
        if live_status != '':
            for groupnum in VR_group_list[i]:
                await bot.send_group_msg(group_id=groupnum, message=VR_name_list[i] +' 开播啦啦啦！！！ ' + live_status)
    
    for i in range(min(len(wb_uid_list),len(wb_group_list))):
        wb_content = GetWeibo(wb_uid_list[i], i)
        for content in wb_content:
            try:
                for groupnum in wb_group_list[i]:
                    res = await bot.send_group_msg(group_id=groupnum, message=content)
            except CQHttpError as e:
                pass

def get_live_room_id(mid):
    res = requests.get('https://api.bilibili.com/x/space/acc/info?mid='+str(mid)+'&jsonp=jsonp')
    res.encoding = 'utf-8'
    res = res.text
    data = json.loads(res)
    data = data['data']
    roomid = 0
    try:
        roomid = data['live_room']['roomid']
    except:
        pass
    return roomid

def get_long_weibo( id):
    """获取长微博"""
    for i in range(5):
        url = 'https://m.weibo.cn/detail/%s' % id
        html = requests.get(url).text
        html = html[html.find('"status":'):]
        html = html[:html.rfind('"hotScheme"')]
        html = html[:html.rfind(',')]
        html = '{' + html + '}'
        js = json.loads(html, strict=False)
        weibo_info = js.get('status')
        if weibo_info:
            weibo = parse_weibo(weibo_info)
            return weibo
        time.sleep(random.randint(6, 10))

def parse_weibo(weibo_info):
    weibo = collections.OrderedDict()
    if weibo_info['user']:
        weibo['user_id'] = weibo_info['user']['id']
        weibo['screen_name'] = weibo_info['user']['screen_name']
    else:
        weibo['user_id'] = ''
        weibo['screen_name'] = ''

    text_body = weibo_info['text']
    selector = etree.HTML(text_body)
    weibo['text'] = etree.HTML(text_body).xpath('string(.)')
    weibo['article_url'] = get_article_url(selector)
    weibo['pics'] = get_pics(weibo_info)
    #return standardize_info(weibo)
    return weibo

def get_article_url(selector):
    """获取微博中头条文章的url"""
    article_url = ''
    text = selector.xpath('string(.)')
    if text.startswith(u'发布了头条文章'):
        url = selector.xpath('//a/@data-url')
        if url and url[0].startswith('http://t.cn'):
            article_url = url[0]
    return article_url

def get_pics(weibo_info):
    """获取微博原始图片url"""
    if weibo_info.get('pics'):
        pic_info = weibo_info['pics']
        pic_list = [pic['large']['url'] for pic in pic_info]
        pics = ','.join(pic_list)
    else:
        pics = ''
    return pics

def get_created_time(created_at):
    """标准化微博发布时间"""
    if u"刚刚" in created_at:
        created_at = datetime.now()
    elif u"分钟" in created_at:
        minute = created_at[:created_at.find(u"分钟")]
        minute = timedelta(minutes=int(minute))
        created_at = datetime.now() - minute
    elif u"小时" in created_at:
        hour = created_at[:created_at.find(u"小时")]
        hour = timedelta(hours=int(hour))
        created_at = datetime.now() - hour
    elif u"昨天" in created_at:
        day = timedelta(days=1)
        created_at = datetime.now() - day
    elif created_at.count('-') == 1:
        created_at = datetime.now() - timedelta(days=365)
    return created_at

def GetWeibo(uid, wbindex):
    content_list=[]
    params = {
        'containerid': '107603' + str(uid)
    }
    url = 'https://m.weibo.cn/api/container/getIndex?'
    r = requests.get(url, params=params)
    res = r.json()
    if res['ok']:
        weibos = res['data']['cards']
        for w in weibos:
            if w['card_type'] == 9:
                retweeted_status = w['mblog'].get('retweeted_status')
                is_long = w['mblog'].get('isLongText')
                weibo_id = w['mblog']['id']
                weibo_url = w['scheme']
                weibo_istop = w['mblog'].get('isTop')
                if weibo_istop and weibo_istop == 1:
                    continue
                if datetime.now() - get_created_time(w['mblog']['created_at'])  > timedelta(seconds = 59):
                   break
                if retweeted_status and retweeted_status.get('id'):  # 转发
                    retweet_id = retweeted_status.get('id')
                    is_long_retweet = retweeted_status.get('isLongText')
                    if is_long:
                        weibo = get_long_weibo(weibo_id)
                        if not weibo:
                            weibo = parse_weibo(w['mblog'])
                    else:
                        weibo = parse_weibo(w['mblog'])
                    if is_long_retweet:
                        retweet = get_long_weibo(retweet_id)
                        if not retweet:
                            retweet = parse_weibo(retweeted_status)
                    else:
                        retweet = parse_weibo(retweeted_status)
                    weibo['retweet'] = retweet
                    content_list.append(wb_name_list[wbindex] + '转发了微博并说： ' + weibo['text'])
                    content_list.append('原微博：'+weibo['retweet']['text'])
                    content_list.append('本条微博地址是：' + weibo_url)
                    
                else:  # 原创
                    if is_long:
                        weibo = get_long_weibo(weibo_id)
                        if not weibo:
                            weibo = parse_weibo(w['mblog'])
                    else:
                        weibo = parse_weibo(w['mblog'])
                    content_list.append(wb_name_list[wbindex] + '发了新微博并说： ' + weibo['text'])
                    content_list.append('本条微博地址是：' + weibo_url)
                    for pic_info in weibo['pics']:
                        content_list.append('[CQ:image,file='+pic_info+']')
                    #return content_list

    return content_list

    

def GetDynamicStatus(uid, VRindex):
    #print('Debug uid  '+str(uid))
    res = requests.get('https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid='+str(uid)+'offset_dynamic_id=0')
    res.encoding='utf-8'
    res = res.text
    #res = res.encode('utf-8')
    cards_data = json.loads(res)
    try:
        cards_data = cards_data['data']['cards']
    except:
        exit()
    #print('Success get')
    try:
        with open(str(uid)+'Dynamic','r') as f:
            last_dynamic_str = f.read()
            f.close()
    except Exception as err:
        last_dynamic_str=''
        pass
    if last_dynamic_str == '':
        last_dynamic_str = cards_data[1]['desc']['dynamic_id_str']
    print(last_dynamic_str)
    index = 0
    content_list=[]
    cards_data[0]['card'] = json.loads(cards_data[0]['card'],encoding='gb2312')
    nowtime = time.time().__int__()
    # card是字符串，需要重新解析
    while last_dynamic_str != cards_data[index]['desc']['dynamic_id_str']:
        #print(cards_data[index]['desc'])
        try:
            if nowtime-cards_data[index]['desc']['timestamp'] > 125:
                break
            if (cards_data[index]['desc']['type'] == 64):
                content_list.append(VR_name_list[VRindex] +'发了新专栏「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
            else:
                if (cards_data[index]['desc']['type'] == 8):
                    content_list.append(VR_name_list[VRindex] + '发了新视频「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
                else:         
                    if ('description' in cards_data[index]['card']['item']):
                        #这个是带图新动态
                        content_list.append(VR_name_list[VRindex] + '发了新动态： ' +cards_data[index]['card']['item']['description'])
                        #print('Fuck')
                        #CQ使用参考：[CQ:image,file=http://i1.piimg.com/567571/fdd6e7b6d93f1ef0.jpg]
                        for pic_info in cards_data[index]['card']['item']['pictures']:
                            content_list.append('[CQ:image,file='+pic_info['img_src']+']')
                    else:
                        #这个表示转发，原动态的信息在 cards-item-origin里面。里面又是一个超级长的字符串……
                        #origin = json.loads(cards_data[index]['card']['item']['origin'],encoding='gb2312') 我也不知道这能不能解析，没试过
                        #origin_name = 'Fuck'
                        if 'origin_user' in cards_data[index]['card']:
                            origin_name = cards_data[index]['card']['origin_user']['info']['uname']
                            content_list.append(VR_name_list[VRindex]+ '转发了「'+ origin_name + '」的动态并说： ' +cards_data[index]['card']['item']['content'])
                        else:
                            #这个是不带图的自己发的动态
                            content_list.append(VR_name_list[VRindex]+ '发了新动态： ' +cards_data[index]['card']['item']['content'])
            content_list.append('本条动态地址为'+'https://t.bilibili.com/'+ cards_data[index]['desc']['dynamic_id_str'])
        except Exception as err:
                print('PROCESS ERROR')
                pass
        index += 1
        if len(cards_data) == index:
            break
        cards_data[index]['card'] = json.loads(cards_data[index]['card'])
    f = open(str(uid)+'Dynamic','w')
    f.write(cards_data[0]['desc']['dynamic_id_str'])
    f.close()
    return content_list


def GetLiveStatus(uid):
    res = requests.get('https://api.live.bilibili.com/room/v1/Room/get_info?device=phone&;platform=ios&scale=3&build=10000&room_id=' + str(uid))
    #res = requests.get('https://api.live.bilibili.com/AppRoom/msg?room_id='+str(uid))
    #res = requests.get ('https://api.live.bilibili.com/xlive/web-room/v1/dM/gethistory?roomid=21463238')
    res.encoding = 'utf-8'
    res = res.text
    try:
        with open(str(uid)+'Live','r') as f:
            last_live_str = f.read()
            f.close()
    except Exception as err:
            last_live_str = '0'
            pass
    try:
        live_data = json.loads(res)
        live_data = live_data['data']
        now_live_status = str(live_data['live_status'])
        live_title = live_data['title']
    except:
        now_live_status = '0'
        pass
    f = open(str(uid)+'Live','w')
    f.write(now_live_status)
    f.close()
    if last_live_str != '1':
        if now_live_status == '1':
            return live_title
    return ''



def main():
    print('test')
    room_id = get_live_room_id(423728837)
    print(GetLiveStatus(room_id))
    #print(GetDynamicStatus(2072023,0))
    #print(GetWeibo(7287111107,0))

if __name__ == "__main__":
    main()
