# OC connection and data query module



#***************BODY BEGIN*****************************************************************************
import cx_Oracle
from db_row_new import *
import time


class db_get:
    def __init__(self,oc_user,oc_passwd, oc_host):
        self.connect=cx_Oracle.connect('%s/%s@%s'% (oc_user,oc_passwd, oc_host))
        ##self.connect = odbc.odbc('%s/%s/%s' % (host,user,passwd))
        self.cursor=self.connect.cursor()
    def query(self,sql):
        self.cursor.execute(sql)
        #self.start_time=time.time()
        self.results=self.cursor.fetchall()
        self.fields=self.cursor.description
        self.stop_time=time.time()
        #self.connect.close()
        R=IMetaRow(self.fields)
        self.data=[R(row) for row in self.results]
        #self.delta_time=self.stop_time-self.start_time
        return self.data, self.fields
    def query_lob(self,sql,num=50):
        self.cursor.execute(sql)
        #self.start_time=time.time()
        self.results=self.cursor.fetchmany(num)
        self.fields=self.cursor.description
        self.stop_time=time.time()
        #self.connect.close()
        R=IMetaRow(self.fields)
        self.data=[R(row) for row in self.results]
        #self.delta_time=self.stop_time-self.start_time
        return self.data, self.fields
    def close(self):
        self.cursor.close
        self.connect.close()
class db_get_lob(db_get):
    def query(self,sql,num=50):
        self.cursor.execute(sql)
        #self.start_time=time.time()
        self.results=self.cursor.fetchmany(num)
        self.fields=self.cursor.description
        self.stop_time=time.time()
        #self.connect.close()
        R=IMetaRow(self.fields)
        self.data=[R(row) for row in self.results]
        #self.delta_time=self.stop_time-self.start_time
        return self.data, self.fields

class data_store:
    def __init__(self,data, fields):
        self.data=data
        self.fields=fields
    def out_put(self, file_name):
        '''write data to txt file, sep \t'''
        _file=open(file_name,'w')
        #output header
        for item in self.fields:
            _file.writelines('%s' % item[0])
            _file.writelines('\t')
        _file.writelines('\n')
        #output data
        for item in self.data:
            for data in item:
                _file.writelines('%s' % data)
                _file.writelines('\t')
            _file.writelines('\n')
        _file.close()
    def output_html(self,file_name):
        '''output file to html format'''
        _file=open(file_name,'w')
        header=''
        content=''
        for item in self.fields:
            header=header+'<TH>'+item[0]+'</TH>'
        for item in self.data:
            content=content+'<TR>'
            for data in item:
                if data<>None:
                    content=content+'<TD>'+str(data)+'</TD>'
                else:
                    content=content+'<TD>'+''+'</TD>'
            content=content+'</TD>'
        table='<TABLE class="sortable">'+header+content+'</TABLE>'
        _file.write(table)
        _file.close()

