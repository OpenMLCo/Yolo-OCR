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

def main():
  # load darknet
  class_id= main_cedula(config.config_file_id,
                                  config.data_file_id,config.weights_id,0.25)
  class_id.load_darknet()
  class_rut= main_rut(config.config_file_rut,
                              config.data_file_rut,config.weights_rut,0.25)
  class_rut.load_darknet()
  ## load info
  folder_path=config.folder_path
  folder_names = os.listdir(folder_path)
  filer_required=config.filer_required
  columns=config.columns
  df=pd.DataFrame(columns=columns)
  for folder in folder_names:
    files_names = os.listdir(folder_path+folder)
    log = ''
    file_numbers=[re.findall(r'\d+', files)[0] for files in files_names if check_number(files)]
    if len(file_numbers)>0:
      file_numbers=np.unique(file_numbers)
    else:
      elements = {'folde_ID':folder,
              'cedulaRepresentante':'no',
              'registroUnico':'no',
              'certificadoExistencia':'no',
              'Log':'NO existen archivos con - numero',
              'ID':'',
              'cedulaRepresentante_match':'no',
              'registroUnico_match':'no',
              'prob_cedula_nombres':0,
              'prob_cedula_apellidos':0,
              'prob_cedula_numero':0,
              'prob_rut_RS':0,
              'prob_rut_NIT':0}
      df = df.append(elements, ignore_index = True)
      continue
    for number_id in file_numbers:
      response = get_info(config.ip_server, config.username_bd, 
                      config.password_bd,config.database, number_id)
      elements = {'folde_ID':folder,
                  'cedulaRepresentante':'no',
                  'registroUnico':'no',
                  'certificadoExistencia':'no',
                  'Log':'',
                  'ID':number_id,
                  'cedulaRepresentante_match':'no',
                  'registroUnico_match':'no',
                  'prob_cedula_nombres':0,
                  'prob_cedula_apellidos':0,
                  'prob_cedula_numero':0,
                  'prob_rut_RS':0,
                  'prob_rut_NIT':0}
      if not response:
        elements['Log']=log+'El ID no existe en la base de datos'
        df = df.append(elements, ignore_index = True)
        continue
      element_names = [file_name for file_name in files_names if number_id in file_name] 
      for file_name in element_names:
        if file_name.split('-')[0] in filer_required:
          try:
            image = np.asarray(convert_from_path(folder_path+folder+'/'+file_name,last_page=1,thread_count=-1)[0])
            elements[file_name.split('-')[0]] = 'si'
            if file_name.split('-')[0]=='cedulaRepresentante':
              result_id,log_ = class_id.main_cedula_run(image)
              log+=log_+'\n'
              # extract info OCR
              elements['prob_cedula_nombres']=np.round(100*compare_metric(re.sub(r'\W+', '', result_id['nombres']),
                                            response['data']['Nombres'].values[0]),1)
              elements['prob_cedula_apellidos']=np.round(100*compare_metric(re.sub(r'\W+', '',result_id['apellidos']),
                                            response['data']['Apellidos'].values[0]),1)
              elements['prob_cedula_numero']=np.round(100*compare_metric(re.sub(r'\W+', '',result_id['numero']),
                                            response['data']['identificacion'].values[0]),1)
              if elements['prob_cedula_numero'] >= 90:
                elements['cedulaRepresentante_match']='si'
              elif (int(elements['prob_cedula_numero'] >= 70) + int(elements['prob_cedula_nombres']>=70) + int(elements['prob_cedula_apellidos']>=70)) >= 2:
                elements['cedulaRepresentante_match']='si'
            elif file_name.split('-')[0]=='registroUnico':
              result_rut,log_ = class_rut.main_cedula_run(image)
              log+=log_+'\n'
              #extract info OCR
              elements['prob_rut_NIT']=np.round(100*compare_metric(re.sub(r'\W+', '', result_rut['NIT']),
                            response['data']['nit'].values[0]),1)
              elements['prob_rut_RS']=np.round(100*compare_metric(re.sub(r'\W+', '', result_rut['RS']),
                            response['data']['name'].values[0]),1)
              if elements['prob_rut_NIT'] >= 90 or elements['prob_rut_RS'] >= 80:
                elements['registroUnico_match']='si'
              elif np.mean(elements['prob_rut_NIT']+elements['prob_rut_RS'])>= 70:
                elements['registroUnico_match']='si'
            print(folder_path+folder+'/'+file_name)
          except:
            log += 'no se peude abrir archivo {}'.format(file_name)
        else:
          log += 'Error archivo {} no esta en lista de requeridos'.format(file_name)+'\n'
      elements['Log']=log
      df = df.append(elements, ignore_index = True)
  df.to_excel(config.save_excel_path,index=False)

if __name__ == '__main__':
  #run main
  main()