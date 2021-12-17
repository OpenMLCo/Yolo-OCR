#data files yolo cedula
config_file_id= 'Yolov4_ID/yolov4_custom.cfg'
data_file_id = 'Yolov4_ID/obj.data' 
weights_id='Yolov4_ID/yolov4_custom_best.weights'

#data files yolo rut
config_file_rut='Yolov4_RUT/yolov4_custom.cfg'
data_file_rut = 'Yolov4_RUT/obj.data' 
weights_rut='Yolov4_RUT/yolov4_custom_best.weights'

# Authentication data for BD pruebas
ip_server = '190.7.134.180'
username_bd = 'julian_c'
password_bd = 'Julian_c_unal_2021'
database = 'pruebas_adr'

#require files and columns log
filer_required=['cedulaRepresentante','registroUnico','certificadoExistencia']
columns=['folde_ID','cedulaRepresentante','registroUnico',
        'certificadoExistencia','Log','ID','cedulaRepresentante_match',
        'registroUnico_match','prob_cedula_nombres','prob_cedula_apellidos',
        'prob_cedula_numero','prob_rut_RS','prob_rut_NIT']

#folder path
folder_path='files2/files/'
