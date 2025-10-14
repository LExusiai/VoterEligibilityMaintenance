from typing import Union
from fastapi import FastAPI
from enum import Enum
from . import database
import pywikibot

app = FastAPI()
site = pywikibot.Site('zh', 'wikipedia')

class ElectionTypes(str, Enum):
    sysop = "sysop"
    interface_admin = "interface_admin"
    bureaucrat = "bureaucrat"
    checkuser = "checkuser"
    oser = "oser"
    arbcom = "arbcom"

@app.get("/election/getid")
def get_election_id(election_type: ElectionTypes, username: str, times: int):
    user = pywikibot.User(site, username)
    registered_flag: bool = user.isRegistered()
    if registered_flag:
        elecion_informations: dict = database.LocalList.get_election_id(election_type, username, times)
        if elecion_informations["flag"]:
            response = {
                "flag": True,
                "election_type": election_type,
                "username": username,
                "times": times,
                "election_id": elecion_informations["election_id"]
            }
            return response
        else:
            response = {
                "flag": False,
                "tip": "No informations."
            }
            return response
    else:
        response = {
            "flag": False,
            "tip": "{username} is not registered.".format(username=username)
        }
        return response
    
@app.get("/election/eligibility")
def get_voter_eligibility(election_id: int, username: str):
    user = pywikibot.User(site, username)
    election_id_list: list = database.LocalList.get_elections_id_list()
    if election_id in election_id_list:
        if user.isRegistered():
            election = database.LocalList(election_id)
            voter_list: list = election.voter_list
            if username + "@zhwiki" in voter_list:
                response = {
                    "flag": True,
                    "voter_eligibility": True
                }
                return response
            else:
                response = {
                    "flag": True,
                    "voter_eligibility": False
                }
                return response
        else:
            response = {
                "flag": False,
                "tip": "username is not registered on zhwiki."
            }
            return response
    else:
        response = {
            "flag": False,
            "tip": "election id is not vaild."
        }
        return response