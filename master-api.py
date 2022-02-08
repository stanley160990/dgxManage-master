from lib2to3.pytree import Base
from typing import Optional
from fastapi import Request, FastAPI, Depends, File, Form, UploadFile, status
from fastapi.param_functions import Query
from requests.models import requote_uri
from libs.Config import Config
from libs.Connections import Psql
from libs.REST import REST
from pydantic import BaseModel

import uvicorn
import json
import datetime

class Create_minio(BaseModel):
    username: str
    password: str

class Build_update(BaseModel):
    img_name : str
    tag : str
    id : str
    token: str
    
class Run_update(BaseModel):
    id_container : str
    durasi_aktual : str
    id : str
    port: str
    
class Stop_update(BaseModel):
    id: str
    id_schedule: str

class Update_minio(BaseModel):
    username: str


app = FastAPI()

psql_con, psql_cur = Psql(Config().database_host, Config().database_port, Config().database_database, Config().database_user, Config().database_password).connect()


@app.get("/")
async def index():
    return_data = {"error": True, "message": "API DGX A100"}

    return return_data


@app.post("/approval")
async def project(DockerImages: str = Form(...), username: str = Form(...), id_hari: str = Form(...), durasi: str = Form(...), id_mesin: str = Form(...)):

    query_data_schedule = "select id_schedule from public.tbl_prototype_schedule_full where status='0' and id_hari = '"  + id_hari + "' and id_mesin='" + id_mesin + "' limit 1"
    psql_cur.execute(query_data_schedule)
    schedule_data = psql_cur.fetchone()

    if schedule_data is not None:
        update_schedule = "update public.tbl_prototype_schedule_full set status=1 where id_schedule='" + schedule_data[0] + "'"
        psql_cur.execute(update_schedule)
        psql_con.commit()

        select_user_sechedule = "select count(*) from public.tbl_prototype_schedule where username='" + username + "' and status='active'"
        psql_cur.execute(select_user_sechedule)
        jmlh_container = psql_cur.fetchone()[0]

        if jmlh_container < 3:

            query_url = "select url from public.tbl_mesin where id_mesin='" + id_mesin + "'"
            psql_cur.execute(query_url)
            url_data = psql_cur.fetchone()
            headers = {'Content-Type': 'application/json'}
            payload = {"id_hari": id_hari, "username": username, "DockerImages": DockerImages}

            agent_dockerfile_url = url_data[0] + "/Dockerfile"
            response_data = REST('POST', agent_dockerfile_url , headers, json.dumps(payload)).send()

            insert_data = (schedule_data[0], id_hari, "register", username, response_data.json()['working_folder'], durasi, id_mesin)
            psql_cur.execute("insert into public.tbl_prototype_schedule (id_schedule, hari, status, username, working_dir, durasi, id_mesin) values(%s, %s, %s, %s, %s, %s, %s)", insert_data)
            psql_con.commit()

            return_val = {"error": False, "message": "Container telah di daftarkan"}
        else:
            update_schedule = "update public.tbl_prototype_schedule_full set status=0 where id_schedule='" + schedule_data[0] + "'"
            psql_cur.execute(update_schedule)
            psql_con.commit()

            return_val = {"error": True, "message": "Telah Mencapai Limit (2)"}
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
        {'id':'1', 'nama': 'Senin'},
        {'id':'2', 'nama': 'Selasa'},
        {'id':'3', 'nama': 'Rabu'},
        {'id':'4', 'nama': 'Kamis'},
        {'id':'5', 'nama': 'Jumat'},
        {'id':'6', 'nama': 'Sabtu'},
        {'id':'7', 'nama': 'minggu'}
    ]}

@app.post('/schedule')
async def schedule_gen(id_hari: str = Form(...), id_mesin: str = Form(...)):
    if id_hari == "1":
        for x in range(0,8):
            for y in range (0,7):
                insert_data = ('1', '0', str(x) + ":" + str(y), id_mesin)
                psql_cur.execute("insert into public.tbl_prototype_schedule_full(id_hari, status, mig_device, id_mesin) values (%s,%s,%s,%s)", insert_data)
                psql_con.commit()
    elif id_hari == "2":
        for x in range(0,8):
            for y in range (0,7):
                insert_data = ('1', '0', str(x) + ":" + str(y), id_mesin)
                psql_cur.execute("insert into public.tbl_prototype_schedule_full(id_hari, status, mig_device, id_mesin) values (%s,%s,%s,%s)", insert_data)
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
    update_data_query = "update public.tbl_prototype_schedule set status='imageCreated', img_name='" \
         + update_data.img_name + "', tag=" + str(update_data.tag) + ",token='" +  update_data.token + "' where id='" + update_data.id + "'"
    psql_cur.execute(update_data_query)
    psql_con.commit()

    return_data = {"error": False, "message": "data build berhasil di update"}
    
    return return_data

# udpate For Run Data
@app.post("/run")
async def build_update(update_data: Run_update):
    update_data_query = "update public.tbl_prototype_schedule set status='run',id_container='" \
        + update_data.id_container + "', durasi_aktual=" + update_data.durasi_aktual +", port='" + update_data.port + "', token='"+ update_data.token +"' where id='" + update_data.id + "'"
    print(update_data_query)
    psql_cur.execute(update_data_query)
    psql_con.commit()

    return_data = {"error": False, "message": "data run berhasil di update"}
    
    return return_data
# update Stop Data
@app.post("/stop")
async def stop_update(update_data: Stop_update):
    update_data_query = "update public.tbl_prototype_schedule set status='stop' and id='"+ update_data.id +"'"
    psql_cur.execute(update_data_query)
    psql_con.commit()
    
    update_data1_query = "update public.tbl_prototype_schedule_full set status='0' where id_schedule='"+ update_data.id_schedule + "'"
    psql_cur.execute(update_data1_query)
    psql_con.commit()

    return_data = {"error": False, "message": "data stop berhasil di update"}

#Get Schedule_data
@app.get("/build/{id_hari}/{id_mesin}") 
async def get_build_schedule(id_hari, id_mesin):
    Query_data = "select working_dir, username, tag, id from public.tbl_prototype_schedule where hari='" + id_hari + "' and status='register' and id_mesin='" + id_mesin + "'"
    psql_cur.execute(Query_data)
    working_data = psql_cur.fetchall()

    return_data = []
    if working_data is not None:
        for data in working_data:
            schedule_data = {'working_dir': data[0], 'username': data[1], 'tag': data[2],
            'id':data[3]}
            return_data.append(schedule_data)
    else:
        return_data = []

    full_return_data = {"data": return_data} 

    return full_return_data

#Get Run Data
@app.get('/run/{id_hari}/{id_mesin}/{status}')
async def get_run_schedule(id_hari, id_mesin, status):
    Query_data = "select username, tag, id, id_schedule, durasi, durasi_aktual, id_container from public.tbl_prototype_schedule where hari='" + id_hari + "' and status='" + status + "' and id_mesin='" + id_mesin + "'"
    psql_cur.execute(Query_data)
    run_data = psql_cur.fetchall()

    return_data = []
    if run_data is not None:
        for data in run_data:
            schedule_data = {'username': data[0], 'tag': data[1], 'id': data[2],
            'id_schedule':data[3], 'durasi': data[4], 'durasi_aktual': data[5], 'id_container': data[6]}
            return_data.append(schedule_data)
    else:
        return_data = []

    full_return_data = {"data": return_data} 

    return full_return_data

#Get mig Device
@app.get('/mig/{id_schedule}')
async def get_mig_dev(id_schedule):
    query_mig = "select mig_device from tbl_prototype_schedule_full where id_schedule='" + id_schedule +"'"
    print(query_mig)
    psql_cur.execute(query_mig)
    mig_data = psql_cur.fetchone()[0]

    return_data = {"error":False, "mig_device": mig_data}

    return return_data

# Minio Object
@app.post('/minio')
async def create_minio(minio_data: Create_minio):
    url_data = psql_cur.fetchone()
    headers = {'Content-Type': 'application/json'}
    payload = {"username": minio_data.username, "password": minio_data.password}

    agent_dockerfile_url = Config().master_obs_url + "/Dockerfile"
    response_data = REST('POST', agent_dockerfile_url , headers, json.dumps(payload)).send()

    return_data ={"error": False, 'message': "success"}

    return return_data

#API Update From Client
@app.post('/minio/client')
async def update_minio_client(updateClient_minio: Update_minio):

    try:
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        insert_data = (updateClient_minio.username, "active", time_now)
        psql_cur.execute("insert into tbl_minio (username, status, created_date) values (%s,%s.%s)", insert_data)
        psql_con.commit()

        return_status = {"error": False, "message": "sukses mengupdate data"}
    except Exception as e:
        return_status = {"error": False, "message": str(e)}
    
    return return_status





    
    


if __name__ == "__main__":
    uvicorn.run("master-api:app", host="0.0.0.0", port=8181, log_level="info")
