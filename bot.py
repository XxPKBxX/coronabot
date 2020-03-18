import discord, asyncio, requests, json, random, datetime, time
from datetime import datetime as dt
from discord.ext import tasks
from itertools import cycle

token = "token"
client = discord.Client()
status = cycle(["l|갓포티파이","w|갓튜브","갓겜"])
cmds = ["코로나현황","코로나대처법","선별진료소","핑","태보해","최근공지","최근재난문자","설정","도움말","도움","마스크","캡챠","관리자"]

cooldown = {}
captcha = []

lastAnnounce = []
lastAlert = {}
alerting = 0

red = discord.Color.red()
green = discord.Color.green()
yellow = discord.Color.gold()
blue = discord.Color.blue()

def isIn(check, toCheck):
    answer = False
    for s in toCheck:
        if s in check: answer = True
    return answer

def getMsg(): #from emergency alert bot
    url = "https://m.search.naver.com/search.naver?sm=tab_hty.top&where=m&query=%EA%B8%B4%EA%B8%89+%EC%9E%AC%EB%82%9C%EB%AC%B8%EC%9E%90&oquery=%EC%9E%AC%EB%82%9C%EB%AC%B8%EC%9E%90&tqi=UBbdqsprvmZssUGUjT0ssssssRC-366294"
    res = requests.get(url).text

    toFind1 = '<span class="ico_tlt"><span class="txt">'
    toFind2 = '</span></span><em class="area_name">'
    main = res[res.find(toFind1):res.find('</span> <button type="button" class="news_more _tail _revert" style="display: none;">')]

    msgType = main[main.find(toFind1) + len(toFind1):main.find(toFind2)]
    if msgType == "기타": msgRegion = main[main.find(toFind2) + len(toFind2):main.find('</em> </span> </div> <div> <time datetime="">')]
    else: msgRegion = main[main.find(toFind2) + len(toFind2):main.find('</em> </span> <a nocr onclick="return goOtherCR(this,')]
    msgTimeAndSender = main[main.find('<time datetime="">') + len('<time datetime="">'):main.find('</time>')]
    msgTime = msgTimeAndSender[:17]
    msgSender = msgTimeAndSender[18:]
    msg = main[main.find('<div class="timeline_info"> <span class="dsc _text">') + len('<div class="timeline_info"> <span class="dsc _text">'):]

    time = msgTime.split()[0][:-1] + " " + msgTime.split()[1]
    year = int(time[:4])
    month = int(time[5:7])
    day = int(time[8:10])
    hour = int(time[11:13])
    minute = int(time[14:])
    time = datetime.datetime(year, month, day, hour, minute, 0, 0)

    return {"type":msgType,"region":msgRegion,"time":time,"sender":msgSender,"content":msg}

def loadJson(fileName):
    try: return json.loads(open(fileName, "r", encoding="utf-8").read())
    except: return None

async def catchError(message, error):
    errorCh = client.get_user(278441794633465876)
    
    embed = discord.Embed(title="오류 발생!", description="기능을 실행하는 동안 오류가 발생하였습니다.", color=red, timestamp=dt.utcnow())
    if message != None: embed.add_field(name="실행 중이던 명령어:", value=message.content)
    if error != None:
        error = str(error).replace("`","")
        embed.add_field(name="오류 내용:", value=f"```\n{error}\n```")
    await errorCh.send(embed=embed)

    if message != None:
        embed = discord.Embed(title="오류 발생!", description="명령어를 실행하는 동안 오류가 발생하였습니다.\n조금 뒤에 다시 시도해 주세요.\n오류가 지속된다면, 저에게 DM으로 지원 메시지를 보내주시길 바랍니다.", color=red, timestamp=dt.utcnow())
        await message.channel.send(embed=embed)

@tasks.loop(seconds=10)
async def loopTen():
    global status
    global lastAlert
    global captcha
    global alerting

    toCh = next(status)
    if toCh.split("|")[0] == "l": await client.change_presence(activity=discord.Activity(name=toCh.split("|")[1], type=discord.ActivityType.listening))
    elif toCh.split("|")[0] == "w": await client.change_presence(activity=discord.Activity(name=toCh.split("|")[1], type=discord.ActivityType.watching))
    else: await client.change_presence(activity=discord.Activity(name=toCh, type=discord.ActivityType.playing))


    alert = getMsg()

    if alerting == 0:
        alerting += 1
        lastAlert = alert
        return

    content = alert["content"]
    if alert == lastAlert: return
    if alert["type"] != "감염병": return

    embed = discord.Embed(title="감염병 관련 재난 문자 발송", description=f"```\n{content}\n```", color=red)
    embed.add_field(name="보내진 지역:", value=alert["region"])
    time = alert["time"]
    if time.hour > 12: timestr = f"{time.year}년 {time.month}월 {time.day}일 | 오후 {time.hour - 12}시 {time.minute}분"
    if time.hour <= 12: timestr = f"{time.year}년 {time.month}월 {time.day}일 | 오전 {time.hour}시 {time.minute}분"
    embed.add_field(name="보내진 시각:", value=timestr)
    embed.add_field(name="보낸 곳:", value=alert["sender"])

    setting = loadJson("settings.json")
    if setting == None:
        await catchError(None, "설정 파일 로드 실패 (재난 문자 발송중)")
        return
        
    for server in client.guilds:
        sent = False
        if str(server.id) in setting and setting[str(server.id)][0] == 0: sent = True
        if str(server.id) in setting and setting[str(server.id)][0] == 1 and sent == False:
            try: await client.get_channel(setting[str(server.id)][1]).send(embed=embed)
            except: notSent += 1
            else: sent = True
        if sent == False:
            for channel in server.text_channels:
                if sent == False and isIn(channel.name, ["공지","announce","재난문자","재난-문자"]):
                    try: await channel.send(embed=embed)
                    except: notSent += 1
                    else: sent = True
        if sent == False:
            try: await server.text_channels[0].send(embed=embed)
            except: notSent += 1
            else: sent = True
    
    lastAlert = alert

@client.event
async def on_ready():
    print("---------------")
    print("봇이 켜졌습니다.")
    print("---------------")

    loopTen.start()

    embed = discord.Embed(title="봇이 켜졌습니다.", description="봇이 켜졌습니다.", color=green, timestamp=dt.utcnow())
    await client.get_user(278441794633465876).send(embed=embed)

@client.event
async def on_message(message):
    global status
    global lastAnnounce
    global cooldown
    logCh = client.get_user(278441794633465876)

    if message.author.bot or str(message.author.id) in captcha: return
    
    if message.guild == None:
        dmBl = loadJson("dmbl.json")
        if dmBl != None and str(message.author.id) in dmBl:
            embed = discord.Embed(title="관리자에 의해서 DM 전송이 차단되었습니다!", description="관리자에 의해 DM 전송이 차단되었기 때문에 DM을 통한 지원 메시지 전송은 금지됩니다.", color=red, timestamp=dt.utcnow())
            if dmBl[str(message.author.id)] != "-none-": embed.add_field(name="사유:", value=dmBl[str(message.author.id)])
            await message.author.send(embed=embed)
            return

        content = message.content.replace("`","")

        embed = discord.Embed(title="문의가 도착하였습니다.", description="문의가 도착했습니다.\n확인 후 필요하면 답장해 주세요.", color=blue, timestamp=dt.utcnow())
        embed.add_field(name="보낸 사람:", value=f"{str(message.author)} ({message.author.id})")
        embed.add_field(name="내용:", value=f"```\n{content}\n```", inline=True)
        await logCh.send(embed=embed)

        await message.author.send(content=":thumbsup: 문의를 전송하였습니다. 관리자가 확인 후 답장하겠습니다.")
        return
    
    if len(message.content) <= 1 or (client.user.id == 680006783623888897 and not message.content.startswith("*")) or (client.user.id == 688249396592115762 and not message.content.startswith(";")): return

    if message.content[1:].split()[0] in cmds:
        try:
            wrLog = open("chatLog.txt", "a", encoding="utf-8")
            if len(open("chatLog.txt","r",encoding="utf-8").read()) < 1: wrLog.write(f"{str(message.author)} ({message.author.id}): {message.content}")
            else: wrLog.write(f"\n{str(message.author)} ({message.author.id}): {message.content}")
            wrLog.close()
        except: pass

        bl = loadJson("bl.json")
        if message.content[1:].split()[0] != "약관" and bl != None and str(message.author.id) in bl:
            embed = discord.Embed(title="관리자에 의해서 명령어 사용이 차단되었습니다!", description="관리자에 의해 명령어 전송이 차단되었기 때문에 봇 사용은 금지됩니다.\n이의 제기는 저를 통해 DM으로 관리자에게 보내십시오.", color=red, timestamp=dt.utcnow())
            if bl[str(message.author.id)] != "-none-": embed.add_field(name="사유:", value=bl[str(message.author.id)])
            await message.channel.send(embed=embed)
            return

        if not str(message.author.id) in cooldown: cooldown.update({str(message.author.id):[1,dt.utcnow()]})
        else:
            toAdd = cooldown[str(message.author.id)][0] + 1
            toAdd2 = cooldown[str(message.author.id)][1]
            cooldown.update({str(message.author.id):[toAdd,toAdd2]})
            if (dt.utcnow() - cooldown[str(message.author.id)][1]).total_seconds() >= 10: del cooldown[str(message.author.id)]
            if str(message.author.id) in cooldown and cooldown[str(message.author.id)][0] > 3:
                await message.add_reaction("💢")
            if str(message.author.id) in cooldown and cooldown[str(message.author.id)][0] > 3: return

    command = message.content[1:].split()[0]
    commandLine = []
    if len(message.content.split()) > 1: commandLine = message.content.split()[1:]
    
    verify = loadJson("verified.json")
    if command in cmds and command != "캡챠" and verify != None and not str(message.author.id) in verify:
        await message.channel.send(embed=discord.Embed(title="지금은 명령어를 사용할 수 없습니다.", description="``*캡챠`` 명령어를 통해 인증한 뒤 다시 사용해 주세요.",color=red,timestamp=dt.utcnow()))
        return

    if command == "코로나현황" and len(commandLine) < 1:
        msg = await message.channel.send(embed=discord.Embed(title="정보 불러오는 중...", description="정보를 불러오고 있습니다. 잠시만 기다려 주세요.", color=yellow, timestamp=dt.utcnow()))
        rep = requests.get("http://ncov.mohw.go.kr/", headers={"User-Agent":"Mozilla/5.0"})
        if rep.status_code != 200:
            await msg.delete()
            await catchError(message, "상태 코드 오류")
        else:
            res = rep.text.replace("\n","").replace("\t","")
            confirmed = res[res.find('<strong class="tit">확진환자</strong><span class="num"><span class="mini">(누적)</span>') + len('<strong class="tit">확진환자</strong><span class="num"><span class="mini">(누적)</span>'):res.find('</span><span class="before">전일대비')]
            add1 = res[res.find('</span><span class="before">전일대비 (+ ') + len('</span><span class="before">전일대비 (+ '):]
            add = add1[:add1.find(')</span></li><li><em class="sign">')]
            confirmedHaeje1 = res[res.find('<strong class="tit">완치<br /><span class="mini_tit">(격리해제)</span></strong><span class="num">') + len('<strong class="tit">완치<br /><span class="mini_tit">(격리해제)</span></strong><span class="num">'):]
            confirmedHaeje = confirmedHaeje1[:confirmedHaeje1.find('</span><span class="before">(+')]
            inspect = res[res.find('<span class="tit">누적 검사수</span><span class="num">') + len('<span class="tit">누적 검사수</span><span class="num">'):res.find(' 건</span></li><li><span class="tit">누적 검사완료수</span>')]
            died1 = res[res.find('<strong class="tit">사망</strong><span class="num">') + len('<strong class="tit">사망</strong><span class="num">'):]
            died = died1[:died1.find('</span><span class="before">(+')]

            if confirmed.replace(",","").isdigit() == False or confirmedHaeje.replace(",","").isdigit() == False or died.replace(",","").isdigit() == False:
                await msg.delete()
                await catchError(message, "파싱 에러")
            else:
                embed = discord.Embed(title="국내 발생 현황", description="아래에서 자세히 확인하세요.", color=blue, timestamp=dt.utcnow())
                embed.add_field(name="확진 환자 수:", value=confirmed + "명")
                embed.add_field(name="전일 대비", value="+ " + add + "명")
                embed.add_field(name="확진 환자 격리 해제 수:", value=confirmedHaeje + "명")
                embed.add_field(name="검사 진행:", value=inspect + "명")
                embed.add_field(name="사망자 수:", value="**" + died + "명**")
                embed.add_field(name="이동 경로:", value="[코로나 맵](https://coronamap.site/) / [코로나 알리미](https://corona-nearby.com/) / [보건복지부](http://ncov.mohw.go.kr/bdBoardList.do?brdId=1&brdGubun=12)")
                embed.set_footer(text="출처: 보건복지부", icon_url="http://ncov.mohw.go.kr/static/image/header/ROK.png")
                await msg.edit(embed=embed)
    elif command == "코로나대처법" and len(commandLine) < 1:
        embed = discord.Embed(title="코로나19 증상 시 대처법", description="코로나19는 증상이 감기와 유사하기 때문에 초기에 발견할 수 있습니다.\n중앙사고수습본부에서 게시한 [게시물](http://ncov.mohw.go.kr/shBoardView.do?brdId=3&brdGubun=32&ncvContSeq=569)을 참조하거나,\n[네이버 지식백과 글](https://m.terms.naver.com/entry.nhn?cid=66630&docId=5916213&categoryId=66630)을 참조하세요.", color=blue, timestamp=dt.utcnow())
        await message.channel.send(embed=embed)
    elif command in ["공적마스크","마스크"]:
        if len(commandLine) < 1: await message.channel.send(embed=discord.Embed(title="사용법", description="```*공적마스크 (주소)```\n'서울특별시'와 같이 시 단위만 입력하는 것은 불가능합니다.", color=blue, timestamp=dt.utcnow()))
        else:
            if len(commandLine) == 1:
                await message.channel.send(content=":no_entry: '서울특별시'와 같이 시 단위만 입력하는 것은 불가능합니다.")
                return
            addr = " ".join(commandLine)
            
            try: req = requests.get(f"https://8oi9s0nnth.apigw.ntruss.com/corona19-masks/v1/storesByAddr/json?address={addr}")
            except Exception as error: await catchError(message, error)
            else:
                if req.status_code != 200: await catchError(message, "상태 코드 오류")
                else:
                    res = req.json()
                    count = res["count"]
                    if count < 1:
                        await message.channel.send(content=":no_entry: 주소가 잘못되었습니다.")
                        return
                    embed = discord.Embed(title="공적 마스크 판매 현황", description=f"``{addr}``에 있는 약국들의 마스크 판매 현황을 불러왔습니다. *총 {count}개의 결과*", color=blue, timestamp=dt.utcnow())
                    for s in res["stores"]:
                        if not "remain_stat" in s: embed.add_field(name=s["name"], value="*불러올 수 없음*")
                        else:
                            remain = s["remain_stat"]
                            if remain == "plenty": embed.add_field(name=s["name"], value="100개 이상")
                            elif remain == "some": embed.add_field(name=s["name"], value="30~100개")
                            elif remain == "few": embed.add_field(name=s["name"], value="2~30개")
                            elif remain == "empty": embed.add_field(name=s["name"], value="**없음**")
                            elif remain == "break": embed.add_field(name=s["name"], value="판매 중지")
                    if len(res["stores"]) > 25: embed.set_footer(text="25개 초과의 결과는 25개까지만 보여줍니다.")
                    await message.channel.send(embed=embed)
    elif command == "마스크판매":
        if len(commandLine) < 1: await message.channel.send(embed=discord.Embed(title="사용법", description="```*마스크판매 (주소)```\n'서울특별시'와 같이 시 단위만 입력하는 것은 불가능합니다.", color=blue, timestamp=dt.utcnow()))
        else:
            if len(commandLine) == 1:
                await message.channel.send(content=":no_entry: '서울특별시'와 같이 시 단위만 입력하는 것은 불가능합니다.")
                return
            addr = " ".join(commandLine)
            
            try: req = requests.get(f"https://8oi9s0nnth.apigw.ntruss.com/corona19-masks/v1/storesByAddr/json?address={addr}")
            except Exception as error: await catchError(message, error)
            else:
                if req.status_code != 200: await catchError(message, "상태 코드 오류")
                else:
                    res = req.json()
                    count = res["count"]
                    if count < 1:
                        await message.channel.send(content=":no_entry: 주소가 잘못되었습니다.")
                        return
                    embed = discord.Embed(title="공적 마스크 판매 현황", description=f"``{addr}``에 있는 마스크를 100개 이상 보유 중인 약국들의 마스크 판매 현황을 불러왔습니다.", color=blue, timestamp=dt.utcnow())
                    number = 0
                    for s in res["stores"]:
                        if "remain_stat" in s:
                            remain = s["remain_stat"]
                            if remain == "plenty":
                                embed.add_field(name=s["name"], value=s["addr"])
                                number += 1
                    if number > 25: embed.set_footer(text="25개 초과의 결과는 25개까지만 보여줍니다.")
                    elif number < 1: embed = discord.Embed(title="찾을 수 없음", description=f"``{addr}``에 있는 마스크를 100개 이상 보유 중인 약국들을 찾을 수 없습니다.", color=red, timestamp=dt.utcnow())
                    await message.channel.send(embed=embed)
    elif command == "선별진료소" and len(commandLine) < 1:
        embed = discord.Embed(title="코로나19 선별진료소 현황", description="[이곳](http://www.mohw.go.kr/react/popup_200128.html)에서 검체채취 가능 진료소 또한 확인할 수 있습니다.", color=blue, timestamp=dt.utcnow())
        await message.channel.send(embed=embed)
    elif command == "핑":
        msg = await message.channel.send(embed=discord.Embed(title=":ping_pong: 퐁!", description=f"현재 코로나 봇은 ``{int(client.latency * 1000)}ms``의 지연시간을 가지고 있습니다.",color=blue,timestamp=dt.utcnow()))
        ping = int((dt.utcnow() - msg.created_at).total_seconds() * 1000)
        await msg.edit(embed=discord.Embed(title=":ping_pong: 퐁!", description=f"현재 코로나 봇은 ``{int(client.latency * 1000)}ms``의 지연시간을 가지고 있습니다.\n저와 {message.author.display_name}님이 닿기까지는 ``{ping}ms``가 걸렸습니다.",color=blue,timestamp=dt.utcnow()))
    elif command == "태보해" and len(commandLine) < 1:
        msg = await message.channel.send(embed=discord.Embed(title="태보해요", description="헛둘헛둘\n**@==(^-^)@**", color=green, timestamp=dt.utcnow()))
        taebo = cycle(["@=(^-^)=@","@(^-^)==@","@=(^-^)=@","@==(^-^)@","@=(^-^)=@"])
        for i in range(5):
            await asyncio.sleep(1)
            await msg.edit(embed=discord.Embed(title="태보해요", description=f"헛둘헛둘\n**{next(taebo)}**", color=green, timestamp=dt.utcnow()))
    elif command == "최근재난문자" and len(commandLine) < 1:
        alert = lastAlert
        content = alert["content"]
        embed = discord.Embed(title="최근 발송된 감염병 관련 재난 문자", description=f"```\n{content}\n```", color=red)
        embed.add_field(name="보내진 지역:", value=alert["region"])
        time = alert["time"]
        if time.hour > 12: timestr = f"{time.year}년 {time.month}월 {time.day}일 | 오후 {time.hour - 12}시 {time.minute}분"
        if time.hour <= 12: timestr = f"{time.year}년 {time.month}월 {time.day}일 | 오전 {time.hour}시 {time.minute}분"
        embed.add_field(name="보내진 시각:", value=timestr)
        embed.add_field(name="보낸 곳:", value=alert["sender"])
        await message.channel.send(embed=embed)
    elif command == "최근공지" and len(commandLine) < 1:
        if len(lastAnnounce) < 1: await message.channel.send(embed=discord.Embed(title="최근 공지 없음", description="최근 공지가 없습니다.", color=red, timestamp=dt.utcnow()))
        else:
            embed = discord.Embed(title="최근 공지", description="최근 공지를 확인하였습니다.\n아래에서 확인하세요.", color=green, timestamp=dt.utcnow())
            embed.add_field(name=lastAnnounce[0], value=lastAnnounce[1].replace("\\n","\n"))
            await message.channel.send(embed=embed)
    elif command in ["도움말","도움"] and len(commandLine) < 1:
        embed = discord.Embed(title="도움말", description="아래에서 명령어 목록을 확인하세요.", color=blue, timestamp=dt.utcnow())
        embed.add_field(name="*코로나현황",value="코로나19 현황을 보여줍니다.")
        embed.add_field(name="*코로나대처법",value="코로나19 대처법을 보여줍니다.")
        embed.add_field(name="*공적마스크 (주소)",value="공적 마스크 판매 현황을 주소에 따라 볼 수 있습니다.")
        embed.add_field(name="*마스크판매 (주소)",value="약국 중 100개 이상을 가지고 있는 약국 목록을 보여줍니다.")
        embed.add_field(name="*선별진료소",value="코로나19 선별진료소 목록을 보여줍니다.")
        embed.add_field(name="*최근공지",value="관리자가 가장 최근에 보낸 공지 내용을 보여줍니다.")
        embed.add_field(name="*최근재난문자",value="가장 최근에 발송된 감염병 관련 재난문자 내용을 보여줍니다.")
        embed.add_field(name="*핑",value="봇의 핑을 보여줍니다.")
        embed.add_field(name="*설정",value="서버 관리자가 봇에 대해 설정을 할 수 있습니다.")
        embed.add_field(name="~~*태보해~~",value="~~@==(^-^)@~~")
        await message.channel.send(embed=embed)
    elif command == "캡챠" and len(commandLine) < 1:
        verify = loadJson("verified.json")
        if verify == None: await catchError(message,"파일 로드 실패")
        if str(message.author.id) in verify:
            await message.channel.send(content=":no_entry: 이미 인증이 되어있습니다.")
            return

        naver = {"X-Naver-Client-Id":"FJSzckugo6bZMGgQ7V3X","X-Naver-Client-Secret":"Fb7IjVDGWu"}
        try:
            req = requests.get("https://openapi.naver.com/v1/captcha/nkey?code=0",headers=naver)
            if req.status_code != 200: await catchError(message, "상태 코드 오류")
        except Exception as error: await catchError(message, error)
        else:
            captcha.append(str(message.author.id))
            code = req.json()["key"]
            embed = discord.Embed(title="이미지에 있는 글자를 입력해 주십시오.", description="표시되는 이미지에 나타난 글자를 1분 내로 입력해 주세요.\n**__대소문자 구분이 필요합니다.__**", color=blue, timestamp=dt.utcnow())
            embed.set_image(url=f"https://openapi.naver.com/v1/captcha/ncaptcha.bin?key={code}")
            await message.channel.send(embed=embed)

            def check(m): return m.author == message.author and m.channel == message.channel

            try: mm = await client.wait_for("message", check=check,timeout=60.0)
            except asyncio.TimeoutError:
                await message.channel.send(embed=None, content=":no_entry: 시간 초과")
                captcha.remove(str(message.author.id))
            else:
                try:
                    req = requests.get(f"https://openapi.naver.com/v1/captcha/nkey?code=1&key={code}&value={mm.content}",headers=naver)
                    if req.status_code != 200: await catchError(message, "상태 코드 오류")
                except Exception as error: await catchError(message, error)
                else:
                    res = req.json()["result"]
                    if res == True:
                        verify.update({str(message.author.id):1})
                        try:
                            wr = open("verified.json","w",encoding="utf-8")
                            wr.write(json.dumps(verify))
                            wr.close()
                        except Exception as error: await catchError(message, error)
                        else: await message.channel.send(embed=discord.Embed(title="인증되었습니다.", description="정상적으로 명령어 이용이 가능합니다.",color=green,timestamp=dt.utcnow()))
                    elif res == False:
                        await message.channel.send(embed=discord.Embed(title="잘못된 값을 입력하였습니다.", description="다시 인증을 진행해 주세요.",color=red,timestamp=dt.utcnow()))
                captcha.remove(str(message.author.id))
    elif command == "설정":
        if not message.author.guild_permissions.administrator and message.author.id != 278441794633465876: await message.channel.send(embed=discord.Embed(title="권한이 부족합니다.", description="이 명령어를 사용하려면 ``관리자`` 권한이 필요합니다.", color=red, timestamp=dt.utcnow()))
        else:
            helpMsg = discord.Embed(title="도움말", description="```\n*설정 재난문자 off|on\n*설정 재난문자채널\n```", color=blue, timestamp=dt.utcnow())
            if len(commandLine) < 1: await message.channel.send(embed=helpMsg)
            else:
                cmd = commandLine[0].lower()
                cmdLine = []
                if len(commandLine[1:]) >= 1: cmdLine = commandLine[1:]
                guildId = str(message.guild.id)
                
                settings = loadJson("settings.json")
                if settings == None:
                    await catchError(message, "설정 파일 로드 실패")
                    return

                if not guildId in settings: settings.update({guildId:[1,0]})

                if cmd == "재난문자":
                    if len(cmdLine) != 1 or not cmdLine[0].lower() in ["off","on"]: await message.channel.send(embed=discord.Embed(title="사용법", description="```*설정 재난문자 off|on```", color=blue, timestamp=dt.utcnow()))
                    else:
                        if cmdLine[0].lower() == "off":
                            if guildId in settings and settings[guildId][0] == 0:
                                await message.channel.send(content=":no_entry: 이미 재난 문자 수신이 꺼져 있습니다.")
                                return

                            try: writeSet = open("settings.json","w",encoding="utf-8")
                            except Exception as error:
                                await catchError(message, error)
                                return
                                
                            settings[guildId][0] = 0
                            settings.update({guildId:settings[guildId]})

                            writeSet.write(json.dumps(settings))
                            writeSet.close()

                            await message.channel.send(content=":thumbsup: 재난 문자 수신을 껐습니다.")
                        elif cmdLine[0].lower() == "on":
                            if guildId in settings and settings[guildId][0] == 1:
                                await message.channel.send(content=":no_entry: 이미 재난 문자 수신이 켜져 있습니다.")
                                return
                                
                            try: writeSet = open("settings.json","w",encoding="utf-8")
                            except Exception as error:
                                await catchError(message, error)
                                return

                            settings[guildId][0] = 1
                            settings.update({guildId:settings[guildId]})

                            writeSet.write(json.dumps(settings))
                            writeSet.close()

                            await message.channel.send(content=":thumbsup: 재난 문자 수신을 켰습니다.")
                elif cmd == "재난문자채널":
                    if len(cmdLine) != 1: await message.channel.send(embed=discord.Embed(title="사용법", description="```*설정 재난문자채널 (#채널)\n*설정 재난문자채널 자동```", color=blue, timestamp=dt.utcnow()))
                    else:
                        if cmdLine[0] == "자동":
                            try: writeSet = open("settings.json","w",encoding="utf-8")
                            except Exception as error:
                                await catchError(message, error)
                                return

                            settings[guildId][1] = 0
                            settings.update({guildId:settings[guildId]})
                            writeSet.write(json.dumps(settings))
                            await message.channel.send(content=f":thumbsup: 이제부터 재난 문자는 자동으로 발송됩니다.")
                            return
                        if not (cmdLine[0].startswith("<#") and cmdLine[0].endswith(">")): await message.channel.send(content=":no_entry: 채널을 맨션해주세요.")
                        else:
                            chId = cmdLine[0][2:-1]
                            if not chId.isdigit() or not client.get_channel(int(chId)) in message.guild.text_channels:
                                await message.channel.send(content=":no_entry: 맨션한 채널이 존재하지 않습니다.")
                                return
                                
                            try: writeSet = open("settings.json","w",encoding="utf-8")
                            except Exception as error:
                                await catchError(message, error)
                                return

                            settings[guildId][1] = int(chId)
                            settings.update({guildId:settings[guildId]})
                            writeSet.write(json.dumps(settings))
                            await message.channel.send(content=f":thumbsup: 이제부터 재난 문자는 <#{chId}>에 발송됩니다.")
    elif command == "관리자":
        if message.author.id != 278441794633465876:
            await message.channel.send(content=":no_entry: 권한이 부족합니다.")
            return
        else:
            helpMsg = discord.Embed(title="도움말", description="```\n*관리자 차단 DM|CMD (아이디) [사유]\n*관리자 로그파일\n*관리자 로그삭제\n*관리자 상태메시지 (내용)\n*관리자 공지 (제목)|(내용)\n*관리자 답장 (아이디) (내용)\n*관리자 서버목록\n*관리자 봇종료\n```", color=blue, timestamp=dt.utcnow())
            if len(commandLine) < 1: await message.channel.send(embed=helpMsg)
            else:
                cmd = commandLine[0].lower()
                cmdLine = []
                if len(commandLine[1:]) >= 1: cmdLine = commandLine[1:]
                if cmd == "차단":
                    if len(cmdLine) == 1:
                        if cmdLine[0].lower() == "dm": blList = loadJson("dmbl.json")
                        elif cmdLine[0].lower() == "cmd": blList = loadJson("bl.json")
                        else:
                            await message.channel.send(content=":no_entry: DM 또는 CMD만 차단 가능합니다.")
                            return

                        if blList == None: await catchError(message, "파일 로드 실패")
                        else:
                            if len(blList) < 1:
                                if cmdLine[0].lower() == "dm": embed = discord.Embed(title="DM 차단 목록", description="DM 차단 목록이 비어있습니다.", color=red, timestamp=dt.utcnow())
                                elif cmdLine[0].lower() == "cmd": embed = discord.Embed(title="명령어 차단 목록", description="명령어 차단 목록이 비어있습니다.", color=red, timestamp=dt.utcnow())
                                await message.channel.send(embed=embed)
                                return

                            if cmdLine[0].lower() == "dm": embed = discord.Embed(title="DM 차단 목록", description="지금까지의 DM 차단 목록입니다.", color=green, timestamp=dt.utcnow())
                            elif cmdLine[0].lower() == "cmd": embed = discord.Embed(title="명령어 차단 목록", description="지금까지의 명령어 차단 목록입니다.", color=green, timestamp=dt.utcnow())
                            for s in blList:
                                user = str(client.get_user(int(s)))
                                reason = blList[s]
                                if reason == "-none-": embed.add_field(name=f"{user} ({s})",value="사유: 없음")
                                else: embed.add_field(name=f"{user} ({s})",value=f"사유: {reason}")
                            await message.channel.send(embed=embed)
                    elif len(cmdLine) < 2: await message.channel.send(embed=discord.Embed(title="사용법", description="```*관리자 차단 DM|CMD (아이디) [사유]```", color=blue, timestamp=dt.utcnow()))
                    else:
                        userId = cmdLine[1]
                        if userId.isdigit() == False: await message.channel.send(content="사용법: ``*관리자 차단 DM|CMD (아이디) [사유]``")
                        else:
                            if not client.get_user(int(userId)) in client.users: await message.channel.send(content=":no_entry: 입력하신 사용자는 존재하지 않습니다.")
                            else:
                                blockType = cmdLine[0].lower()
                                if len(cmdLine[2:]) < 1: reason = "-none-"
                                else: reason = " ".join(cmdLine[2:])
                                
                                if blockType in ["dm","cmd"] and int(userId) == 278441794633465876:
                                    await message.channel.send(content=":no_entry: 봇 주인은 차단시킬 수 없습니다.")
                                    return

                                if blockType == "dm":
                                    bl = loadJson("dmbl.json")
                                    if bl == None: await catchError(message, "파일 로드 실패")
                                    else:
                                        wrBl = open("dmbl.json", "w", encoding="utf-8")

                                        if userId in bl:
                                            del bl[userId]
                                        
                                            wrBl.write(json.dumps(bl))
                                            wrBl.close()
                                            sent = 0
                                        else:
                                            bl.update({userId:reason})
                                        
                                            wrBl.write(json.dumps(bl))
                                            wrBl.close()
                                            sent = 1
                                        
                                        if sent == 1: await message.channel.send(content=":thumbsup: 추가 완료.")
                                        elif sent == 0: await message.channel.send(content=":thumbsup: 삭제 완료.")
                                elif blockType == "cmd":
                                    bl = loadJson("bl.json")
                                    if bl == None: await catchError(message, "파일 로드 실패")
                                    else:
                                        wrBl = open("bl.json", "w", encoding="utf-8")

                                        if userId in bl:
                                            del bl[userId]
                                        
                                            wrBl.write(json.dumps(bl))
                                            wrBl.close()
                                            sent = 0
                                        else:
                                            bl.update({userId:reason})
                                        
                                            wrBl.write(json.dumps(bl))
                                            wrBl.close()
                                            sent = 1

                                        if sent == 1: await message.channel.send(content=":thumbsup: 추가 완료.")
                                        elif sent == 0: await message.channel.send(content=":thumbsup: 삭제 완료.")
                                else: await message.channel.send(content=":no_entry: DM 또는 CMD만 차단 가능합니다.")
                elif cmd == "로그파일" and len(cmdLine) < 1:
                    try: await message.channel.send(content=":book: 로그 파일을 첨부하였습니다.", file=discord.File("chatLog.txt"))
                    except Exception as error: await catchError(message, error)
                elif cmd == "로그삭제" and len(cmdLine) < 1:
                    try: open("chatLog.txt","w",encoding="utf-8").close()
                    except Exception as error: await catchError(message, error)
                    else: await message.channel.send(content=":thumbsup: 삭제 완료.")
                elif cmd == "상태메시지":
                    if len(cmdLine) < 1: await message.channel.send(embed=discord.Embed(title="사용법", description="```*관리자 상태메시지 (내용)```\n``|||``로 구분합니다.\n앞에 ``w|``, ``l|``을 붙이면 각각 시청중, 청취중으로 표시됩니다.", color=blue, timestamp=dt.utcnow()))
                    else:
                        status = cycle(" ".join(cmdLine).split("|||"))
                        await message.channel.send(content=":thumbsup: 변경 완료.")
                        loopTen.restart()
                elif cmd == "공지":
                    if len(cmdLine) < 2: await message.channel.send(embed=discord.Embed(title="사용법", description="```*관리자 공지 (제목)|(내용)```\n내용에서 줄바꿈은 ``\\n``으로 사용하십시오.", color=blue, timestamp=dt.utcnow()))
                    else:
                        title = " ".join(cmdLine).split("|")[0].replace("`","")
                        content = " ".join(cmdLine).split("|")[1].replace("\\n","\n").replace("`","")
                        lastAnnounce = [title,content.replace("\n","\\n")]

                        embed = discord.Embed(title=title, description=content, color=blue, timestamp=dt.utcnow())
                        embed.set_footer(text="봇 관리자로부터", icon_url=client.user.avatar_url)

                        notSent = 0
                        sentCh = 0
                        for server in client.guilds:
                            sent = False
                            for channel in server.text_channels:
                                if sent == False and isIn(channel.name, ["공지","announce"]):
                                    try: await channel.send(embed=embed)
                                    except: notSent += 1
                                    else:
                                        sentCh += 1
                                        sent = True
                            if sent == False:
                                channel = server.text_channels[0]
                                try: await channel.send(embed=embed)
                                except: notSent += 1
                                else: sentCh += 1

                        embed = discord.Embed(title="공지가 보내졌습니다!", description="입력하신 내용을 전송하였습니다.", color=green, timestamp=dt.utcnow())
                        embed.add_field(name="공지가 보내진 채널:", value=f"{sentCh}개")
                        embed.add_field(name="보내기를 실패한 채널:", value=f"{notSent}개")
                        await message.channel.send(embed=embed)
                elif cmd == "답장":
                    if len(cmdLine) < 2: await message.channel.send(embed=discord.Embed(title="사용법", description="```*관리자 답장 (아이디) (내용)```\n", color=blue, timestamp=dt.utcnow()))
                    else:
                        userId = cmdLine[0]
                        if userId.isdigit() == False: await message.channel.send(content="사용법: ``*관리자 답장 (아이디) (내용)``\n내용에서 줄바꿈은 ``\\n``으로 사용하십시오.")
                        else:
                            if not client.get_user(int(userId)) in client.users: await message.channel.send(content=":no_entry: 입력하신 사용자는 존재하지 않습니다.")
                            else:
                                content = " ".join(cmdLine[1:]).replace("\\n","\n")
                                sendCh = client.get_user(int(userId))

                                embed = discord.Embed(title="답장이 도착하였습니다.", description="```\n" + content + "\n```", color=blue, timestamp=dt.utcnow())
                                await sendCh.send(embed=embed)

                                await message.channel.send(content=":thumbsup: 답장을 전송하였습니다.")
                                return
                elif cmd == "봇종료" and len(cmdLine) < 1:
                    embed = discord.Embed(title="봇이 꺼졌습니다.", description="봇 관리자에 의해 봇이 꺼졌습니다.", color=red, timestamp=dt.utcnow())
                    await logCh.send(embed=embed)
                    await client.change_presence(status=discord.Status.offline)
                    await client.logout()
                elif cmd == "서버목록" and len(cmdLine) < 1:
                    embed = discord.Embed(title="서버 목록", description=f"코로나봇을 사용하는 서버 목록*({len(client.guilds)}개)*입니다.", color=green, timestamp=dt.utcnow())

                    for server in client.guilds:
                        embed.add_field(name=f"{server.name} ({server.id})", value=f"멤버: {len(server.members)}명")
                    await message.channel.send(embed=embed)
                else: await message.channel.send(embed=helpMsg)

client.run(token)
