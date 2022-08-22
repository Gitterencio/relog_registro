from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta
import pyodbc
import re
#encriptar
from cryptocode import encrypt,decrypt
#pip install  cryptocode

class importador(models.Model):
    _name = 'reloj_registro.importador'
    _description = 'Importador de registro de reloj'

    name = fields.Char(string='Nombre de la conexion', required=True)
    host = fields.Char(string='Servidor de la BD', default='127.0.0.1',
                       required=True, help='Coloque el nombre o direccion del servidor')
    namedb = fields.Char(string='Nombre de la BD',
                         default='RELOJ', required=True)
    user = fields.Char(string='Usuario BD', default='SA', required=True)
    driver = fields.Char(
        string='Driver', default='ODBC Driver 17 for SQL Server', required=True)
    pwd = fields.Char(string='Contraseña BD', required=True)
    pr_Dia = fields.Datetime(string='Fecha de inicio',
                             required=True, default=fields.datetime.today())
    ul_Dia = fields.Datetime(string='Fecha final',
                             required=True, default=fields.datetime.today())
    conn_string = fields.Text('Conexion', compute='_get_conn_string')

    @api.onchange('pwd')
    def _onchange_pass_encrypt(self):
        if self.pwd:
            self.pwd = encrypt("{0}".format(self.pwd),"uwu")

    def _get_conn_string(self):
        pwd_d = decrypt("{0}".format(self.pwd),"uwu")
        self.conn_string = f"""
	        DRIVER={{{self.driver}}};
	        SERVER={self.host};
	        DATABASE={self.namedb};
	        Trust_Connection=yes;
	        UID={self.user};
	        PWD={pwd_d};"""

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
            if(u.identification_id):
                limpio = re.sub('[\.-]', '', u.identification_id)
                resultado = limpio[3:]
                if(resultado == code):
                    id = u.id
        return id

    def _crear_registro(self, id, en, sal):
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

    def importar_registros(self, fecha):
        db = self.namedb
        cnxn = pyodbc.connect(self.conn_string)
        entradas = pyodbc.connect(self.conn_string).cursor()
        salidas = pyodbc.connect(self.conn_string).cursor()
        employes = cnxn.cursor()
        employes.execute(""" SELECT [Userid]
                            	,[CardNum]
                            	,[Name] 
                            	FROM [{0}].[dbo].[Userinfo]; """.format(db))

        emp = employes.fetchone()
        while emp:
            id = self._get_employee_id(emp.CardNum)
            if id:
                entradas.execute("""SELECT [Logid]
                                     ,[CheckTime]
                                     ,[CheckType]
                             	     ,[Statusid]
                                     ,[StatusText]
                                FROM [{1}].[dbo].[Checkinout] c
                                INNER JOIN [{1}].[dbo].[Status] s ON s.Statusid = c.CheckType 
                                AND c.Userid = {0}
                                AND [CheckType] = 0
                                AND CONVERT(DATE,[CheckTime]) = '{2}'
                                ORDER BY CheckTime ASC""".format(emp.Userid, db, fecha))
                salidas.execute("""SELECT [Logid]
                                     ,[CheckTime]
                                     ,[CheckType]
                             	     ,[Statusid]
                                     ,[StatusText]
                                FROM [{1}].[dbo].[Checkinout] c
                                INNER JOIN [{1}].[dbo].[Status] s ON s.Statusid = c.CheckType 
                                AND c.Userid = {0}
                                AND [CheckType] = 1
                                 AND CONVERT(DATE,[CheckTime]) = '{2}' 
                                ORDER BY CheckTime ASC""".format(emp.Userid, db, fecha))
                ent = entradas.fetchone()
                sal = salidas.fetchone()

                while ent:
                    if ent and sal:
                        if ent.CheckTime < sal.CheckTime:

                            self._crear_registro(
                                id, (ent.CheckTime + timedelta(hours=6)), (sal.CheckTime + timedelta(hours=6)))

                            ent = entradas.fetchone()
                            sal = salidas.fetchone()
                        else:
                            sal = salidas.fetchone()
                    elif ent and not sal:
                        break

                emp = employes.fetchone()
            else:
                emp = employes.fetchone()

    def importar_registros_diario(self):
        fecha = (datetime.now() - timedelta(hours=6)).date()
        try:
            self.importar_registros(fecha)
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

    def importar_registros_rango(self):
        ini = (self.pr_Dia - timedelta(hours=6)).date()
        fin = (self.ul_Dia - timedelta(hours=6)).date()

        try:
            if ini == fin:
                self.importar_registros(ini)

            elif fin > ini:
                while (ini <= fin):
                    self.importar_registros(ini)
                    ini += timedelta(days=1)

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


""" 
BLOQUE DE CODIGO PARA ACCIONES AUTOMATICAS ODOO
conns= (env["reloj_registro.importador"].search([]))

for i in range(len(conns)):
  conns[i].importar_registros_diario()
  """


"""
REGLA SALARIAL PARA AUSENCIAS SIN PAGA
Condiciones
Condición basada en	Python Expression
Condición python	result = worked_days.ANPG

Cálculo
Tipo de importe	Python Code
Código Python	result = (worked_days.ANPG.number_of_days)*(BASIC/30)*-1
"""
