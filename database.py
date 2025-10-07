# -*- coding: utf-8 -*-

import toolforge
import datetime
import json
import os
import pymysql
import pathlib
import configparser

env = os.environ
# The function will return a list including two lists: fmt_voter_list and voter_list.
# The usernames in fmt_voter_list have a suffix "@zhwiki", and the usernames in voter_list are not.
def get_qualified_voter_list(timestamp: datetime.datetime) -> list:
    connection: pymysql.Connection = toolforge.connect('zhwiki')
    with connection:
        with connection.cursor() as cursor:
            # Thanks for Stang's SQL. I adjusted some sentences to make it working with pymysql.
            # D180, CUR, D180
            sql = '''
            SELECT u.user_name as username
            FROM user u
            INNER JOIN actor a ON u.user_id = a.actor_user
            INNER JOIN(
            SELECT r.rev_actor, COUNT(*) as recent_edits
            FROM revision_userindex r
            INNER JOIN page p ON r.rev_page = p.page_id
            WHERE r.rev_timestamp >= %s
                AND r.rev_timestamp <= %s
                AND p.page_namespace NOT IN (2, 3)
            GROUP BY r.rev_actor
            HAVING recent_edits >= 10
            ) recent ON a.actor_id = recent.rev_actor
            WHERE
                (u.user_registration IS NULL OR u.user_registration <= %s)
                AND u.user_is_temp = 0
                AND u.user_editcount >= 500
                AND u.user_id NOT IN (
                    SELECT ug.ug_user
                    FROM user_groups ug
                    WHERE ug.ug_group = 'bot'
                )
                AND u.user_name NOT LIKE 'Renamed user %'
            ORDER BY u.user_name;
            '''
            time_delta = datetime.timedelta(days=180)
            latest_time = timestamp - time_delta
            timestamp = str(timestamp.strftime("%Y%m%d%H%M%S"))
            latest_time = str(latest_time.strftime("%Y%m%d%H%M%S"))
            cursor.execute(sql, (latest_time,timestamp,latest_time,))
            result = cursor.fetchall()
            suffix = "@zhwiki"
            fmt_voter_list = [data[0].decode('utf-8') + suffix for data in result]
            voter_list = [data[0].decode('utf-8') for data in result]
            return [fmt_voter_list, voter_list]

def get_toolsdb_connection(database_name: str) -> pymysql.connections.Connection:
    toolsdb = pathlib.Path.home().joinpath("replica.my.cnf")
    config = configparser.ConfigParser()
    config.read_string(toolsdb.read_text())
    connection = pymysql.connections.Connection(
        host="tools.db.svc.wikimedia.cloud",
        database=database_name,
        user=config.get("client", "user"),
        password=config.get("client", "password")
    )
    return connection

def is_admin(userid: int) -> bool:
    pass

# Voter datas stored in the ToolsDB        
class LocalList():
    def __init__(self, election_id) -> None:
        self.election_id: int = election_id

    # Before you use this method to do anything, please make sure the main list has been added into the database.
    @staticmethod
    def update_the_mainlist() -> bool:
        connection = get_toolsdb_connection(env['EVB_DB_Name'])
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        voter_list: str = json.dumps(get_qualified_voter_list(timestamp))
        sql: str = '''
        UPDATE election_list
        SET voter_list = %s
        WHERE election_id = 0;
        '''
        with connection.cursor() as cursor:
            cursor.execute(sql,(voter_list,))
            connection.commit()
            sql = ''' SELECT voter_list FROM election_list WHERE election_id = 0;'''
            cursor.execute(sql)
            result = cursor.fetchone()
            local_voter_list: list = json.loads(result[0].decode('utf-8'))
        if local_voter_list == json.loads(voter_list):
            return True
        else:
            return False

    def update_the_sublist(self, new_sublist: list) -> bool:
        connection = get_toolsdb_connection(env['EVB_DB_Name'])
        if new_sublist == None:
            return False
        else:
            payload: str = json.dumps(new_sublist)
            sql = '''
            UPDATE election_list
            SET voter_list = %s
            WHERE election_id = %s
            '''
            with connection.cursor() as cursor:
                cursor.execute(sql,(payload, self.election_id,))
                connection.commit()
                sql = '''SELECT voter_list FROM election_list WHERE election_id = %s'''
                cursor.execute(sql,(self.election_id,))
                result = cursor.fetchone()
                updated_list: list = json.loads(result[0].decode('utf-8'))
                if updated_list == new_sublist:
                    return True
                else:
                    return False
    
    @staticmethod
    def create_a_sublist(username: str, times: int, election_type: str, page_created_time: int, page_created_user: str) -> list:
        update_status: bool = LocalList.update_the_mainlist()
        if update_status == True:
            sql = '''
            INSERT INTO election_list ( 
            username, 
            times,
            election_type,
            voter_list,
            created_time,
            page_created_user
            )
            SELECT %s AS username, %s AS times, %s AS election_type, voter_list, %s AS created_time, %s AS page_created_user
            FROM election_list
            WHERE election_id = 0;
            '''
            connection = get_toolsdb_connection(env['EVB_DB_Name'])
            with connection.cursor() as cursor:
                cursor.execute(sql, (username, times, election_type, page_created_time, page_created_user,))
                connection.commit()
                sql = 'SELECT election_id, username, times, voter_list FROM election_list WHERE username = %s AND times = %s AND election_type = %s;'
                cursor.execute(sql, (username, times, election_type,))
                result = cursor.fetchone()
                result = (result[0], result[1].decode('utf-8'), result[2].decode('utf-8'), result[3].decode('utf-8'),)
                if result[1] == username and result[2] == str(times):
                    datas = [result[0], json.loads(result[3])]
                    return datas
                else:
                    return [-1]
        else:
            return [-2]

    @staticmethod
    def get_elections_index() -> list:
        sql = '''SELECT election_id, username, times, election_type FROM election_list WHERE election_id > 0;'''
        elections = []
        with get_toolsdb_connection(env['EVB_DB_Name']).cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            for s in result:
                elections.append([s[0], s[1].decode('utf-8'), s[2].decode('utf-8'), s[3].decode('utf-8')])
        return elections

    @property
    def voter_list(self) -> list:
        sql = 'SELECT voter_list FROM election_list WHERE election_id =%s;'
        with get_toolsdb_connection(env['EVB_DB_Name']).cursor() as cursor:
            cursor.execute(sql, (self.election_id,))
            result = cursor.fetchone()
            return json.loads(result[0].decode('utf-8'))
    
    @property
    def nomination_page_created_time(self) -> str:
        sql = 'SELECT created_time FROM election_list WHERE election_id =%s;'
        with get_toolsdb_connection(env['EVB_DB_Name']).cursor() as cursor:
            cursor.execute(sql, (self.election_id,))
            result = cursor.fetchone()
            page_created_time = json.loads(result[0])
            return page_created_time
        
    @property
    def subpage_title(self) -> str:
        connection = get_toolsdb_connection(env['EVB_DB_Name'])
        sql = 'SELECT username, times, election_type FROM election_list WHERE election_id = %s'
        with connection.cursor() as cursor:
            cursor.execute(sql,(self.election_id,))
            result = cursor.fetchone()
            vote_information: list = [value.decode('utf-8') for value in result]
            prefix: str = env["EVB_LIST_PREFIX"]
            return "prefix" + "/" + vote_information[2] + "/" + vote_information[0] + "/" + vote_information[1]
        
    @property
    def is_securePoll(self) -> bool:
        connection = get_toolsdb_connection(env["EVB_DB_Name"])
        sql = 'SELECT election_id FROM SecurePoll WHERE election_id = %s'
        with connection.cursor() as cursor:
            cursor.execute(sql, (self.election_id,))
            row = cursor.fetchone()
            if not row:
                return False
            else:
                if row[0] == self.election_id:
                    return True
                else:
                    return False
            