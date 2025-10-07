from typing import Union
from fastapi import FastAPI
from . import database

app = FastAPI()

@app.get("/election/is_eligibility/{election_id}")
def is_eligibility(election_id: int, username: str) -> dict:
    election = database.LocalList(election_id=election_id)
    voter_list: list = election.voter_list
    if username == "":
        response = {
            "successful_flag": False
        }
        return response
    else:
        if "@zhwiki" in username:
            if username in voter_list[0]:
                response = {
                    "successful_flag": True,
                    "election_id": election,
                    "eligibility": True
                }
                return response
            else:
                response = {
                    "successful_flag": True,
                    "election_id": election,
                    "eligibility": False
                }
                return response
        else:
            if username in voter_list[1]:
                response = {
                    "successful_flag": True,
                    "election_id": election,
                    "eligibility": True
                }
                return response
            else:
                response = {
                    "successful_flag": True,
                    "election_id": election,
                    "eligibility": False
                }
                return response
            
@app.get("/election/index_query")
def index_query(username: str, times: str, election_type: str):
    election_index = database.LocalList.get_elections_index()
    for election in election_index:
        if election[1] == username and election[2] == times and election[3] ==election_type:
            response = {
                "successful_flag": True,
                "election_id": election[0]
            }
            return response
        else:
            continue
        
    response = {
        "successful_flag": False
    }
    return response
        