#Importing required modules
from __future__ import print_function
import httplib2
import os
from googleapiclient.discovery import build
#from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import base64
from bs4 import BeautifulSoup
import re
import time
import dateutil.parser as parser
from datetime import datetime
import datetime
import email
from cleantext import clean
import csv
import logging

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args([])
except ImportError:
    flags = None

#######################################################

#Defining auhorization scopes
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

# Defining credentials and storage file names
CLIENT_SECRET_FILE = 'credentials.json' #Name of gmail credential file
storage = 'gmail-storage.json' #Name of storage credential retured by Gmail API
APPLICATION_NAME = 'Gmail API Python' #Name of Application

########################################################

# Defining your gmail search query
search_query = "kunal.jain@analyticsvidhya.com, after:01/01/2019"

#Function to activate credential
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    path = '~/Desktop/folders/Doing_DS' #creating credential path
    home_dir = os.path.expanduser(path)
    credential_dir = os.path.join(home_dir, 'secrets')
    credential_path = os.path.join(credential_dir,
                                   CLIENT_SECRET_FILE)
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    storage_path = os.path.join(credential_dir,
                                   storage)

    store = Storage(storage_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(credential_path, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + storage_path)
    return credentials

#######################################################

#A function to get authorization and create a service
def get_service():
    
    #authorization of credentials
    http = credentials.authorize(httplib2.Http())

    #service variable is the access point to complete gmail API
    service = build('gmail', 'v1', http=http)
    
    return service

#######################################################

def filter_mail(service, query):
    '''
    service = a gmail service
    
    query = a search query
    '''
    # maxResults can be changed
    mail_id = service.users().messages().list(userId='me', 
                                              maxResults=5,
                                              q=search_query).execute()['messages']

    return mail_id

#######################################################

def data_encoder(text):
    if len(text)>0:
        message = base64.urlsafe_b64decode(text)
        message = str(message, 'utf-8')
        message = email.message_from_string(message)
    return message

#######################################################

def readMessage(content)->str:
    message = None
    if "data" in content['payload']['body']:
        message = content['payload']['body']['data']
        message = data_encoder(message)
    elif "data" in content['payload']['parts'][0]['body']:
        message = content['payload']['parts'][0]['body']['data']
        message = data_encoder(message)
    else:
        print("body has no data.")
    return message

########################################################

def fetch_mail(mail_id):
    mail_list = []
    
    for ml_id in mail_id:
        mail_dict = { }
        m_id = ml_id['id'] # get id of individual message
        message = service.users().messages().get(userId= 'me',
                                                 id=m_id).execute() 
        payld = message['payload'] # get payload of the message 
        m_head = payld['headers'] # getting message payload header

        
        for sub in m_head: #Fetching the mail Subject
            if sub['name'] == 'Subject':
                m_subj = sub['value']
                mail_dict['Subject'] = m_subj
            else:
                pass
        
        
        for dt in m_head: # getting the date
            if dt['name'] == 'Date':
                mail_date = dt['value']
                date_parse = (parser.parse(mail_date))
                m_date = (date_parse.date())
                mail_dict['Date'] = str(m_date)
            else:
                pass

        
        for sender in m_head: # getting the Sender
            if sender['name'] == 'From':
                m_from = sender['value']
                mail_dict['Sender'] = m_from
            else:
                pass
            
            
        mssg = readMessage(message)
        msg_body = BeautifulSoup(mssg.get_payload(), 'lxml')
        msg_text = msg_body.body.get_text()
        clean_text = clean(msg_text, fix_unicode=True, no_line_breaks=True, no_urls=True)
        mail_dict['Message body'] = clean_text
        
        mail_list.append(mail_dict)
    
    return mail_list

######################################################

def save_data(mail_list, file_path):
    with open(file_path, 'w', encoding='utf-8', newline = '') as csvfile: 
        #fieldnames = ['Sender','Subject','Date','Snippet','Message_body']
        fieldnames = ['Sender','Subject','Date','Message body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter = ',')
        writer.writeheader()
        for val in mail_list:
            writer.writerow(val)
            
#######################################################

def main(project_dir):
    '''
    main method
    '''
    # get logger
    logger = logging.getLogger(__name__)
    logger.info('getting raw gmail data')
    
    # search and get mail ids
    mail_ids = filter_mail(service, query = search_query)
    logger.info('searching gmail to get mail ids')
    
    # fetch mail ids to a list
    mail_List = fetch_mail(mail_id = mail_ids)
    logger.info('Fetching and cleaning gmail')
    
    # gmail file paths
    raw_data_path = os.path.join(os.path.pardir,'data','raw')
    fetchmail_data_path = os.path.join(raw_data_path, 'fetched_gmail.csv')
    
    # saving gmail data
    save_data(mail_List,fetchmail_data_path)
    logger.info('saving gmail data')


if __name__ == '__main__':
    # getting root directory
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    
    # setup logger
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    
    #getting credentials
    credentials = get_credentials()
    #logger.info('getting gmail credentials')
    
    #creating the service
    service = get_service()
    #logger.info('creating gmail service')

    # call the main
    main(project_dir)
