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
def get_qualified_voter_list(timestamp: datetime.datetime) -> list[list]:
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
            timestamp = timestamp.strftime("%Y%m%d%H%M%S") # type: ignore # waht? why?
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

# Voter datas stored in the ToolsDB        
class LocalList():
    def __init__(self, election_id) -> None:
        self.election_id: int = election_id

    # Before you use this method to do anything, please make sure the main list has been added into the database.
    @staticmethod
    def update_the_mainlist() -> bool:
        connection = get_toolsdb_connection(env['EVB_DB_NAME'])
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
            local_voter_list: list = json.loads(result[0])
        if local_voter_list == json.loads(voter_list):
            return True
        else:
            return False

    def update_the_sublist(self, new_sublist: list) -> bool:
        connection = get_toolsdb_connection(env['EVB_DB_NAME'])
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
                updated_list: list = json.loads(result[0])
                if updated_list == new_sublist:
                    return True
                else:
                    return False
    
    @staticmethod
    def create_a_sublist(username: str, times: int, election_type:str, eligibility_deadline: datetime.datetime) -> int:
        sublist: list = get_qualified_voter_list(eligibility_deadline)
        sql = '''
        INSERT INTO election_list ( 
        username, 
        times,
        election_type,
        voter_list
        )
        SELECT %s AS username, %s AS times, %s AS election_type, %s AS voter_list
        FROM election_list
        WHERE election_id = 0;
        '''
        connection = get_toolsdb_connection(env['EVB_DB_NAME'])
        with connection.cursor() as cursor:
            cursor.execute(sql,(username, times, election_type, json.dumps(sublist)))
            connection.commit()
            sql = 'SELECT election_id, username, times, voter_list FROM election_list WHERE username = %s AND times = %s AND election_types = %s;'
            cursor.execute(sql, (username, times, election_type,))
            result = cursor.fetchone()
            result = (result[0], result[1].decode('utf-8'), result[2].decode('utf-8'),)
            if result[1] == username and result[2] == str(times):
                return result[0]
            else:
                return -1
            

    @staticmethod
    def get_elections_index() -> list:
        sql = '''SELECT election_id, username, times, election_type FROM election_list WHERE election_id > 0;'''
        elections = []
        with get_toolsdb_connection(env['EVB_DB_NAME']).cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            for s in result:
                elections.append([s[0], s[1].decode('utf-8'), s[2].decode('utf-8'), s[3].decode('utf-8')])
        return elections
    
    @staticmethod
    def get_elections_id_list() -> list:
        sql = '''SELECT election_id FROM election_list;'''
        elections = []
        with get_toolsdb_connection(env['EVB_DB_NAME']).cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            for s in result:
                elections.append(s)
        return elections
    
    @staticmethod
    def get_election_id(election_type: str, username: str, times: int) -> dict:
        sql = '''SELECT election_id FROM election_list WHERE election_type = %s AND username = %s AND times = %s;'''
        connection: pymysql.Connection = get_toolsdb_connection(env['EVB_DB_NAME'])
        with connection.cursor() as cursor:
            cursor.execute(sql, (election_type, username, times,))
            result = cursor.fetchone()
            if len(result) == 0:
                response = {
                    "flag": False
                }
                return response
            else:
                election_id: int = result[0]
                response = {
                    "flag": True,
                    "election_id": election_id
                }
                return response

    @property
    def voter_list(self) -> list:
        sql = 'SELECT voter_list FROM election_list WHERE election_id =%s;'
        with get_toolsdb_connection(env['EVB_DB_NAME']).cursor() as cursor:
            cursor.execute(sql, (self.election_id,))
            result = cursor.fetchone()
            return json.loads(result[0])
        
    @property
    def subpage_title(self) -> str:
        connection = get_toolsdb_connection(env['EVB_DB_NAME'])
        sql = 'SELECT username, times, election_type FROM election_list WHERE election_id = %s'
        with connection.cursor() as cursor:
            cursor.execute(sql,(self.election_id,))
            result = cursor.fetchone()
            vote_information: list = [value.decode('utf-8') for value in result]
            prefix: str = env["EVB_LIST_PREFIX"]
            return "prefix" + "/" + vote_information[2] + "/" + vote_information[0] + "/" + vote_information[1]
        
    @property
    def is_securePoll(self) -> bool:
        connection = get_toolsdb_connection(env["EVB_DB_NAME"])
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