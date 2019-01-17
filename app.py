from flask import Flask, render_template, request, redirect, abort, json, send_file,url_for, jsonify
import json
import psycopg2
import sys
import csv
import xlwt
from pandas import DataFrame
import random
import re
import secret
# import flask.ext.whooshalchemy

app = Flask(__name__, static_folder='static')

# #database information
# db_name = 'postgres'
# user_nanime = 'postgres'
# host = '141.211.55.211'
# port = '58419'
# sslcert="postgresql.crt"
# sslkey="postgresql.key"
# sslrootcert="root.crt"
# sslmode="verify-ca"



#for all the files that need to be populated in the HTML pages
# QUERY_VARIABLES_FILE = "query_variables.json"
# query_variables = []
VARIABLE_DESCRIPTION_FILE = "variable_description.json"
variable_description = {}
DATASET_LIST_FILE = "dataset_list.json"
dataset_list = {}

# def init():
#     # global query_variables
#     global variable_description
#     global dataset_list
#
#     try:
#         # f = open(QUERY_VARIABLES_FILE)
#         # query_variables = json.loads(f.read())
#         # f.close()
#         f = open(VARIABLE_DESCRIPTION_FILE)
#         variable_description = json.loads(f.read())
#         f.close()
#         f = open(DATASET_LIST_FILE)
#         dataset_list = json.loads(f.read())
#         f.close()
#     except:
#         # query_variables = []
#         variable_description = {}
#         dataset_list = {}


#
# def get_query_variables():
#     global query_variables
#     return query_variables
#
# def get_variable_description():
#     global variable_description
#     return variable_description
#
# def get_dataset_list():
#     global dataset_list
#     return dataset_list



#routing goes here
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/exhibits")
def sec_exhibits():
    statement = '''SELECT datefiled FROM exhibits ORDER BY datefiled DESC LIMIT 1'''
    try:
        conn = psycopg2.connect(database=secret.db_name, user=secret.user_name, host=secret.host, port=secret.port, sslcert=secret.sslcert, sslkey=secret.sslkey, sslrootcert=secret.sslrootcert, sslmode=secret.sslmode)
        cur = conn.cursor()
    except Error as e:
        print(e)

    cur.execute(statement)
    conn.commit()
    # for row in cur:
    #     date_latest = row[0]
    date_latest = 'test'

    f = open(VARIABLE_DESCRIPTION_FILE)
    variable_description = json.loads(f.read())
    f.close()
    f = open(DATASET_LIST_FILE)
    dataset_list = json.loads(f.read())
    f.close()

    output_number = random.randint(1,10000000001)
    variable_description_list = variable_description['filings_exibits_variable_description']
    variable_list = dataset_list['filing_exhibits_dataset_list']
    return render_template("exhibits.html", output_number = output_number, variable_description_list=variable_description_list, variable_list = variable_list, date_latest = date_latest)




##################################################
@app.route("/exhibitsoutput", methods=["POST"])
def exhibitsoutput():
    output_number = request.args.get('output_number', None)

    date_variable = request.form.get('date_variable')
    if date_variable == 'filingdate':
        date_model = 'datefiled'
        open_line = 'SELECT DateFiled, formtype '
    elif date_variable == 'reportdate':
        date_model = 'reportperiod'
        open_line = 'SELECT reportperiod, formtype '

    form_type = request.form.getlist('form_type')
    form_type_str = ""
    for ele in form_type:
        form_type_str += ele+", "
    form_type_str_final = "("+form_type_str[:-2]+') '
    #
    startdate = request.form['startdate']
    startdate_split = startdate.split('/')
    startdate_formatted = startdate_split[-1]+'-'+startdate_split[0]+'-'+startdate_split[1]
    enddate = request.form['enddate']
    enddate_split = enddate.split('/')
    enddate_formatted = enddate_split[-1]+'-'+enddate_split[0]+'-'+enddate_split[1]
    date_all = startdate+" - "+enddate
    #
    outputformat = request.form['outputformat']
    #
    companycodeformat = request.form['CompanyCode']
    providecompanycode = request.form['providecompanycode']
    # the value of providecompanycode is decide if the user directly put in the company code, or upload a file, or select the entire database
    CompanyCodeUserPutin = request.form['company_code_user_putin']
    selected = request.form['selected_variable']
    selected_x = selected.split(',')
    variable_dict_check = {'Filing Date':'datefiled', 'Conformed Period of Report or Fiscal Period End':'reportperiod', 'SEC Form':'formtype', 'Company Name':'companyname', 'Reference Name of Complete Report Filing':'filename', 'Complete Report File Size':'filesize', 'SEC Acceptance Date':'secaccdate', 'SEC Acceptance Time':'secacctime', 'Exhibit Sequence Number':'exhibitseq', 'Exhibit Type':'exhibittype', 'Exhibit Description':'exhibitdesc', 'Exhibit Reference Filename':'exhibitfilename'}
    variable_list_str = ""
    for ele in selected_x:
        if ele == 'Filing Date':
            if date_variable == 'filingdate':
                pass
            elif date_variable == 'reportdate':
                variable = variable_dict_check[ele]
                variable_list_str += variable + ','
        elif ele == 'Conformed Period of Report or Fiscal Period End':
            if date_variable == 'filingdate':
                variable = variable_dict_check[ele]
                variable_list_str += variable + ','
            elif date_variable == 'reportdate':
                pass
        elif ele=="SEC Form":
            pass
        else:
            variable = variable_dict_check[ele]
            variable_list_str += variable + ','
    if len(variable_list_str)>0:
        variable_list_str_final = ", "+variable_list_str[:-1] + ' '
    else:
        variable_list_str_final = ''
    #
    if providecompanycode == 'EnterInCompanyCode':
        # this means user directly put in company code
        company_code_list = CompanyCodeUserPutin.split()
        company_code = "( "
        for ele in company_code_list:
            company_code += ele + ", "
        company_code_final = company_code[:-2]+')'
        condition_company_code = 'WHERE ' + companycodeformat + ' in ' + company_code_final
        form_code = ' AND formtype in '+form_type_str_final
    elif providecompanycode == 'SelectEntireDatabase':
        # select entire database
        company_code = '*'
        condition_company_code = ''
        form_code = 'WHERE formtype in '+form_type_str_final

    #
    # open_line = 'SELECT '
    # variables = '* '
    database_name = 'FROM exhibits '
    # condition_company_code = 'WHERE ' + companycodeformat + ' in ' + company_code_final
    # company_code # this is the string contains all the company code, '1234546, 2334543, 244546'
    #具体company code值还没有写呢 要从textbox里面抓 或者读上传的文件里面抓
    condition_date_begin2 = ' AND '+date_model+' BETWEEN \''+ startdate_formatted
    condition_date_end2 = '\' AND \'' + enddate_formatted + '\''
    statement = open_line+variable_list_str_final+database_name+condition_company_code+ form_code +condition_date_begin2+condition_date_end2
    # +variabletestr
    #
    # # SELECT serverlocation
    # #Download from serverlocation
    #
    #
    # # try:
    # #     conn = psycopg2.connect(database=db_name, user=user_name, host=host, port=port, sslcert=sslcert, sslkey=sslkey, sslrootcert=sslrootcert, sslmode=sslmode)
    # #     cur = conn.cursor()
    # # except Error as e:
    # #     print(e)
    # # # #
    # # cur.execute(statement)
    # # conn.commit()
    # #
    # # if outputformat == 'csv':
    # #     output_file_name = "output_"+str(output_number)+".csv"
    # #     output_file_path = "output_file/"
    # #
    # #     with open(output_file_path+output_file_name, 'w') as f:
    # #         f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # #         for row in cur:
    # #             f.writerow(row[1:])
    # # elif outputformat == 'text':
    # #     output_file_name = 'output_'+str(output_number)+'.txt'
    # #     output_file_path = "output_file/"
    # #     with open(output_file_path+output_file_name, 'w') as f:
    # #     # with open('output.txt', 'w') as f:
    # #         for row in cur:
    # #             f.write(str(row[1:]))

    return render_template("output.html", variable_list=statement, output_file_name = output_file_name,output_number=output_number,date_all=date_all, outputformat=outputformat,selected=selected)
    # return render_template("query_test.html", variable_list=statement)
##################################################



# start with eightk
# first, add the trigger part. need another javascript part to calculate the selection
# second
# there must be some sum function to do the computation
# trigger info need to be changed

@app.route("/eightkoutput", methods=["POST"])
def eightkoutput():
    output_number = request.args.get('output_number', None)

    # date_variable = request.form['date_variable']
    date_variable = request.form.get('date_variable')
    if date_variable == 'filingdate':
        date_model = 'datefiled'
        open_line = 'SELECT ItemSeqNo, DateFiled '
    elif date_variable == 'reportdate':
        date_model = 'reportperiod'
        open_line = 'SELECT ItemSeqNo, reportperiod '

    startdate = request.form['startdate']
    startdate_split = startdate.split('/')
    startdate_formatted = startdate_split[-1]+'-'+startdate_split[0]+'-'+startdate_split[1]
    enddate = request.form['enddate']
    enddate_split = enddate.split('/')
    enddate_formatted = enddate_split[-1]+'-'+enddate_split[0]+'-'+enddate_split[1]
    date_all = startdate+" - "+enddate

    outputformat = request.form['outputformat']

    companycodeformat = request.form['CompanyCode']
    providecompanycode = request.form['providecompanycode']
    # the value of providecompanycode is decide if the user directly put in the company code, or upload a file, or select the entire database
    CompanyCodeUserPutin = request.form['company_code_user_putin']
    selected = request.form['selected_variable']
    selected_x = selected.split(',')
    variable_dict_check = {'SEC Central Index Key':'cik', 'Filing Date':'datefiled', 'Conformed Period of Report or Fiscal Period End':'reportperiod', 'SEC Form':'formtype', 'Company Name':'companyname', 'Reference Name of Complete Report Filing':'filename', 'Complete Report File Size':'filesize', 'SEC Acceptance Time':'secacctime', 'Form 8-K Item Number':'itemseqno', 'Form 8-K Item Description':'item'}
    variable_list_str = ""
    # need to check  'Number of 8-K Items' first, if so, add COUNT
    for ele in selected_x:
        if ele == 'Filing Date':
            if date_variable == 'filingdate':
                pass
            elif date_variable == 'reportdate':
                variable = variable_dict_check[ele]
                variable_list_str += variable + ','
        elif ele == 'Conformed Period of Report or Fiscal Period End':
            if date_variable == 'filingdate':
                variable = variable_dict_check[ele]
                variable_list_str += variable + ','
            elif date_variable == 'reportdate':
                pass
        elif ele=="Form 8-K Item Number":
            pass
        else:
            variable = variable_dict_check[ele]
            variable_list_str += variable + ','
    if len(variable_list_str)>0:
        variable_list_str_final = ", "+variable_list_str[:-1] + ' '
    else:
        variable_list_str_final = ' '

    selected_trigger = request.form['selected_trigger_event']
    selected_trigger_x = selected_trigger.split(',')
    selected_trigger_final = []
    for ele in selected_trigger_x:
        cleaned = re.search(r'Section \d', ele)
        selected_trigger_final.append(cleaned[0])

    section_dict_check = {'Section 1':"'1.01', '1.02', '1.03'", 'Section 2':"'2.01','2.02','2.03','2.04','2.05','2.06'", 'Section 3':"'3.01','3.02','3.03'", 'Section 4':"'4.01','4.02'", 'Section 5':"'5.01','5.02','5.03','5.04','5.05','5.06','5.07'", 'Section 6':"'6.01','6.02','6.03','6.04','6.05'", 'Section 7':"'7.01'", 'Section 8':"'8.01'", 'Section 9':"'9.01'"}
    trigger_str = ""
    for ele in selected_trigger_final:
        ele_split = ele.split(' - ')
        section_value = ele_split[0]
        section_selected = section_dict_check[section_value]
        trigger_str += section_selected + ','
    trigger_str_final = "("+trigger_str[:-1] + ') '

    if providecompanycode == 'EnterInCompanyCode':
        # this means user directly put in company code
        company_code_list = CompanyCodeUserPutin.split()
        company_code = "( "
        for ele in company_code_list:
            company_code += ele + ", "
        company_code_final = company_code[:-2]+')'
        condition_company_code = 'WHERE ' + companycodeformat + ' in ' + company_code_final
    elif providecompanycode == 'SelectEntireDatabase':
        # select entire database
        company_code = '*'
        condition_company_code = ''
    #

    # this one has been moved to top
    # open_line = 'SELECT ItemSeqNo, DateFiled'


    # if count_operation == 1:
    #     open_line = 'SELECT COUNT(ItemSeqNo), ItemSeqNo, '
        # here may need 'GROUP BY cik '
        # 这里还要再看一下逻辑，count哪一个，以及groupby哪一个。因为在count & groupby里面的东西是必须要select上的
        # 所以 如果这些是默认 怎么和用户选择的去重
        # ItemSeqNo count可行，因为trigger也必须选，但要去重
    # elif count_operation ==0:
    #     open_line = 'SELECT '
    # variables = '* '
    #


    # 这部分可以合并上去的 这个if判断
    database_name = 'FROM eightkitems '
    if providecompanycode == 'EnterInCompanyCode':
        condition_company_code = 'WHERE ' + companycodeformat + ' in ' + company_code_final
        trigger_code = ' AND ItemSeqNo in '+trigger_str_final
    elif providecompanycode == 'SelectEntireDatabase':
        condition_company_code = ''
        trigger_code = 'WHERE ItemSeqNo in '+trigger_str_final




    # company_code # this is the string contains all the company code, '1234546, 2334543, 244546'
    #具体company code值还没有写呢 要从textbox里面抓 或者读上传的文件里面抓

    # 放到上面和condition_compnay_code一起了
    # trigger_code = 'AND ItemSeqNo in '+trigger_str_final

    # condition_date_begin = ' AND secaccdate BETWEEN \'' + startdate_formatted
    # condition_date_end = '\' AND \'' + enddate_formatted + '\''

    condition_date_begin2 = ' AND '+date_model+' BETWEEN \''+ startdate_formatted
    condition_date_end2 = '\' AND \'' + enddate_formatted + '\''

    statement = open_line+variable_list_str_final+database_name+condition_company_code+ trigger_code +condition_date_begin2+condition_date_end2
    # statement = open_line+variable_list_str_final+database_name+condition_company_code+condition_date_begin2+condition_date_end2

    # +variabletestr

    # SELECT serverlocation
    #Download from serverlocation

    #
    # try:
    #     conn = psycopg2.connect(database=db_name, user=user_name, host=host, port=port, sslcert=sslcert, sslkey=sslkey, sslrootcert=sslrootcert, sslmode=sslmode)
    #     cur = conn.cursor()
    # except Error as e:
    #     print(e)
    # # #
    # cur.execute(statement)
    # conn.commit()
    #
    # if outputformat == 'csv':
    #     output_file_name = "output_"+str(output_number)+".csv"
    #     output_file_path = "output_file/"
    #
    #     with open(output_file_path+output_file_name, 'w') as f:
    #         f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #         for row in cur:
    #             f.writerow(row[1:])
    # elif outputformat == 'text':
    #     output_file_name = 'output_'+str(output_number)+'.txt'
    #     output_file_path = "output_file/"
    #     with open(output_file_path+output_file_name, 'w') as f:
    #     # with open('output.txt', 'w') as f:
    #         for row in cur:
    #             f.write(str(row[1:]))

    return render_template("output.html", variable_list=statement, output_file_name = output_file_name,output_number=output_number,date_all=date_all, outputformat=outputformat,selected=selected)
    # return render_template("query_test.html", variable_list=statement)


@app.route("/eightkitem")
def sec_eightkitem():
    statement = '''SELECT datefiled FROM eightkitems ORDER BY datefiled DESC LIMIT 1'''
    try:
        conn = psycopg2.connect(database=secret.db_name, user=secret.user_name, host=secret.host, port=secret.port, sslcert=secret.sslcert, sslkey=secret.sslkey, sslrootcert=secret.sslrootcert, sslmode=secret.sslmode)
        cur = conn.cursor()
    except Error as e:
        print(e)
    # #
    cur.execute(statement)
    conn.commit()
    # for row in cur:
        # date_latest = row[0]
    date_latest = 'test'

    f = open(VARIABLE_DESCRIPTION_FILE)
    variable_description = json.loads(f.read())
    f.close()
    f = open(DATASET_LIST_FILE)
    dataset_list = json.loads(f.read())
    f.close()

    output_number = random.randint(1,10000000001)
    variable_description_list = variable_description['eightk_items_variable_description']
    variable_list = dataset_list['eightk_items_dataset_list']
    return render_template("eightkitem.html", output_number = output_number, variable_description_list=variable_description_list, variable_list = variable_list, date_latest = date_latest)

@app.route("/secfiling")
def sec_filing():
    statement = '''SELECT datefiled FROM forms ORDER BY datefiled DESC LIMIT 1'''
    try:
        conn = psycopg2.connect(database=secret.db_name, user=secret.user_name, host=secret.host, port=secret.port, sslcert=secret.sslcert, sslkey=secret.sslkey, sslrootcert=secret.sslrootcert, sslmode=secret.sslmode)
        cur = conn.cursor()
    except Error as e:
        print(e)
    # #
    cur.execute(statement)
    conn.commit()
    for row in cur:
        date_latest = row[0]
    # date_latest = 'test'

    f = open(VARIABLE_DESCRIPTION_FILE)
    variable_description = json.loads(f.read())
    f.close()
    f = open(DATASET_LIST_FILE)
    dataset_list = json.loads(f.read())
    f.close()

    output_number = random.randint(1,10000000001)
    # with open('variable_description_list.json') as f:
    #     f_raw = json.loads(f.read())
    #     variable_description_list = f_raw["all"]
    # with open('variable_list.json') as f:
    #     f_raw = json.loads(f.read())
    #     variable_list = f_raw["all"]
    variable_description_list = variable_description['filings_index_variable_description']
    variable_list = dataset_list['filing_index_dataset_list']
    return render_template("secfiling.html", output_number = output_number, variable_description_list=variable_description_list, variable_list = variable_list, date_latest = date_latest)
#
@app.route("/output", methods=["POST"])
def output():
    output_number = request.args.get('output_number', None)

    startdate = request.form['startdate']
    startdate_split = startdate.split('/')
    startdate_formatted = startdate_split[-1]+'-'+startdate_split[0]+'-'+startdate_split[1]
    enddate = request.form['enddate']
    enddate_split = enddate.split('/')
    enddate_formatted = enddate_split[-1]+'-'+enddate_split[0]+'-'+enddate_split[1]
    date_all = startdate+" - "+enddate

    outputformat = request.form['outputformat']

    companycodeformat = request.form['CompanyCode']
    providecompanycode = request.form['providecompanycode']
    # the value of providecompanycode is decide if the user directly put in the company code, or upload a file, or select the entire database
    CompanyCodeUserPutin = request.form['company_code_user_putin']
    selected = request.form['selected_variable']
    selected_x = selected.split(',')
    variable_dict_check = {'SEC Central Index Key':'cik', 'Filing Date':'datefiled', 'SEC Form':'formtype', 'Company Name':'companyname', 'Reference Name of Complete Report Filing':'filename', 'First SEC Date with Index Record Information':'findexdate', 'Last SEC Date with Index Record Information':'lindexdate', 'Index Source':'source'}
    variable_list_str = ""
    for ele in selected_x:
        variable = variable_dict_check[ele]
        variable_list_str += variable + ','
    variable_list_str_final = variable_list_str[:-1] + ' '
    # selected = request.form.getlist('selecteditem')
    # selected_str = ""
    # for ele in selected:
    #     selected_str = selected_str + ele


    # FileUserChoose = request.files['choosefile']
    # variable_list = request.get_json(force=True)
    # data = variable_list['position1']
    if providecompanycode == 'EnterInCompanyCode':
        # this means user directly put in company code
        company_code_list = CompanyCodeUserPutin.split()
        company_code = "( "
        for ele in company_code_list:
            company_code += ele + ", "
        company_code_final = company_code[:-2]+')'
        condition_company_code = 'WHERE ' + companycodeformat + ' in ' + company_code_final
        condition_date_begin = ' AND secaccdate BETWEEN \'' + startdate_formatted
        condition_date_end = '\' AND \'' + enddate_formatted + '\''
    # elif providecompanycode == 'ChooseCompanyCodeFromFile':
        # upload a file
        # with open(FileUserChoose, 'r') as f:
            # company_code = f.read()
            # f.close()
    elif providecompanycode == 'SelectEntireDatabase':
        # select entire database
        company_code_final = ''
        condition_company_code = ''
        condition_date_begin = ' WHERE secaccdate BETWEEN \'' + startdate_formatted
        condition_date_end = '\' AND \'' + enddate_formatted + '\''
    # # variabletest = request.get_json(force=True,silent=False)
    # variabletest = request.json.get('position1')
    # # Maybe get json should be this one
    # #but the UserCreateForm
    # form = UserCreateForm.from_json(request.get_json())
    # form = UserCreateForm.form_json()


    open_line = 'SELECT  '
    # variables = '* '
    database_name = 'FROM forms '

    # company_code # this is the string contains all the company code, '1234546, 2334543, 244546'
    #具体company code值还没有写呢 要从textbox里面抓 或者读上传的文件里面抓

    statement = open_line+variable_list_str_final+database_name+condition_company_code+condition_date_begin+condition_date_end
    # +variabletestr

    try:
        conn = psycopg2.connect(database=secret.db_name, user=secret.user_name, host=secret.host, port=secret.port, sslcert=secret.sslcert, sslkey=secret.sslkey, sslrootcert=secret.sslrootcert, sslmode=secret.sslmode)
        cur = conn.cursor()
    except Error as e:
        print(e)
    # #
    cur.execute(statement)
    conn.commit()
    #
    # df = DataFrame(results.fetchall())
    # df.columns = results.keys()
    # if outputformat == 'csv':
    #     df.to_csv('output.csv')
    # elif outputformat == 'text':
    #     df.to_
    # elif outputformat == 'excel':
    #     df.to_exl



    if outputformat == 'csv':
        output_file_name = "output_"+str(output_number)+".csv"
        output_file_path = "output_file/"

        with open(output_file_path+output_file_name, 'w') as f:
            f = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in cur:
                f.writerow(row[:])
    elif outputformat == 'text':
        output_file_name = 'output_'+str(output_number)+'.txt'
        output_file_path = "output_file/"
        with open(output_file_path+output_file_name, 'w') as f:
        # with open('output.txt', 'w') as f:
            for row in cur:
                f.write(str(row[1:]))
    # elif outputformat == 'excel':
    #     with open('output.xlsx', 'w') as f:

    return render_template("output.html", variable_list=statement, output_file_name = output_file_name,output_number=output_number,date_all=date_all, outputformat=outputformat,selected=selected)
    # return render_template("query_test.html", variable_list=statement)

@app.route('/download_output')
def download_output():
    output_number = request.args.get('output_number', None)
    # outputformat = request.form['outputformat']
    outputformat = request.arg.get('outputformat',None)
    if outputformat == 'csv':
        file_path = "output_file/output_"+str(output_number)+".csv"
        file_name = "output_"+str(output_number)+".csv"
    elif outputformat == 'text':
        file_path = "output_file/output_"+str(output_number)+".txt"
        file_name = "output_"+str(output_number)+".txt"
    # 这里要把txt文件的下载加上

    try:
		# return send_file('./output_file/output.cvs', as_attachment=True, attachment_filename='output.cvs')
        return send_file(file_path, as_attachment=True, attachment_filename=file_name)
    except Exception as e:
        return str(e)

@app.route('/manuals')
def manuals():
    return render_template("manuals.html")

# @app.route('/search')
# def search():
#     return render_template("search.html")


@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        search_condition = request.form.get("search_condition")
        if keyword:
            if search_condition == '1':
                statement = "SELECT DISTINCT companyname, cik FROM consolidatedindex WHERE consolidatedindex.companyname ILIKE '"+keyword+"%'"
            elif search_condition =='2':
                statement = "SELECT DISTINCT companyname, cik FROM consolidatedindex WHERE consolidatedindex.companyname ILIKE '%"+keyword+"%'"
            elif search_condition =='3':
                statement = "SELECT DISTINCT companyname, cik FROM consolidatedindex WHERE consolidatedindex.companyname ILIKE '"+keyword+"'"

            try:
                conn = psycopg2.connect(database=db_name, user=user_name, host=host, port=port, sslcert=sslcert, sslkey=sslkey, sslrootcert=sslrootcert, sslmode=sslmode)
                cur = conn.cursor()
            except Error as e:
                print(e)

            cur.execute(statement)
            conn.commit()

            company_name_cik = {"content":[]}
            for row in cur:
                dict = {}
                dict['company_name'] = row[0]
                dict['cik'] = row[1]
                company_name_cik['content'].append(dict)
                # company_name.append(row[0])
                # cik.append(row[1])
        else:
            company_name_cik = {"content":[]}

        #     company_name = ['-']
        #     cik = ['-']
        #     no_input = "Need input"

    elif request.method == 'GET':
        company_name_cik = {"content":[]}

    # return render_template("search.html", company_name_cik=company_name_cik)



    #     x = str(company_name)+str(cik)
    #
    #     if story:
    #         result = myfunction(story)
    #         return jsonify(result=result)
    #     else:
    #         return jsonify(result='Input needed')

    # return render_template('index.html')
    # return render_template("query_test.html")
    # return redirect(url_for('search'))
    return render_template("search.html", company_name_cik=company_name_cik)

    # return flask.jsonify({'html':getPrediction(word)})

# @app.route('/', methods= ["GET", "POST"])
#
#
#     return render_template('index.html')


# @app.route('/get_word')
# def get_prediction():
#   word = flask.request.args.get('word')
#   return flask.jsonify({'html':getPrediction(word)})

    # if request.method == 'POST':
    # names = request.files["output-format"]
    # print(names)

    # if not request.json:
    #     abort(400)
    # print(request.json)
    # return json.dumps(request.json)

    # x = request.form["companycodechoice"]

    # if request.method == 'POST':
    #     if request.form["outputformat"] == "csv":
    #         format = '1111111111111111'
    #     else:
    #         format = '222222222222222'


    # if request.method == 'POST':
    # a = {'a':'b', 'c':'d'}
    # try:
    #     variable_list = request.get_json(force=True)
    #     blob = request.get_json(force=True)
    # except:
    #     abort(400)
    # if not 'title' in blob:
    #     abort(400)
    # task = {
    #     'id': tasks[-1]['id'] + 1,
    #     'title': blob['title'],
    #     'description': blob.get('description', ""),
    #     'done': False
    # }
    # tasks.append(task)
    # return jsonify({'task': task})




    # return(str(x))
    # for name in names:
    #     print(name)
    # return '', 200
    # x = json.loads(json_data)
    # a = []
    # for ele in x.values():
    #     a.append(ele)

#     start_date = request.form["startDate"]
#     end_date = request.form["endDate"]
#     company_code_type = request.form["company_code_type"]
#     enter_code = request.form["enter_code"]
#     enter_code_from_file = request.files["choosefile"]
#     enter_code_from_file = request.form["choosefile"]
#     f = open(enter_code_from_file, 'r')
#     f_raw = f.read()
#     company_code_from_file = []
#     for ele in f_raw:
#         company_code_from_file.append(ele)
#
#
#     # name = request.form["name"]
#     # message = request.form["message"]
#     # model.add_entry(name, message)
#
#     # selected_variable_list = request.json() #希望找到被选中的variable 放到query的select里面
#     # the selected div name is selectedItem
#     # But do not know if this is right
#
#     selected_variable_list = request.form["selectedItem"]
#     selected_variable_list = request.form.getlist('selectedItem')
#
#     s = ""
#     for ele in selected_variable_list:
#         s += ele+"\n"
#
#     query = "SELECT %sFROM Form" % s
#     test2 = selected_variable_list
#     # /output<filename> this should be right
#     #
#     # create a file, save it in the right directory
#     # create the name for it
#     # give the name to output_file

    # variable_list = ''j
    # for ele in json_data:
    # # loop over every row
    #     variable_list += ele + ', '


# output_format = request.form["output-format"]
# if output_format == 'csv':
#   with open('output.csv', 'wb') as csvfile:
#       csvfile.write(the_out_put_from_database)
# elif output_format == 'text':
#   with open('output.csv', 'wb') as csvfile:
#       csvfile.write(the_out_put_from_database)
# elif output_format == 'excel':
#   with open('output.csv', 'wb') as csvfile:
#       csvfile.write(the_out_put_from_database)
#
#     # this is the final one we will use but for now we test the query at first
#     # return render_template("output.html", output_file = )

#






#
# @app.route("/postentry", methods=["POST"])
# def postentry():
#     name = request.form["name"]
#     message = request.form["message"]
#     model.add_entry(name, message)
#     return redirect("/")
#
# @app.route('/download_pbs_rpython/')
# def download_pbs_rpython():
# 	try:
# 		return send_file('./static/pbs/example(r&python).pbs', as_attachment=True, attachment_filename='example(r&python).pbs')
# 	except Exception as e:
# 		return str(e)
#
# #************in HTML we will user
# #<a href="/<path:filename>" class="btn btn-primary" target="blank">Download the Materials</a>
# #or can we use href="{{url_for('download', variable = {{file_name}})}}"
#
# # @app.route('/<path:filename>', methods=['GET', 'POST'])
# @app.route('/<path:filename>', methods=['GET', 'POST'])
# def download(filename):
#     try:
#         return send_from_directory(app.static_folder, filename=filename)
#     except Exception as e:
#         return str(0)
#
#
#
#



# set the location for the whoosh index
# app.config['WHOOSH_BASE'] = 'path/to/whoosh/base'

# class Postgresql(db.Model):
#   __tablename__ = 'postgres'
#   __searchable__ = ['title', 'content']  # these fields will be indexed by whoosh
#
#   id = app.db.Column(app.db.Integer, primary_key=True)
#   title = app.db.Column(app.db.Text)
#   content = app.db.Column(app.db.Text)
#   created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#
#   def __repr__(self):
#      return '{0}(title={1})'.format(self.__class__.__name__, self.title)
#
#





if __name__=="__main__":
    # init()
    ################# STEP SIX: populate the database at 1 a.m. everyday #################

    # schedule.every().day.at("01:00").do(execute_all)
    #
    # while True:
    #     schedule.run_pending()
    #     time.sleep(30)
    app.run(host='127.0.0.1', port=5000,debug=True)
