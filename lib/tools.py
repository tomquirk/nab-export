from datetime import datetime
from getpass import getpass


def write_step(name, content):

    with open(name, 'w') as f:
        f.write(content)


def read_step(name):

    with open(name, 'r') as r:
        return r.read()


def get_credentials():

    try:
        with open('.credentials', 'r') as f:
            lines = f.read().split('\n')

            if len(lines) < 2:
                print '\n\n\tIt looks like there\'s only ' + str(len(lines)) + ' line in .credentials file'
                print '\tPlease ensure the file contains two lines,'
                print '\tfirst line - username, second line - password'
                print '\n\n'
                return None

            return lines

    except Exception as e:
        lines = []
        print('Could not find .credentials file. Please enter username and password')
        print('Username:')
        lines.append(raw_input())
        lines.append(getpass())

        return lines


def make_password(password, key, alphabet):

    # No idea why this is need. Seems to check for duplicates
    # Why they didn't do that on server? Stupid...
    for i in range(0, len(alphabet)):
        if i != alphabet.index(alphabet[i]):
            alphabet = alphabet[0, i] + alphabet[i+1:]

    # Now here's funny bit.
    # We take a character from password and corresponding (by index) character from
    # password key (which changes every page load).
    # Then we calculate the length between password character and corresponding
    # key character in the alphabet.
    r = []
    for i in range(0, len(password)):

        if password[i] in alphabet:
            pi = alphabet.index(password[i])
            ki = alphabet.index(key[i])
            ni = pi - ki
            if ni < 0:
                ni += len(alphabet)
            r.append(alphabet[ni])

    return ''.join(r)


def parse_transaction_date(text):
    return datetime.strptime(text, '%d %b %y')
