import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import datetime
from calendar import monthrange
from anthill import anthill, anthill_name

def auth_log(this_month):
    '''
    authentification for all other action with worksheet, using scope, credentials, authentification
    '''
    # defining the scope of the aplication
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # credentials to google drive and sheet API
    credentials = ServiceAccountCredentials.from_json_keyfile_name('ups_anthill_inout_google_drive.json', scope)
    # authentification
    gc = gspread.authorize(credentials)
    wks = gc.open(this_month).sheet1
    return wks

def row_delete(order, wks):
    '''
    delete row with order
    '''
    wks.delete_row(order+2)

def row_insert(order, wks):
    '''
    add a row with order
    '''
    wks.insert_row([], order+2)

def create_new_sheet(anthill, this_month, days):
    '''
    creating new sheet when there is no existing with current month name
    '''
    sh = gc.create(this_month)
    # sharing the new sheet with acc
    sh.share('anthillprague@gmail.com', perm_type='user', role='owner')
    wks = gc.open(this_month).sheet1
    resize_rows = anthill.num_of_ants + 2
    resize_cols = days + 7
    wks.resize(rows=resize_rows, cols=resize_cols)
    return wks


def number_of_days():
    '''
    number of days in a month for writting in columns
    '''
    now = datetime.datetime.now()
    days = monthrange(now.year, now.month)[1]
    return days

def a_notion(a1, a2, b1, b2):
    '''
    convert to A1 notion ({}:{})
    '''
    a1_notion = gspread.utils.rowcol_to_a1(a1, a2)
    a2_notion = gspread.utils.rowcol_to_a1(b1, b2)
    return a1_notion, a2_notion

def batch_cells(list_append,cell_list, wks):
    '''
    batch updating the cell with list of values
    '''
    for i, val in enumerate(list_append):  #gives us a tuple of an index and value
        cell_list[i].value = val    #use the index on cell_list and the val from cell_values
    wks.update_cells(cell_list, value_input_option='USER_ENTERED')

def worksheet_title(anthill, this_month, wks):
    '''
    naming the cell (1,1) with curretnt month name and the worksheet tittle
    '''
    wks.update_cell(1,1, "{}".format((this_month.upper())))
    wks.update_title("{}".format(this_month))
    wks.update_cell(2+anthill.num_of_ants, 1, "hours/day")

def names_rows(anthill, wks):
    '''
    names in anthill_list is written in first column sorted alphabeticly
    '''
    names_list = [] 
    a1_notion, a2_notion = a_notion(2, 1, anthill.num_of_ants+1, 1)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    names_list = [key for key, values in sorted(anthill_name.items(), key=lambda x: x[1].row)]
    batch_cells(names_list, cell_list, wks)

def header_days(days, wks):
    '''
    writing month's days in header row
    '''
    days_list = []
    a1_notion, a2_notion = a_notion(1, 2, 1, days+1)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(1, days+1):
        days_list.append(x)
    batch_cells(days_list, cell_list, wks)

def header_calculation(days, wks):
    '''
    labels for the columns in the SUM part of the worksheets
    '''
    calc_list = ["SUM hours", "wage", "wage - 1%", "tips ratio", "tips", "total"]
    a1_notion, a2_notion = a_notion(1, days+2, 1, days+len(calc_list)+1)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    batch_cells(calc_list, cell_list, wks)

def SUM_day(anthill, days, wks):
    '''
    formula for SUM hours in all days
    '''
    sum_day_list = []
    a1_notion, a2_notion = a_notion(2,days+2,anthill.num_of_ants+1,days+2)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(anthill.num_of_ants):
        b1_notion, b2_notion = a_notion(x+2, 2, x+2, days+1)
        sum_day_list.append("=SUM({}:{})".format(b1_notion, b2_notion))
    batch_cells(sum_day_list, cell_list, wks)


def SUM_wage(anthill_name, days, wks):
    '''
    formula for SUM wage * user pay
    '''
    sum_wage_list = []
    a1_notion, a2_notion = a_notion(2,days+3,anthill.num_of_ants+1,days+3)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    sorted_keys = [key for key, values in sorted(anthill_name.items(), key=lambda x: x[1].row)]
    for key in sorted_keys:
        b1_notion, b2_notion = a_notion(anthill_name[key].row, days+2, 1, 1)
        sum_wage_list.append("=SUM({}*{})".format(b1_notion, anthill_name[key].pay))
    batch_cells(sum_wage_list, cell_list, wks)


def SUM_wage99(anthill, days, wks):
    '''
    formula for SUM 99% of the wage (exclude the 1% that goes)
    '''
    sum_wage99_list = []
    a1_notion, a2_notion = a_notion(2,days+4,anthill.num_of_ants+1,days+4)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(anthill.num_of_ants):
        b1_notion, b2_notion = a_notion(x+2, days+3, 1, 1)
        sum_wage99_list.append("=0.99*ROUNDDOWN({};0)".format(b1_notion))
    batch_cells(sum_wage99_list, cell_list, wks)

def SUM_tips_ratio(anthill, days, wks):
    '''
    formula SUM tips ratio for each row user time to all time in a month
    '''
    sum_tips_ratio_list = []
    a1_notion, a2_notion = a_notion(2,days+5,anthill.num_of_ants+1,days+5)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(anthill.num_of_ants):
        b1_notion, b2_notion = a_notion(x+2, days+2, anthill.num_of_ants+2, days+2)
        sum_tips_ratio_list.append("={}/{}".format(b1_notion, b2_notion))
    batch_cells(sum_tips_ratio_list, cell_list, wks)

def SUM_tips(anthill, days, wks):
    '''
    formula SUM tips based on ratio
    '''
    sum_tips_list = []
    a1_notion, a2_notion = a_notion(2,days+6,anthill.num_of_ants+1,days+6)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(anthill.num_of_ants):
        b1_notion, b2_notion = a_notion(x+2, days+5, anthill.num_of_ants+2, days+6)
        sum_tips_list.append("=ROUNDDOWN({}*{};0)".format(b1_notion, b2_notion))
    batch_cells(sum_tips_list, cell_list, wks)

def SUM_total(anthill, days, wks):
    '''
    formula SUM total of the payment
    '''
    sum_total_list = []
    a1_notion, a2_notion = a_notion(2,days+7,anthill.num_of_ants+1,days+7)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    for x in range(anthill.num_of_ants):
        b1_notion, b2_notion = a_notion(x+2, days+4, x+2, days+6)
        sum_total_list.append("=ROUNDDOWN({}+{};0)".format(b1_notion, b2_notion))
    batch_cells(sum_total_list, cell_list, wks)

def SUM_all(anthill, days, wks):
    '''
    SUM of hours for each day and colmuns during the month in the worksheet
    '''
    sum_all_list = []
    a1_notion, a2_notion = a_notion(anthill.num_of_ants+2, 2, anthill.num_of_ants+2, days+7)
    cell_list = wks.range("{}:{}".format(a1_notion, a2_notion))
    # print(cell_list)
    for x in range(1, days+7):
        b1_notion, b2_notion = a_notion(2, x+1, anthill.num_of_ants+1, x+1)
        sum_all_list.append("=SUM({}:{})".format(b1_notion, b2_notion))
    batch_cells(sum_all_list, cell_list, wks)
    wks.update_cell(2+anthill.num_of_ants, days+6, "0")

def user_sheet_log(anthill_name, day_in, user_name, hours_delta, wks):
    '''
    writing the user time in the user cell with the day IN
    '''
    if wks.cell(anthill_name[user_name].row, day_in+1).value == "":
        wks.update_cell(anthill_name[user_name].row, day_in+1, "=ROUNDDOWN({};2)".format(hours_delta))
    else:
        cell_value = float(wks.cell(anthill_name[user_name].row, day_in+1).value)
        total_hours = cell_value + hours_delta
        wks.update_cell(anthill_name[user_name].row, day_in+1, "=ROUNDDOWN({};2)".format(total_hours))

def try_this_month():
    # to do: move newly created spredsheet to ucetnictvi folder
    this_month = time.strftime("%b %Y", time.gmtime())
    days = number_of_days()
    # cathing the error when the sheet doesnt exist
    try:
        wks = auth_log(this_month)
    except:
        wks = create_new_sheet(anthill, this_month, days)
        update_worksheet(anthill, wks)
    return  wks, this_month, days

def update_worksheet(anthill, days, wks):
    '''
    the fuction to update all the information in the worksheet
    '''
    worksheet_title(anthill, this_month, wks)
    names_rows(anthill, wks)
    header_days(days, wks)
    header_calculation(days, wks)
    SUM_day(anthill, days, wks)
    SUM_wage(anthill_name, days, wks)
    SUM_wage99(anthill, days, wks)
    SUM_tips_ratio(anthill, days, wks)
    SUM_tips(anthill, days, wks)
    SUM_total(anthill, days, wks)
    SUM_all(anthill, days, wks)
