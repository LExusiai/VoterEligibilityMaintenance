# -*- coding: utf-8 -*-

import datetime
import pywikibot
import os
import re
from pywikibot import pagegenerators
from . import database

env = os.environ
site = pywikibot.Site('zh', 'wikipedia')

main_list_page = pywikibot.Page(site, env['EVB_MAINLIST'])

def maintenance_mainlist() -> None:
    list_before_update: list = database.LocalList(0).voter_list
    update_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y年%m月%d日%H时%M分%S秒（协调世界时）")
    database.LocalList.update_the_mainlist()
    updated_list: list = database.LocalList(0).voter_list
    if sorted(list_before_update) == sorted(updated_list):
        return None
    else:
        removed_voter: set = set(list_before_update[1]) - set(updated_list[1])
        added_voter: set = set(updated_list[1]) - set(list_before_update[1])
        wikitext_list = "\n".join(updated_list[0])
        wikitext_list = "{{/header}}" + "\n" \
             + "本页面为机器人依[[Wikipedia:人事任免投票资格]]自动生成的合资格选民名单，全名单合计{person}人。".format(person=len(updated_list[0]))\
             + "\n" + "名单最后更新基准时间：{time}".format(time=update_time) \
             + "\n" + "<pre>" + "\n" + wikitext_list + "\n" + "</pre>"
        main_list_page.text = wikitext_list
        summary = ""
        if added_voter:
            summary: str = summary + "+" + "、".join(added_voter)
        if removed_voter:
            summary: str = summary + "-" + "、".join(removed_voter)
        main_list_page.save(summary=summary)

# -1 : sublist existed.
# -2 : user is not registered.
def create_a_sublist(username: str, times: int, election_type: str, timestamp: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)) -> int:
    user = pywikibot.User(site, username)
    if user.isRegistered():
        election_check: dict = database.LocalList.get_election_id(election_type, username, times)
        if election_check["flag"] == False:
            election_id: int = database.LocalList.create_a_sublist(username, times, election_type, timestamp)
            election = database.LocalList(election_id)
            voter_list: list[list] = election.voter_list
            wikitext_list = "\n".join(voter_list[0])
            wikitext_list = "{{Wikipedia:人事任免投票资格/名单/header}}" + "\n\n" \
                + "本页面为机器人依[[Wikipedia:人事任免投票资格]]为某场选举自动生成的合资格选民名单，全名单合计{person}人。".format(person=len(voter_list[0]))\
                + "\n\n" + "名单最后更新基准时间：{time}".format(time=timestamp) \
                + "\n\n" + "<pre>" + "\n" + wikitext_list + "\n" + "</pre>"
            main_list_page.text = wikitext_list
            summary = "新名单"
            page = pywikibot.Page(site, env["EVB_LIST_PREFIX"] + str(election_id))
            page.text = wikitext_list
            page.save(summary=summary)
            return election_id
        else:
            return -1
    else:
        return -2

def get_latest_username(username: str) -> str:
    finding: bool = True
    find_username = username
    while finding:
        user = pywikibot.User(site, find_username)
        if user.isRegistered():
            finding = False
            return find_username
        else:
            find_username = user.renamed_target().title(with_ns=False)

def maintenance_sublists() -> None:
    sublists_index: list = database.LocalList.get_elections_index()
    elections_id: list = []

    for sublists in sublists_index:
        if sublists[0]:
            elections_id.append(sublists[0])

    for election_id in elections_id:
        username_changes: list = []
        local_election = database.LocalList(election_id)
        voter_list = local_election.voter_list[1]
        for voter in voter_list:
            if voter == get_latest_username(voter):
                continue
            else:
                username_changes.append([voter, get_latest_username(voter)])

        if len(username_changes) == 0:
            continue
        else:
            new_voter_list: list = [local_election.voter_list[0], local_election.voter_list[1]]
            for change in username_changes:
                ori_username = change[0]
                ori_username_fmt = change[0] + "@zhwiki"
                new_username = change[1]
                new_username_fmt = change[1] + "@zhwiki"
                fmt_index: int = new_voter_list[0].index(ori_username_fmt)
                ori_index: int = new_voter_list[1].index(ori_username)
                new_voter_list[0][fmt_index] = new_username_fmt
                new_voter_list[1][ori_index] = new_username
            local_election.update_the_sublist(new_sublist=new_voter_list)
        
        if local_election.is_securePoll:
            pass
            # to do: send message to notification group.
        
        sub_list_page = pywikibot.Page(site, local_election.subpage_title)
        new_sub_list: list = local_election.voter_list
        wikitext_list = "\n".join(new_sub_list[0])
        wikitext_list = "{{Wikipedia:人事任免投票资格/名单/header}}" + "\n" \
             + "本页面为机器人依[[Wikipedia:人事任免投票资格]]自动生成的合资格选民名单，全名单合计{person}人。".format(person=len(local_election.voter_list[0]))\
             + "\n" + "名单最后更新基准时间：{time}".format(time=datetime.datetime.now(datetime.timezone.utc).strftime("%Y年%m月%d日%H时%M分%S秒（协调世界时）")) \
             + "\n" + "<pre>" + "\n" + wikitext_list + "\n" + "</pre>"
        sub_list_page.text = wikitext_list
        summary = "机器人已自动更新重命名用户：" + "、".join([f"{a} -> {b}" for a,b in username_changes])
        sub_list_page.save(summary=summary)

def new_nomination_detection() -> None:
    year: int = datetime.datetime.now(datetime.timezone.utc).year
    votes_in_zhwiki = pywikibot.Category(site, str(year) + "年維基百科投票")
    admin_votes = pywikibot.Category(site, "管理员任免投票")
    election_index_list: list = database.LocalList.get_elections_index()
    election_type_list: list[str] = ["管理员", "界面管理员", "行政员", "用户查核员", "监督员"]
    nominations = pagegenerators.CategoryFilterPageGenerator(pagegenerators.CategorizedPageGenerator(votes_in_zhwiki), [admin_votes])
    nominations_list: list[pywikibot.Page] = list(nominations)
    if len(nominations_list) == 0:
        return None
    else:
        nominations_list: list[str] = [page.title() for page in nominations_list]
        for page_title in nominations_list:
            if page_title.startswith("申请成为"):
                nomination_information: list[str] = page_title[4:].split('/')
                page_created_time: datetime.datetime= pywikibot.Page(page_title).oldest_revision.timestamp
                match nomination_information:
                    case [election_type, username]:
                        if election_type in election_type_list:
                            match election_type:
                                case "管理员":
                                    election_id: int = create_a_sublist(username, 1, "sysop", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "界面管理员":
                                    election_id: int = create_a_sublist(username, 1, "interface_admin", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "行政员":
                                    election_id: int = create_a_sublist(username, 1, "bureaucrat", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "用户查核员":
                                    election_id: int = create_a_sublist(username, 1, "checkuser", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "监督员":
                                    election_id: int = create_a_sublist(username, 1, "oser", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case _:
                                    # todo: log
                                    continue
                        else:
                            # todo: type not vaild.
                            continue
                    case [election_type, username, times]:
                        regex = re.search(r'第(.*?)次', times)
                        if regex:
                            times = int(regex.group(1))
                        else:
                            times = 1
                            
                        if election_type in election_type_list:
                            match election_type:
                                case "管理员":
                                    election_id: int = create_a_sublist(username, times, "sysop", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "界面管理员":
                                    election_id: int = create_a_sublist(username, times, "interface_admin", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "行政员":
                                    election_id: int = create_a_sublist(username, times, "bureaucrat", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "用户查核员":
                                    election_id: int = create_a_sublist(username, times, "checkuser", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case "监督员":
                                    election_id: int = create_a_sublist(username, times, "oser", page_created_time)
                                    if election_id >= 0:
                                        # todo: log
                                        continue
                                    else:
                                        # todo: log
                                        continue
                                case _:
                                    # todo: log
                                    continue
                        else:
                            # todo: type not vaild.
                            continue
                    case _:
                        # wokao
                        continue
            else:
                # todo: title error
                continue




                
    

