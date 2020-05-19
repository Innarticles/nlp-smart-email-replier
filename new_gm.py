# Importing required libraries
from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
import re
import time
import dateutil.parser as parser
from datetime import datetime
import datetime
import csv


# Creating a storage.JSON file with authentication details
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'


def main():
    
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    
   
    service = build('gmail', 'v1', http=creds.authorize(Http())) #  
    # Call the Gmail API to fetch INBOX
    results = service.users().messages().list(userId='me',labelIds = ['INBOX']).execute()
    messages = results.get('messages', [])
 
    print ("Total messages in inbox: ", str(len(messages)))

    final_list = [ ]


    for msg in messages:
        temp_dict = { }
        m_id = msg['id'] # get id of individual message
        message = service.users().messages().get(userId= 'me', id=m_id).execute() # fetch the message using API
        payld = message['payload'] # get payload of the message 
        headr = payld['headers'] # get header of the payload


        for one in headr: # getting the Subject
            if one['name'] == 'Subject':
                msg_subject = one['value']
                temp_dict['Subject'] = msg_subject
            else:
                pass

        for two in headr: # getting the date
            if two['name'] == 'Date':
                msg_date = two['value']
                date_parse = (parser.parse(msg_date))
                m_date = (date_parse.date())
                temp_dict['Date'] = str(m_date)
            else:
                pass

        for three in headr: # getting the Sender
            if three['name'] == 'From':
                msg_from = three['value']
                temp_dict['Sender'] = msg_from
            else:
                pass

        #temp_dict['Snippet'] = message['snippet'] # fetching message snippet


        try:
            
            # Fetching message body
            mssg_parts = payld['parts'] # fetching the message parts
            part_one  = mssg_parts[0] # fetching first element of the part 
            part_body = part_one['body'] # fetching body of the message
            part_data = part_body['data'] # fetching data from the body
            clean_one = part_data.replace("-","+") # decoding from Base64 to UTF-8
            clean_one = clean_one.replace("_","/") # decoding from Base64 to UTF-8
            clean_two = base64.b64decode (bytes(clean_one, 'UTF-8')) # decoding from Base64 to UTF-8
            soup = BeautifulSoup(clean_two , "lxml" )
            mssg_body = soup.body()
            # mssg_body is a readible form of message body
            # depending on the end user's requirements, it can be further cleaned 
            # using regex, beautiful soup, or any other method
            temp_dict['Message_body'] = mssg_body

        except:
            pass
        
        #print(temp_dict)
        final_list.append(temp_dict) # This will create a dictonary item in the final list



    print("Total messaged retrived: ", str(len(final_list)))



    #exporting the values as .csv
    with open('g_message_output.csv', 'w', encoding='utf-8', newline = '') as csvfile:
        fieldnames = ['Sender','Subject','Date','Message_body']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter = ',')
        writer.writeheader()
        for val in final_list:
            writer.writerow(val)

if __name__ == '__main__':
    main()
