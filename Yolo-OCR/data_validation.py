#from extract_info_RUT import main_rut
#from extract_info_cedula import main_cedula
import os
#from pdf2image import convert_from_bytes,convert_from_path
import pandas as pd
import numpy as np
import re
import pymysql
import config
import unidecode
import cv2
from extract_info_cedula import main_cedula
from extract_info_RUT import main_rut
from pdf2image import convert_from_bytes,convert_from_path

def bd_connection(host_db, user, password, db_name, id_user):
    try:
        # Abre conexion con la base de datos
        conn = pymysql.connect(host=host_db, user=user, password=password, database=db_name)
        # Query para extraer la data de la base de datos
        sql_query = pd.read_sql_query('''
                                       SELECT 
                                            id, usersId, name, nit, identificacion, 
                                            CONCAT (primerNombre, ' ' , segundoNombre) as Nombres,
                                            CONCAT (primerApellido, ' ', segundoApellido) as Apellidos
                                       FROM organizations
                                       WHERE id = {idUser}
                                       '''.format(idUser=id_user), conn)
        # desconecta del servidor
        conn.close()
        return sql_query
    except Exception as err:
        print('Error encontrado: ' + str(err))
        return pd.DataFrame()

def get_info(ip_server, username_bd, password_bd,
                         database, id_user):
    data = bd_connection(ip_server, username_bd, password_bd,
                         database, id_user)
    if data.empty:
        # En caso que el id de usuario no exista en base de datos, devuelve este mensaje
        message = 'No existen datos asociados a este usuario en base de datos'
    else:
        # Se pasa a mayúscula todos los registros de estas columnas
        cols_to_upper = ['name', 'Nombres','Apellidos']
        data[cols_to_upper] = data[cols_to_upper].apply(lambda x: x.astype(str).str.upper())
        # Se omiten puntos, comas y espacios en la columna identificación y se reemplaza _ por - en columna nit
        data['identificacion'] = data['identificacion'].\
            str.replace('.', '', regex=False).\
            str.replace(',', '', regex=False).\
            str.strip()
        data['nit'] = data['nit'].\
            str.replace('.', '', regex=False).\
            str.replace(',', '', regex=False).\
            str.replace('_', '-', regex=False).\
            str.strip().\
            str.split('-')[0][0]
        # Se quitan caracteres especiales y ñ de la columna nombreCompleto
        data['Nombres'] = data['Nombres'].apply(lambda x: unidecode.unidecode(x).replace('  ', ' ').strip())
        data['Apellidos'] = data['Apellidos'].apply(lambda x: unidecode.unidecode(x).replace('  ', ' ').strip())
        data['name'] = data['name'].apply(lambda x: unidecode.unidecode(x).replace('  ', ' '))
        # obtener solo elemntos alphanuemricos
        data['Nombres'] = data['Nombres'].apply(lambda x: re.sub(r'\W+', '', x))
        data['Apellidos'] = data['Apellidos'].apply(lambda x: re.sub(r'\W+', '', x))
        data['name'] = data['name'].apply(lambda x: re.sub(r'\W+', '', x))
        
        message = 'ok'
        response = {'response': message, 'data': data}
        return response

def compare_metric(string_extracted,string_real):
  i=0
  jj=0
  for element_extracted in string_extracted:
    for j,element_real in enumerate(string_real[jj:]):
      if element_extracted==element_real:        
        i+=1
        jj += j
        break
  return (2*i)/(len(string_real)+len(string_extracted))

def check_number(file_name):
  return any(char.isdigit() for char in file_name)

path_img_id='/content/Yolo-OCR/Yolo-OCR/cedulaRepresentante-56.pdf'
path_img_rut='/content/Yolo-OCR/Yolo-OCR/registroUnico-56.pdf'
image_raw_id = convert_from_path(path_img_id)
image_raw_id = np.asarray(image_raw_id[0])
image_raw_rut = convert_from_path(path_img_rut)
image_raw_rut = np.asarray(image_raw_rut[0])

class_id= main_cedula(config.config_file_id,
                                config.data_file_id,config.weights_id,0.25)
class_id.load_darknet()
class_rut= main_rut(config.config_file_rut,
                            config.data_file_rut,config.weights_rut,0.25)
class_rut.load_darknet()

result_id = class_id.main_cedula_run(image_raw_id)
result_rut = class_rut.main_cedula_run(image_raw_rut)

ip_server = '190.7.134.180'
# Authentication data for BD pruebas
username_bd = 'julian_c'
password_bd = 'Julian_c_unal_2021'
database = 'pruebas_adr'
id_user = int(re.findall(r'\d+', path_img_id)[0])
response = get_info(config.ip_server, config.username_bd, 
                    config.password_bd,config.database, id_user)

nombres_metric=compare_metric(result_id['nombres'],
                response['data']['Nombres'].values[0])
apellidos_metric=compare_metric(result_id['apellidos'],
               response['data']['Apellidos'].values[0])
numero_metric=compare_metric(result_id['numero'],
               response['data']['identificacion'].values[0])
nit_metric=compare_metric(result_rut['NIT'],
               response['data']['nit'].values[0])
rs_metric=compare_metric(result_rut['RS'],
               response['data']['name'].values[0])
print('nombres_metric',nombres_metric)
print('apellidos_metric',apellidos_metric)
print('numero_metric',numero_metric)
print('nit_metric',nit_metric)
print('rs_metric',rs_metric)