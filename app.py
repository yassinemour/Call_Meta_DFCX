import os,sys
from flask import Flask, request
from pymessenger import bot
import uuid
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import session
import json

app = Flask(__name__)

#Get Value from Config file 
with open('./Config.json', 'r') as f:
  configdata = json.load(f)

PAGE_ACCESS_TOKEN = configdata["PAGE_ACCESS_TOKEN"]
PROJECT_ID = configdata["project_id"]
LOCATION = configdata["location"]
AGENT_ID =  configdata["agent_id"]
LANGUAGE_CODE = configdata["language_code"]


bot = bot.Bot(PAGE_ACCESS_TOKEN)
#webhook Get
@app.route('/webhook', methods=['GET'])
def verify() :
    # webhook verfication
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge") :
        if not request.args.get("hub.verify_token") == configdata["verify_token"] :
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "This is a Poc of Connector DialogFlow CX & META for ADEO", 200

#webhook POST
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    #log(data)

    if data['object'] == 'page' :
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                #GET sender and Recipient id 
                sender_id = messaging_event['sender']['id']
                recipient_id = messaging_event['recipient']['id']
                 #GET post Message 
                if messaging_event.get('message'):
                    if 'text' in messaging_event['message']:
                        message_text = messaging_event['message']['text']
                    else: 
                         message_text = 'there is no text'

            #Call Dialog flow CX detect Intet with the message got from Meta (The goal it's to detect intent with message and get the Fulfillment response from dialog flow cx)
            responsedialogflow = detect_intent_from_dialogflowcx(PROJECT_ID ,LOCATION , AGENT_ID,message_text, LANGUAGE_CODE)
            bot.send_text_message(sender_id,str(responsedialogflow)) 
       
        #print(str(responsedialogflow))
        #print(sender_id) 
        #print(recipient_id)

    return "OK",200


def log(message):
    print(message)
    sys.stdout.flush()

#Methode to detect intent and get response from dialogflowcx 
def detect_intent_from_dialogflowcx(
    project_id,
    location,
    agent_id,
    text,
    language_code,
):
    """Returns the result of detect intent with sentiment analysis"""
    #print("Start Detect")
    client_options = None
    if location != "global":
        api_endpoint = f"{location}-dialogflow.googleapis.com:443"
        #print(f"API Endpoint: {api_endpoint}\n")
        client_options = {"api_endpoint": api_endpoint}
    session_client = SessionsClient(client_options=client_options)
    session_id = str(uuid.uuid4())

    session_path = session_client.session_path(
        project=project_id,
        location=location,
        agent=agent_id,
        session=session_id,
    )

    text_input = session.TextInput(text=text)
    query_input = session.QueryInput(text=text_input, language_code=language_code)

    request = session.DetectIntentRequest(
        session=session_path,
        query_input=query_input
    
    )

    response = session_client.detect_intent(request=request)
    if response.query_result.response_messages[1].text:
        response_text = response.query_result.response_messages[1].text.text[0]
    
    #print(f"Detect Intent Request: {request.query_params.disable_webhook}")
    #response_text = []
    #for message in response.query_result.response_messages:
       # if message.text:
           # curr_response_text = message.text.text
            #print(f"Agent Response: {curr_response_text}")
            #response_text.append(curr_response_text)
    return response_text

if __name__ == "__main__" :
    app.run(debug= True, port=80)