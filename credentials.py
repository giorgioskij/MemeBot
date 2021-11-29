'''
To include personal credentials, such as the token or a custom path for the
users database file, create a file in this same directory named credentials_private.py 
and just declare the values as variables like:

TOKEN = <your_token>
USERS_PATH = <your_path> 
'''
try:
    from credentials_private import TOKEN, USERS_PATH
    TOKEN = TOKEN
    USERS_PATH = USERS_PATH
except:
    TOKEN = ''
    USERS_PATH = 'users.pkl'