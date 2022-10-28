from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import re
#encriptar
from cryptocode import encrypt,decrypt
#pip install  cryptocode

#pip install mysql-connector-python
class importador_vici(models.Model):
    _name = 'reloj_registro.importador_vici'
    _description = 'Importador de registros vicidial'

    name = fields.Char(string='Nombre de la conexion', required=True)
    host = fields.Char(string='Servidor de la BD', default='10.0.90.1',
                       required=True, help='Coloque el nombre o direccion del servidor')
    namedb = fields.Char(string='Nombre de la BD',
                         default='asterisk', required=True)
    user = fields.Char(string='Usuario BD', default='SA', required=True)
    pwd = fields.Char(string='Contraseña BD', required=True)
    pr_Dia = fields.Datetime(string='Fecha de inicio',
                             required=True, default=fields.datetime.today())
    ul_Dia = fields.Datetime(string='Fecha final',
                             required=True, default=fields.datetime.today())


    @api.onchange('pwd')
    def _onchange_pass_encrypt(self):
        if self.pwd:
            self.pwd = encrypt("{0}".format(self.pwd),"uwu")
            
    def imprimir_hora(self):
        data = datetime.now()
        return{
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Fecha y Hora Interna',
                'message': 'Hora: {0} || Fecha: {1}  TZ-Estandar'.format(data.time(), data.date()),
                'sticky': True,
                'target': 'current',
                'type': 'warning',
            }}
    
    def _get_employee_id(self, code):
        id = 0
        users = (self.env["hr.employee"].search([]))
        for u in users:
            if(u.pin):
                
                if(u.pin == code):
                    id = u.id
        return id
    def _crear_registro(self, id, en, sal):

        #print(f'{id} - {en} {sal}')
        reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
               '<=', en), ('check_out', '=', False)], order='create_date desc', limit=1))

        if reg:
            if en.date() > reg.check_in.date():
                reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                       '<=', en), ('check_out', '>=', en)], order='create_date desc', limit=1))
                if not reg:
                    reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                       '<=', sal), ('check_out', '>=', sal)], order='create_date desc', limit=1))
                    if not reg:
                        reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                       '>=', en), ('check_out', '<=', sal)], order='create_date desc', limit=1))
                        if not reg:
                            reg = (self.env["hr.attendance"].search(
                                [('employee_id', '=', id), ('check_in', '=', en)]))
                            if not reg:
                                try:
                                    (self.env["hr.attendance"]).create(
                                        {"employee_id": id, "check_in": (en), "check_out": (sal)})
                                except Exception as e:
                                    print(e)

        else:
            reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                   '<=', en), ('check_out', '>=', en)], order='create_date desc', limit=1))
            if not reg:
                reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                   '<=', sal), ('check_out', '>=', sal)], order='create_date desc', limit=1))
                if not reg:
                    reg = (self.env["hr.attendance"].search([('employee_id', '=', id), ('check_in',
                   '>=', en), ('check_out', '<=', sal)], order='create_date desc', limit=1))
                    if not reg:
                        reg = (self.env["hr.attendance"].search(
                            [('employee_id', '=', id), ('check_in', '=', en)]))
                        if not reg:
                            try:
                                (self.env["hr.attendance"]).create(
                                    {"employee_id": id, "check_in": (en), "check_out": (sal)})
                            except Exception as e:
                                print(e)
    def importar_registros(self, fecha,emp,entradas,salidas):
                                       
                id = self._get_employee_id(emp[0])
 
                if id:
                     
                    entradas.execute("""SELECT event_date,event FROM vicidial_timeclock_log vtl
							WHERE user = {0}
							AND event = 'LOGIN'                              
							AND DATE(event_date)  =  '{1}'                             
							ORDER BY event_date ASC LIMIT 5 """.format(emp[0],fecha))

                    salidas.execute("""SELECT event_date,event FROM vicidial_timeclock_log vtl
							WHERE user = {0}
							AND event = 'LOGOUT'                              
							AND DATE(event_date)  =  '{1}'                             
							ORDER BY event_date ASC LIMIT 5 """.format(emp[0], fecha))
                    
                    sal = salidas.fetchone()
                    if not sal:
                            salidas.execute("""SELECT event_date,event FROM vicidial_timeclock_log vtl
							WHERE user = {0}
							AND event = 'AUTOLOGOUT'                              
							AND DATE(event_date)  =  '{1}'                             
							ORDER BY event_date ASC LIMIT 1 """.format(emp[0], fecha+timedelta(days=1)))
                            
                            sal = salidas.fetchone()

                    ent = entradas.fetchone()
                    
                    while ent:
                        if ent and sal:
                            if ent[0] < sal[0]:

                                self._crear_registro(id, (ent[0] + timedelta(hours=6)), (sal[0] + timedelta(hours=6)))

                                ent = entradas.fetchone()
                                sal = salidas.fetchone()
                            else:
                                sal = salidas.fetchone()
                        elif ent and not sal:
                            break


    def importar_registros_diario_vici(self):
        fecha = (datetime.now() - timedelta(hours=6)).date()
        fecha -= timedelta(days=1)
        pwd_d = decrypt("{0}".format(self.pwd),"uwu")
        li = 0
        lg = 10

        try:
            cnxn = mysql.connector.connect(host=self.host,
                                         database=self.namedb,
                                         user=self.user,
                                         password=pwd_d )
        
            if cnxn.is_connected():
                employes = cnxn.cursor(buffered=True)
                entradas = cnxn.cursor(buffered=True)
                salidas = cnxn.cursor(buffered=True)
                employes.execute(f"""SELECT  user,full_name FROM vicidial_users vu ORDER BY user ASC LIMIT {li},{lg} """)
                emp = employes.fetchone()

                while emp :
                   
                    while emp:
                        self.importar_registros(fecha,emp,entradas,salidas)

                        emp = employes.fetchone()
                    li+=lg
                    print("tanda siguiente")
                    employes.execute(f"""SELECT  user,full_name FROM vicidial_users vu ORDER BY user ASC LIMIT {li},{lg} """)
                    emp = employes.fetchone()

            return{
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Registros de Reloj',
                    'message': '¡Atención! Importacion de datos terminada para la fecha {0}'.format(fecha),
                    'sticky': True,
                    'target': 'current',
                    'type': 'success',
                }}
        except:
            return{
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Registros de Reloj',
                    'message': '''¡Atención! 
                    Error en la Conexión ''',
                    'sticky': True,
                    'target': 'current',
                    'type': 'danger',
                }}
        finally:
            if cnxn.is_connected():
                entradas.close()
                salidas.close() 
                employes.close()
                cnxn.close()
                print("close conexion")

    def importar_registros_rango(self):
        ini = (self.pr_Dia - timedelta(hours=6)).date()
        fin = (self.ul_Dia - timedelta(hours=6)).date()
        date_x = ini
        li = 0
        lg = 10
        pwd_d = decrypt("{0}".format(self.pwd),"uwu")
     
        try:
            cnxn = mysql.connector.connect(host=self.host,
                                         database=self.namedb,
                                         user=self.user,
                                         password=pwd_d )
        
            if cnxn.is_connected():
                employes = cnxn.cursor(buffered=True)
                entradas = cnxn.cursor(buffered=True)
                salidas = cnxn.cursor(buffered=True)
                employes.execute(f"""SELECT  user,full_name FROM vicidial_users vu ORDER BY user ASC LIMIT {li},{lg} """)
                emp = employes.fetchone()
                while emp :
                   
                    while emp:
                         
                        date_x = ini    
                        if date_x == fin:
                            self.importar_registros(date_x,emp,entradas,salidas)

                        elif fin > date_x:
                           while (date_x <= fin):
                               self.importar_registros(date_x,emp,entradas,salidas)
                               date_x += timedelta(days=1)

                        else:
                            return{
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': 'Registros de Reloj',
                                    'message': '¡Atención! Rango de dias invalido: {0} <-> {1}'.format(ini, fin),
                                    'sticky': True,
                                    'target': 'current',
                                    'type': 'warning',
                                }}
                        emp = employes.fetchone()
                    li+=lg
                    print("tanda siguiente")
                    employes.execute(f"""SELECT  user,full_name FROM vicidial_users vu ORDER BY user ASC LIMIT {li},{lg} """)
                    emp = employes.fetchone()
            return{
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Registros de Reloj',
                    'message': '''¡Atención! 
                    Importacion de datos terminada ''',
                    'sticky': True,
                    'target': 'current',
                    'type': 'success',
                }}

        except:
            return{
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Registros de Reloj',
                    'message': '''¡Atención! 
                    Error en la Conexión ''',
                    'sticky': True,
                    'target': 'current',
                    'type': 'danger',
                }}
        finally:
            if cnxn.is_connected():
                entradas.close()
                salidas.close() 
                employes.close()
                cnxn.close()
                print("close conexion")
""" 
BLOQUE DE CODIGO PARA ACCIONES AUTOMATICAS ODOO
conns= (env["reloj_registro.importador_vici"].search([]))

for i in range(len(conns)):
  conns[i].importar_registros_diario_vici()
  """