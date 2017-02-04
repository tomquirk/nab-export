import re
from datetime import datetime

from mechanize import Browser, ControlNotFoundError, _http
from bs4 import BeautifulSoup
from bs4.element import NavigableString

from lib.tools import make_password, get_credentials
from lib.tools import parse_transaction_date

#
# There's could be more than one URL when you log in
#
logged_in_urls = ['https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl',
                  'https://ib.nab.com.au/nabib/loginProcess.ctl']


def get_accounts(text):
    """
    Scrapes given text and returns a list of accounts associated with the account
    :param text: raw HTML string of account overview
    :return: List of dictionaries, each representing accounts
    """
    soup = BeautifulSoup(text, "html.parser")
    account_divs = soup.select('.acctDetails')

    if len(account_divs) == 0:
        print('\tNo accounts found.')
        return None

    accounts = []

    for div in account_divs:
        name = div.select('a span')[0].text.strip()
        if not name:
            print('\tNo Account name found.')
            return None

        details_div = div.select('.accountNumber')[0]
        bsb = re.findall('BSB: ([\d-]*)', details_div.text)
        acc_no = re.findall('Acct No: ([\d-]*)', details_div.text)

        if not bsb or not acc_no:
            print('Account number of BSB is missing for account \'%s\'' % name)
            return None

        link = div.select('a[href^="javascript:viewTransaction(\'"]')[0]
        params = re.findall("'(.*?)'", link.attrs['href'])
        if len(params) != 2:
            print('\tError: incorrect HREF for account: ', link.attrib['href'])
            return None

        accounts.append({
            'name': name,
            'bsb': bsb[0],
            'acc_no': acc_no[0],
            'params': params
        })

    return accounts


def check_url(b, expected_urls):

    if type(expected_urls) == 'str':
        expected_urls = [expected_urls]

    if not b.geturl() in expected_urls:
        print('\tExpected URL: %s' % expected_urls)
        print('\tCurrent URL: %s' % b.geturl())
        return False

    return True


def login():

    creds = get_credentials()
    if not creds:
        return None

    b = Browser()
    b.set_handle_robots(False)
    b.addheaders = [
        ('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) '
                       'Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
        ('Connection', 'keep-alive'),
        ('Cache-Control', 'max-age=0'),
        ('Accept-Encoding', 'gzip, deflate, br')
    ]

    b.set_handle_equiv(True)
    b.set_handle_gzip(True)
    b.set_handle_redirect(True)
    b.set_handle_referer(True)
    b.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    b.set_handle_refresh(_http.HTTPRefreshProcessor(), max_time=1)

    # Want debugging messages?
    # b.set_debug_http(True)
    b.set_debug_redirects(True)
    b.set_debug_responses(True)

    print('Opening main page...')
    b.open('http://www.nab.com.au')
    print('OK')

    print('Opening login redir page...')
    b.open('http://www.nab.com.au/cgi-bin/ib/301_start.pl?browser=correct')
    print('OK')

    print('Opening real login page...')
    b.open('https://ib.nab.com.au/nabib/index.jsp')
    print('OK')

    b.select_form(nr=0)
    try:
        webKeyCtrl = b.form.find_control(id='webKey')
        webAlphaCtrl = b.form.find_control(id='webAlpha')
    except ControlNotFoundError:
        print('Cannot find necessary login controls, quitting')
        return

    webKey = webKeyCtrl.value
    webAlpha = webAlphaCtrl.value
    newPassword = make_password(creds[1], webKey, webAlpha)

    usernameCtrl = b.form.find_control(name='userid')
    passwordCtrl = b.form.find_control(name='encoded-password')
    passwordCtrl.readonly = False
    usernameCtrl.value = creds[0]
    passwordCtrl.value = newPassword

    b_data = b.form.find_control(name='browserData')
    b_data.readonly = False
    b_data.value = '1332067415674;z=-660*-600;s=1440x900x24;h=325b2e41;l=en-US;p=MacIntel;i=0;j=7;k=0;' \
                   'c=81d6c46c:,799e53ad:,f67180ac:,c801b011:,9ed81ce8:,68bab54a:,3db529ef,97362cfc;'

    b.form.new_control('text', 'login', {'value': ''})
    b.form.fixup()
    b['login'] = 'Login'

    print('Logging in...')
    b.submit()

    if not check_url(b, logged_in_urls):
        print('Error logging in.')
        return None

    print('OK')
    return b


def extract_transactions(content):

    soup = BeautifulSoup(content, "html.parser")
    rows = soup.select('#transactionHistoryTable tbody tr')
    transactions = []

    for row in rows:

        tds = row.select('td')
        detail_lines = list(tds[1].children)
        details = []

        for detail_line in detail_lines:
            if type(detail_line) == NavigableString:
                details.append(detail_line)

        # Here's the assumption here: if there are two lines in the transaction
        # details cell, first line is payee and second one is memo
        payee = details[0] if len(details) > 0 else ''
        memo = details[1] if len(details) > 1 else ''

        def toFloat(text):
            if len(text) > 0:
                return float(text[:-3].strip().replace(',', ''))
            return None

        transactions.append({
            'date': tds[0].text,
            'date_obj': parse_transaction_date(tds[0].text),
            'payee': payee,
            'memo': memo,
            'debit_amount': toFloat(tds[2].text),
            'credit_amount': toFloat(tds[3].text),
            'balance': toFloat(tds[4].text)
        })

        print payee

    return transactions


def open_account_transactions_page(b, account):

    account_id = account[0]
    account_type = account[1]

    if not b in logged_in_urls:
        print('\tCurrent url is %s, need to open accounts page in %s' %
              (b.geturl(), logged_in_urls[0]))
        b.open('https://ib.nab.com.au/nabib/acctInfo_acctBal.ctl')

    print('\tOpening transaction page for account %s... ' % account_id)

    URL_FORM_ACCOUNT_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistoryGetSettings.ctl'
    b.select_form(name='submitForm')
    b.form.set_all_readonly(False)
    b.form.action = URL_FORM_ACCOUNT_HISTORY
    b.form['account'] = account_id
    b.form['accountType'] = account_type
    b.submit()
    print('\tOK')

    if not check_url(b, URL_FORM_ACCOUNT_HISTORY):
        print('\tCannot open page %s with details for account %s' % (
              URL_FORM_ACCOUNT_HISTORY, account_id))
        return None

    print('\tOpening date range form...')
    URL_TRANS_HISTORY = 'https://ib.nab.com.au/nabib/transactionHistorySelectAccount.ctl'
    form_url = URL_TRANS_HISTORY + '?filterIndicator=true'
    b.open(form_url)
    if not check_url(b, form_url):
        return None
    print('\tOK')

    return b


def get_servers_today_date(b):

    # periodToDate seems to contain today's date, should be safe to use
    b.select_form(name='transactionHistoryForm')
    input_today = b.form['periodToDate'].split('/')

    return datetime(2000 + int(input_today[2]), int(input_today[1]), int(input_today[0]))


def query_server_transactions(b, start_date):

    TRANSACTIONS_PER_PAGE = 200
    end_date = get_servers_today_date(b)
    b.select_form(name='transactionHistoryForm')
    # Setting the period doesnt work - JS is involved. 90 Days default it is :(
    # b.form['periodModeSelect'] = ['Custom']
    # b.form['periodFromDate'] = start_date.strftime('%d/%m/%y')
    # periodFromDate = b.form.find_control(name='periodFromDate')
    # periodFromDate.value = start_date.strftime('%d/%m/%y')
    b.form['transactionsPerPage'] = [str(TRANSACTIONS_PER_PAGE)]
    b.form.fixup()
    
    URL_SUBMIT_HISTORY_FORM = 'https://ib.nab.com.au/nabib/transactionHistoryValidate.ctl'
    b.form.action = URL_SUBMIT_HISTORY_FORM

    print('\tGetting transactions from %s to %s' % (start_date.strftime('%d/%m/%y'), end_date))
    b.submit()

    response = b.response().read()
    if not check_url(b, URL_SUBMIT_HISTORY_FORM):
        return

    print('\tOK')

    return b


def get_all_transactions(b, account, start_date):

    b = query_server_transactions(b, start_date)
    if not b:
        return None

    # get transaction count
    cont = b.response().read()
    soup = BeautifulSoup(cont, "html.parser")
    rawTransCount = soup.find_all('td', text=re.compile('Found:'))
    if rawTransCount is None:
        print('No transaction count found, must be error')
        return None
    
    # period = soup.find_all('td', text=re.compile('Period:'))[0].get_text().replace('\t', '').split('\n')
    # actual_start_date = str(period[2].strip())
    # if actual_start_date != start_date.strftime('%d/%m/%y'):
    #     print('Server returned the wrong dates - %s vs expected %s' % (actual_start_date, start_date.strftime('%d/%m/%y')))
    #     return None

    transactionCount = int(rawTransCount[0].get_text().replace(',','').split(' ')[1])
    print("%d transactions found\n" % transactionCount)
    print("Initialising scrape...\n")

    trans = []

    # Extract and store all transactions into db
    while True:
        
        cont = b.response().read()
        soup = BeautifulSoup(cont, "html.parser")

        currPage = 1
        new_trans = extract_transactions(cont)

        if len(new_trans) == 0:
            print('\tNo transactions found on page %s, that\'s strange.')
        else:
            trans.extend(new_trans)
            print('\t%d transactions added.' % len(new_trans))

        print('Total transactions = %d' % len(trans))
        if len(trans) >= transactionCount:
            print('No more transactions')
            break

        currPage += 1

        print('\tOpening page #%d...' % currPage)
        b.open('https://ib.nab.com.au/nabib/transactionHistoryDisplay.ctl?fromAccount=&%s-p=%d' % (get_credentials()[2], currPage))

    return trans
