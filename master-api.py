from cProfile import run
from email import message
from lib2to3.pytree import Base
# from re import X
from typing import Optional
from fastapi import Request, FastAPI, Depends, File, Form, UploadFile, status
from fastapi.param_functions import Query
# from requests.models import requote_uri
from libs.Config import Config
from libs.Connections import Psql
from libs.REST import REST
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from libs.Connections import Ldap

from ldap3.utils.hashed import hashed
from ldap3 import MODIFY_REPLACE, HASHED_SALTED_SHA

import uvicorn
import json
import datetime


class Build_update(BaseModel):
    img_name : str
    tag : str
    id : str
    
    
class Run_update(BaseModel):
    id_container : str
    id : str
    port: str
    token: str

class Stop_update(BaseModel):
    id: str
    id_schedule: str


app = FastAPI()

origins = [
    "https://ai-coe.gunadarma.ac.id",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


psql_con, psql_cur = Psql(Config().database_host, Config().database_port, Config().database_database, Config().database_user, Config().database_password).connect()
ldap_conn = Ldap(Config().ldap_host, Config().ldap_port, Config().ldap_username, Config().ldap_password).connect()

@app.get("/")
async def index():
    return_data = {"error": True, "message": "API DGX A100"}

    return return_data

@app.post("/ldap")
async def post_ldap(username: str = Form(...), password: str = Form(...), mail: str = Form(...), telephoneNumber: str = Form(...), givenName: str = Form(...)):
    
    free_username = username.replace('@', '_at_')
    
    user = "cn=" + free_username + ",ou=user,dc=ai-coe,dc=gunadarma,dc=ac,dc=id"

    hash_pass = hashed(HASHED_SALTED_SHA, password)
    givenName_split = givenName.split(" ")

    sn = givenName_split[0]

    data = {"givenname":givenName, "mail": mail, "sn": sn, "userpassword": hash_pass, "telephoneNumber": telephoneNumber, 'uid': free_username}

    try:
        ldap_conn.add(user, ["inetOrgPerson", "organizationalPerson", "top", "person"], data)
        return_data = {"error": False, "message": "Ldap berhasil ditambhakan"}
    except Exception as e:
        return_data = {"error": True, "message": str(e)}
    
    return return_data

# Aksi Aproval Proposal
@app.post("/approval")
async def project(DockerImages: str = Form(...), username: str = Form(...), id_hari: str = Form(...), durasi: str = Form(...), id_mesin: str = Form(...)):

    # GET id_schedule from tbl_prototype_schedule_full
    query_data_schedule = "select id_schedule from public.tbl_gpu_schedule where status=%s and id_hari = %s and id_mesin=%s limit 1"
    select_data = (True, id_hari, id_mesin)
    psql_cur.execute(query_data_schedule, select_data)
    schedule_data = psql_cur.fetchone()

    if schedule_data is not None:
        # update id_schedule to occupay
        update_schedule = "update public.tbl_gpu_schedule set status=%s where id_schedule=%s"
        update_data = (False, schedule_data[0])
        psql_cur.execute(update_schedule, update_data)
        psql_con.commit()

        # Get DGX URL
        query_url = "select url from public.tbl_mesin where id_mesin='" + id_mesin + "'"
        psql_cur.execute(query_url)
        url_data = psql_cur.fetchone()

        # Build Rest Data
        headers = {'Content-Type': 'application/json'}
        payload = {"id_hari": id_hari, "username": username, "DockerImages": DockerImages}
        agent_dockerfile_url = url_data[0] + "/Dockerfile"

        # Send to Agent REST API
        response_data = REST('POST', agent_dockerfile_url , headers, json.dumps(payload)).send()


        # Update Data from return
        # prod
        insert_data = (schedule_data[0], id_hari, username, response_data.json()['working_folder'], durasi, id_mesin, response_data.json()['docker_file'], True)
        # dev only
        # insert_data = (schedule_data[0], id_hari, username, "x", durasi, id_mesin, "Y", True)
        psql_cur.execute("insert into public.tbl_flow_approval (id_schedule, id_hari, username, working_dir, durasi, id_mesin, docker_file, created_at, active) values(%s,%s, %s, %s, %s, %s, %s, (now() at time zone 'utc'), %s)", insert_data)
        psql_con.commit()

        return_val = {"error": False, "message": "Container telah di daftarkan"}
    
    elif schedule_data is None:
        return_val = {"error": True, "message": "jadwal penuh!!!"}


    return return_val

@app.post('/mesin')
async def add_mesin(nama_mesin: str = Form(...), url : str = Form(...), description: str = Form(...), gpu: str = Form(...), mig_pergpu: str = Form(...)):
    insert_data = (nama_mesin, 'active', description, url, gpu, mig_pergpu)
    psql_cur.execute("insert into public.tbl_mesin(nama_mesin, status, description, url, gpu, mig_pergpu) values (%s,%s,%s,%s,%s,%s)", insert_data)
    psql_con.commit()
    
    return_status = {'error': False, 'message': 'mesin_berhasil_ditambah'}

    return return_status

@app.get('/mesin')
async def get_mesin():
    query_url = "select * from public.tbl_mesin"
    psql_cur.execute(query_url)
    mesin_data = psql_cur.fetchall()

    return_data = []
    for data in mesin_data:
        mesin_data = {'id_mesin': data[0], 'nama_mesin': data[1], 'status': data[2], 'description': data[3], 'url': data[4], 'gpu':data[5], 'mig_pergpu': data[6]}
        return_data.append(mesin_data)
    
    full_return_data = {"error": False, "data": return_data}

    return full_return_data

@app.get('/hari')
async def get_hari():
    return {"error": False, "data":[
        {'id':'10', 'nama': "RSC GPU 20G (max 8)"},
        {'id':'11', 'nama': "RSC GPU 40G (max 4)"},
        {'id':'12', 'nama': "RSC CPU"}
    ]}

@app.post('/schedule')
async def schedule_gen(id_hari: str = Form(...), id_mesin: str = Form(...)):
    if id_hari == "10":
        for x in range(0,4):
            for y in range (0,2):
                insert_data = (str(id_hari), True, str(x) + ":" + str(y), id_mesin)
                psql_cur.execute("insert into public.tbl_gpu_schedule(id_hari, status, mig_device, id_mesin) values (%s,%s,%s,%s)", insert_data)
                psql_con.commit()
    
    elif id_hari == "11":
        for x in range(4,8):
            insert_data = (str(id_hari), True, str(x) , id_mesin)
            psql_cur.execute("insert into public.tbl_gpu_schedule(id_hari, status, mig_device, id_mesin) values (%s,%s,%s,%s)", insert_data)
            psql_con.commit()



    retrun_status = {"error": False, "message": "schedule Telah Ditambahkan"}
    return retrun_status

@app.get('/schedule/{id_hari}/{id_mesin}')
async def get_schedule(id_hari, id_mesin):
    query_schedule = "select id_schedule, id_mesin from public.tbl_prototype_schedule_full where id_hari='" + id_hari +"' and id_mesin='"+ id_mesin+"' and status='0'"
    psql_cur.execute(query_schedule)
    schedule_data = psql_cur.fetchall()

    return_data = []
    for schedule in schedule_data:
        data = {'id_schedule': schedule[0], 'id_mesin':schedule[1]}
        return_data.append(data)
    
    full_return_data = {'error': False, 'data': return_data}

    return full_return_data

# update For Build Data
@app.post("/build")
async def build_update(update_data: Build_update):
    select_approval_data_query = """SELECT id_approval, id_schedule, id_hari, username, working_dir, durasi, id_mesin, docker_file, 
    created_at,active FROM public.tbl_flow_approval where id_approval=%s"""
    select_approval_data = (update_data.id,)
    psql_cur.execute(select_approval_data_query, select_approval_data)
    approval_data = psql_cur.fetchone()

    # Insert build data + move approval data
    insert_data_query = """insert into public.tbl_flow_build (tag, img_name, id_approval, id_schedule, id_hari, username, working_dir, 
    durasi, id_mesin, docker_file, created_at, active) 
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,(now() at time zone 'utc'), %s)"""
    insert_data = (str(update_data.tag), update_data.img_name, approval_data[0], approval_data[1], approval_data[2], approval_data[3], 
                    approval_data[4], approval_data[5], approval_data[6], approval_data[7], True)
    psql_cur.execute(insert_data_query, insert_data)
    psql_con.commit()

    update_data_approval_query = "update public.tbl_flow_approval set active=%s where id_approval=%s"
    update_data_approval = (False, update_data.id)
    psql_cur.execute(update_data_approval_query, update_data_approval)
    psql_con.commit()

    return_data = {"error": False, "message": "data build berhasil di update"}
    
    return return_data

# udpate For Run Data
@app.post("/run")
async def build_update(update_data: Run_update):

    #select Build Data
    select_build_data_query = """SELECT tag, img_name, id_approval, id_schedule, id_hari, username, working_dir, durasi, id_mesin, 
    docker_file FROM public.tbl_flow_build where id_approval=%s;"""
    select_build_data = (update_data.id,)
    psql_cur.execute(select_build_data_query, select_build_data)
    build_data = psql_cur.fetchone()

    # Insert run data + move build data
    insert_data_query = """insert into public.tbl_flow_run (id_container, port, jupyter_token, tag, img_name, id_approval, id_schedule, 
    id_hari, username, working_dir, durasi, id_mesin, docker_file, running_at, active) 
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,(now() at time zone 'utc'), %s)"""
    insert_data = (update_data.id_container, update_data.port, update_data.token, build_data[0], build_data[1],build_data[2],build_data[3],
                    build_data[4],build_data[5],build_data[6],build_data[7],build_data[8], build_data[9],True)
    psql_cur.execute(insert_data_query, insert_data)
    psql_con.commit()

    update_data_build_query = "update public.tbl_flow_build set active=%s where id_approval=%s"
    update_data_build = (False, update_data.id) 
    psql_cur.execute(update_data_build_query, update_data_build)
    psql_con.commit()

    return_data = {"error": False, "message": "data run berhasil di update"}
    
    return return_data

# update Stop Data
@app.post("/stop")
async def stop_update(update_data: Stop_update):
    update_data_run_query = "update public.tbl_flow_run set active=%s, stoped_at=(now() at time zone 'utc') where id_approval=%s"
    update_data_run=(False, update_data.id)
    psql_cur.execute(update_data_run_query, update_data_run)
    psql_con.commit()
    
    update_data_gpu_query = "update public.tbl_gpu_schedule set active=%s where id_schedule=%s"
    update_data_gpu=(False, update_data.id_schedule)
    psql_cur.execute(update_data_gpu_query, update_data_gpu)
    psql_con.commit()

    return_data = {"error": False, "message": "data stop berhasil di update"}

    return return_data

#Get approval data -> internal usage
@app.get("/approval/{id_hari}/{id_mesin}") 
async def get_build_schedule(id_hari, id_mesin):
    Query_data_query = "select working_dir, username, tag, id_approval, docker_file from public.tbl_flow_approval where id_hari=%s and active=%s and id_mesin=%s"
    Query_data = (id_hari, True, id_mesin)
    psql_cur.execute(Query_data_query, Query_data)
    working_data = psql_cur.fetchall()

    return_data = []
    if working_data is not None:
        for data in working_data:
            schedule_data = {'working_dir': data[0], 'username': data[1], 'tag': data[2],
            'id':data[3], 'docker_file':data[4]}
            return_data.append(schedule_data)
    else:
        return_data = []

    full_return_data = {"data": return_data} 

    return full_return_data

# Get Build Data -> Internal Usage
@app.get('/build/{id_hari}/{id_mesin}')
async def get_run_schedule(id_hari, id_mesin):
    run_data_query = "select id_schedule, img_name, tag, id_approval, from tbl_flow_build where id_hari=%s, id_mesin=%s, action=%s"
    
    run_data = (id_hari, id_mesin, True)
    psql_cur.execute(run_data_query, run_data)

    run_data = psql_cur.fetchall()

    return_data = []
    if run_data is not None:
        for data in run_data:
            schedule_data = {'id_schedule': data[0], 'img_name': data[1], 'tag': data[2], 'id': data[3]}
            return_data.append(schedule_data)
    
    return return_data

#------------------------- Eksternal API ----------------------------------------------------------------------------
#Get Run Data per user -> Eksternal Usage
@app.get('/run/{id_hari}/{id_mesin}/{status}/{user}')
async def get_run_schedule(id_hari, id_mesin, status, user):

    psql_cur.execute("select url from tbl_mesin where id_mesin='"+ id_mesin +"'")
    url_mesin = psql_cur.fetchone()[0]
    lst_mesin = url_mesin.split(":")
    

    psql_cur.execute("select id_container, jupyter_token, active, port from public.tbl_flow_run where username='" + user + "' and id_hari='" + id_hari + "'")
    approval_data = psql_cur.fetchall()
    return_data = []
    for approval in approval_data:

        if approval[2] is True:
            status = 'running'
        else:
            status = 'stop'
        
        url_jupyter = lst_mesin[0] + ":" + lst_mesin[1] + ":" + approval[3]

        running_data = {"id_container":approval[0], 'url_jupyter': url_jupyter, 'token': approval[1], 'status': status}

        return_data.append(running_data)
    
    
    full_return_data = {"data": return_data} 

    return full_return_data

#Get mig Device -> internal Usage
@app.get('/mig/{id_schedule}')
async def get_mig_dev(id_schedule):
    query_mig = "select mig_device from tbl_gpu_schedule where id_schedule='" + id_schedule +"'"
    print(query_mig)
    psql_cur.execute(query_mig)
    mig_data = psql_cur.fetchone()[0]

    return_data = {"error":False, "mig_device": mig_data}

    return return_data

#rgistrasi_pelatihan
@app.post('/pelatihan')
async def create_pelatihan():
    print()

@app.get('/pelatihan/{user}')
async def get_pelatihan():
    print()

if __name__ == "__main__":
    uvicorn.run("master-api:app", host="0.0.0.0", port=8181, log_level="info")
