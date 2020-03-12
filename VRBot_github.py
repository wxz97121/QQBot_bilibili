
# -*-coding:utf8-*-


import nonebot
from aiocqhttp.exceptions import Error as CQHttpError
from datetime import datetime
import random
import requests
import json
import time


VR_uid_list=[61639371]
VR_group_list=[
   [950253287,849437495]
    ]
VR_name_list=['轴伊']


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

        live_status = GetLiveStatus(VR_uid_list[i])
        if live_status != '':
            for groupnum in VR_group_list[i]:
                await bot.send_group_msg(group_id=groupnum, message=VR_name_list[i] +' 开播啦啦啦！！！ ' + live_status)



def GetDynamicStatus(uid, VRindex):
    res = requests.get('https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid='+str(uid)+'offset_dynamic_id=0')
    res.encoding='utf-8'
    res = res.text
    #res = res.encode('utf-8')
    cards_data = json.loads(res)
    cards_data = cards_data['data']['cards']
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
        try:
            if (cards_data[index]['desc']['type'] == 64):
                content_list.append(VR_name_list[VRindex] +'发了新专栏「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
            else:
                if (cards_data[index]['desc']['type'] == 8):
                    content_list.append(VR_name_list[VRindex] + '发了新视频「'+ cards_data[index]['card']['title'] + '」并说： ' +cards_data[index]['card']['dynamic'])
                else:         
                    if ('description' in cards_data[index]['card']['item']):
                        #这个是带图新动态
                        content_list.append(VR_name_list[VRindex] + '发了新动态： ' +cards_data[index]['card']['item']['description'])
                        print('Fuck')
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
#        print(len(cards_data))
#        print(index)
        if len(cards_data) == index:
            break
        #这条是105 秒前发的。
        if nowtime-cards_data[index]['desc']['timestamp'] > 105:
            break
        cards_data[index]['card'] = json.loads(cards_data[index]['card'])
    f = open(str(uid)+'Dynamic','w')
    f.write(cards_data[0]['desc']['dynamic_id_str'])
    f.close()
    return content_list


def GetLiveStatus(uid):
    res = requests.get('https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld?mid='+str(uid))
    res.encoding = 'utf-8'
    res = res.text
    try:
        with open(str(uid)+'Live','r') as f:
            last_live_str = f.read()
            f.close()
    except Exception as err:
            last_live_str = '0'
            pass
    live_data = json.loads(res)
    live_data = live_data['data']
    now_live_status = str(live_data['liveStatus'])
    live_title = live_data['title']
    f = open(str(uid)+'Live','w')
    f.write(now_live_status)
    f.close()
    if last_live_str == '0':
        if now_live_status == '1':
            return live_title
    return ''



def main():
    print(GetDynamicStatus(455916618,0))

if __name__ == "__main__":
    main()
