#!/usr/bin/python
# -*- coding:utf-8 -*-
#-------------------------------------------
# Designer  : Lu Jia
# E-mail    : lujiacn@Gmail.com
#-------------------------------------------
from getpass import getpass
from oc_lib import db_get_lob, db_get
import sys
import os
from xml.dom.minidom import parse, parseString


def f_dcibook_list(study, book_name, con):
    sql="""
        SELECT   dbp.dci_id, dbp.display_sn
                FROM dci_book_pages dbp,
                 clinical_studies cs,
                 dci_books db
                WHERE cs.study = '%s'
                AND dbp.clinical_study_id = cs.clinical_study_id
                AND db.dci_book_id = dbp.dci_book_id
                and db.NAME = '%s'
             ORDER BY dbp.DISPLAY_SN

    """ % (study, book_name)
    dci_list, fields=con.query(sql)
    return dci_list

#def f_dci_xml_download(study, con):
#  """Download last dci form versions, save to output folder"""
#  sql = """select a.dci_id, a.fl_xml, a.version_sn from dci_form_versions a,
#(select distinct max(df.version_sn) over(partition by df.dci_id) as last_version, df.dci_id
#from dci_form_versions df, clinical_studies cs
#where cs.study = '%s'
#AND df.clinical_study_id = cs.clinical_study_id) t
#where a.dci_id = t.dci_id
#and a.version_sn = t.last_version
#      """ % (study)
#  form_data, form_fields = con.query_lob(sql, 200)
#  for i in range(len(form_data)):
#    dci_id = form_data[i]['dci_id']
#    xml_data = form_data[i]['fl_xml'].read()
#    file_name = 'output/%s_%s.xml' % (study, dci_id)
#    file = open(file_name, 'w')
#    file.write(xml_data)
#    file.close()

def f_dci_xml(study, dci_id, con):
    '''fields: dci xml obj'''
    file_name = 'output/%s_%s.xml' % (study, dci_id)
    try:
      file = open(file_name, 'r')
      output = file.read()
      file.close()
      return output
    except:
      sql='''
        SELECT fl_xml
        FROM dci_form_versions dfv
        where dci_id = %s
        order by dfv.version_sn desc
      ''' % (dci_id)
      form_data,form_fields=con.query_lob(sql,50)
      output = form_data[0]['fl_xml'].read()
      file = open(file_name,'w')
      file.write(output)
      file.close()
      return output


def f_q_dict(study, con):
    """return dict with question id and quetion name"""
    output_dict={}
    sql='''SELECT DISTINCT dq.dcm_question_group_id qg_id, dq.DCM_QUESTION_ID q_id, question_name name
                   FROM dcm_questions dq, clinical_studies cs
                  WHERE cs.study='%s'
            and dq.clinical_study_id=cs.clinical_study_id
    ''' % study

    r_data, r_field=con.query(sql)

    for i in range(len(r_data)):
        the_key='_'.join([str(r_data[i]['qg_id']),str(r_data[i]['q_id'])])
        output_dict[the_key]=r_data[i]['name']
    return output_dict
def f_dcm_dict(study, con):
    '''Function to get DCM, subset id, return dict, used for DCM information in annoatated DCI'''
    output_dict={}
    sql="""
        SELECT DISTINCT dcms.dcm_id || '_' || dcms.dcm_subset_sn NAME,
                           'DCM: '||dcms.NAME
                        || '('
                        || dcms.dcm_subset_sn
                        || ')'
                        || ', '
                        || dcms.subset_name
            ||'; View(s): '
            ||decode(qgn.short_name, null, null, dcms.short_name)
            ||decode(qg.short_name, null, null,', ')
            ||decode(qg.short_name, null, null, dcms.short_name||qg.short_name)   VALUE
                   FROM dcms,
                        clinical_studies cs,
                        (SELECT qgr.dcm_id, qgr.short_name
                           FROM dcm_question_groups qgr, clinical_studies cs
                          WHERE cs.study = '%s'
                            AND qgr.clinical_study_id = cs.clinical_study_id
                            AND qgr.repeating_flag = 'Y') qg,
                        (SELECT qgr.dcm_id, qgr.short_name
                           FROM dcm_question_groups qgr, clinical_studies cs
                          WHERE cs.study = '%s'
                            AND qgr.clinical_study_id = cs.clinical_study_id
                            AND qgr.repeating_flag = 'N') qgn
                  WHERE cs.study = '%s'
                    AND dcms.clinical_study_id = cs.clinical_study_id
                    AND dcms.dcm_id = qg.dcm_id(+)
              AND DCMS.DCM_ID=QGN.DCM_ID(+)

    """ % (study, study, study)
    r_data, r_field=con.query(sql)

    for i in range(len(r_data)):
        the_key=r_data[i]['NAME']
        output_dict[the_key]=r_data[i]['VALUE']
    return output_dict

def f_xml_ann(dom_obj,que_dict, dcm_dict):
    """return  que_name dict, for annotation attributes"""
    def f_dcm(dcm_form_list, page_seq):
        form_list=dcm_form_list
        temp_data=[]
        for i in range(len(form_list)):
            ## question IDs
            try:
                qg_id=form_list[i].getElementsByTagName('DCMQuestionAttributes')[0].attributes['DCM_Question_Group_ID'].value
                q_id=form_list[i].getElementsByTagName('DCMQuestionAttributes')[0].attributes['DCM_Question_ID'].value
                q_sn=form_list[i].getElementsByTagName('DCMQuestionAttributes')[0].attributes['Repeat_SN'].value

                form_id=form_list[i].attributes['FieldName'].value

                que_key='_'.join([qg_id, q_id])

                que_name=que_dict[que_key]+'.'+str(q_sn)
            except:
                print form_list[i].attributes.keys()
                que_name='Error'
                form_id='Error_id'

            ## form location
            #lrx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightX'].value)
            lry=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightY'].value)+off_set
            ulx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftX'].value)+off_set_x
            lrx=ulx+width
            #uly=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftY'].value)
            uly=lry+high
            # ulx, uly,lrx,lry

            rect=",".join([str(ulx),str(lry),str(lrx),str(uly)])
            page_num=start_page
            temp_dict={}
            temp_dict['name']=str(page_num)+'_'+form_id
            temp_dict['page_num']=page_num
            temp_dict['rect']=rect
            temp_dict['que_name']=que_name
            temp_data.append(temp_dict)
        return temp_data
    def f_header(dci_form_list, page_seq):
        form_list=dci_form_list
        temp_data=[]
        for i in range(len(form_list)):
            ##que_name
            try:
                que_name=form_list[i].attributes['FieldName'].value
            except:
                print 'In f_header function'
                print form_list[i].attributes.keys()
                que_name='blank'

            ## form location
            #lrx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightX'].value)
            lry=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightY'].value)+off_set
            ulx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftX'].value)+off_set_x
            lrx=ulx+width
            #uly=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftY'].value)
            uly=lry+high
            # ulx, uly,lrx,lry

            rect=",".join([str(ulx),str(lry),str(lrx),str(uly)])
            page_num=start_page
            temp_dict={}
            temp_dict['name']=str(page_num)+'_'+que_name
            temp_dict['page_num']=page_num
            temp_dict['rect']=rect
            temp_dict['que_name']=que_name
            temp_data.append(temp_dict)
        return temp_data
    def f_dcm_info(dcm_block, dcm_dict):
        form_list=dcm_block
        temp_data=[]
        width=150
        for i in range(len(form_list)):

            ##que_name
            try:
                dcm_id=form_list[i].attributes['DCM_ID'].value
                dcm_subset_sn=form_list[i].attributes['DCM_Subset_SN'].value

                dict_key=str(dcm_id)+'_'+str(dcm_subset_sn)
                #print dict_key
                que_name=dcm_dict[dict_key]
            except:
                #print form_list[i].attributes.keys()
                que_name='blank'

            ## form location
            #lrx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightX'].value)
            #lry=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['LowerRightY'].value)+off_set
            lry=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftY'].value)+off_set
            ulx=float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftX'].value)+off_set_x
            lrx=ulx+width
            #uly=max_y-float(form_list[i].getElementsByTagName('Geometry')[0].attributes['UpperLeftY'].value)
            uly=lry+high
            # ulx, uly,lrx,lry

            rect=",".join([str(ulx),str(lry),str(lrx),str(uly)])
            page_num=start_page
            temp_dict={}
            temp_dict['name']=str(page_num)+'_'.join([str(dcm_id), str(dcm_subset_sn)])
            temp_dict['page_num']=page_num
            temp_dict['rect']=rect
            temp_dict['que_name']=que_name
            temp_data.append(temp_dict)
        return temp_data

    ###########  main begin ############
    global start_page
    ## define High, with
    high=18
    width=60
    off_set=30
    off_set_x=60
    output_data=[]
    blocks=dom_obj.getElementsByTagName('Page')
    for j in range(len(blocks)):
        page_seq=blocks[j].attributes['PageSequence'].value

        #define max_y
        max_y=540*int(page_seq)
        #dcm
        dcm_block=blocks[j].getElementsByTagName('DCMBlocks')
        dcm_form_list=dcm_block[0].getElementsByTagName('FormField')

        #header
        header_block=blocks[j].getElementsByTagName('HeaderBlock')
        header_form_list=header_block[0].getElementsByTagName('FormField')

        #dcm_name and subset
        dcm_info_list=blocks[j].getElementsByTagName('DCMBlock')
        print 'dcm_infor_len:',len(dcm_info_list)

        output_data=output_data+f_dcm(dcm_form_list, page_seq)\
                +f_header(header_form_list, page_seq)\
                +f_dcm_info(dcm_info_list,dcm_dict)

        # get current start page
        start_page=start_page+1
    return output_data

def f_xml_content(xml_ann_dict):
    ques_name_dict=xml_ann_dict
    """function generate xml comment content  """

    #### % name, page, rect, que_name
    xml_content="""
                <freetext width="2" color="#AABFFF" opacity="0.955002" flags="print"  date="" name="%s" page="%s" rect="%s" subject="text" title="BJ_DBD">
                  <contents-richtext>
                    <body xmlns="http://www.w3.org/1999/xhtml" xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:APIVersion="Acrobat:9.1.0" xfa:spec="2.0.2" style="font-size:8.0pt;text-align:left;color:#FF0000;font-weight:normal;font-style:normal;font-family:Helvetica,sans-serif;font-stretch:normal"><p><span>%s</span></p></body>
                  </contents-richtext>
                  <defaultappearance>0.6667 0.75 1 rg /Helv 8 Tf</defaultappearance>
                  <defaultstyle>font: Helvetica,sans-serif 8.0pt; text-align:left; color:#FF0000 </defaultstyle>
                </freetext>
            """""
    temp_text=''
    for i in range(len(ques_name_dict)):
        name=ques_name_dict[i]['name']
        page=ques_name_dict[i]['page_num']
        rect=ques_name_dict[i]['rect']
        que_name=ques_name_dict[i]['que_name']
        temp_text=temp_text+xml_content % (name, page, rect, que_name)
    temp_text=temp_text
    return temp_text

def main(study, book_name, con):
    dci_list=f_dcibook_list(study, book_name, con)
    que_dict=f_q_dict(study,con)
    dcm_dict=f_dcm_dict(study,con)
    #f_dci_xml_download(study, con)
    xml_output=''
    ###### template for header and footer
    xml_header="""<?xml version="1.0" encoding="UTF-8"?>
            <xfdf xmlns="http://ns.adobe.com/xfdf/" xml:space="preserve">
          <annots>"""
    xml_footer="""</annots>
          <f href=""/>
          <ids original="10D8FE50B699A705396B1C69D62257D7" modified="C70D099293EE1848B20D7D8F0D2425C7"/>
        </xfdf>"""

    for i in range(len(dci_list)):
      dci_id=dci_list[i]['DCI_ID']
      dci_pn=dci_list[i]['display_sn']
      print "DCI_ID: ", dci_id, "| page_number: ", dci_pn
      print "----------------------------------------------"
      dci_xml=f_dci_xml(study, dci_id, con)
      #dci_xml=dci_xml.replace("<<"," ")
      #dci_xml=dci_xml.replace(">>"," ")
      try:
        dom_obj=parseString(dci_xml)
        xml_dict=f_xml_ann(dom_obj, que_dict, dcm_dict)
        xml_ann=f_xml_content(xml_dict)
        xml_output=xml_output+xml_ann
      except Exception, e:
        print "Errror: %s" % e
        print """xml parse error for this page, may be due to special charactors in layout or other unknown reason. Please check saved xml file in the save folder."""
        #xml_file = open("%s_%s.xml" % (study, dci_id),'w')
        #xml_file.write(dci_xml)
        #xml.close()

    xml_output=xml_header+xml_output+xml_footer

    file=open('%s_%s.xfdf' % (study, book_name),'w')
    file.write(xml_output)
    file.close()


start_page=0

if __name__ == '__main__':
    oc_host='ocprod'
    print "Please input OC account: "
    oc_user=raw_input()
    print "Please input OC password: "
    oc_passwd=getpass()
    print "Please input study name: "
    study=raw_input()
    print "Please input DCI book name: "
    book_name=raw_input()
    con=db_get(oc_user,oc_passwd,oc_host)
    main(study, book_name, con)



