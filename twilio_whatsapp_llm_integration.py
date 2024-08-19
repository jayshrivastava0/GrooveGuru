from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import time
import openai
from twilio.rest import Client
from dotenv import load_dotenv
from urllib.parse import parse_qs

load_dotenv()

# OpenAI API Key
openai_key: str = os.environ.get('OPENAI_API_KEY')
openai_assistant_id: str = os.environ.get('OPENAI_ASSISTANT_ID')

# Initialize Twilio client
account_sid: str = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token: str = os.environ.get('TWILIO_AUTH_TOKEN')
client_twilio: Client = Client(account_sid, auth_token)

# Twilio WhatsApp sandbox number
twilio_whatsapp_number: str = 'whatsapp:+14155238886'

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for incoming WhatsApp messages.
    """
    def do_GET(self):
        self.send_response(405)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Method Not Allowed. Please send a POST request to /whatsapp.")

        
    def do_POST(self) -> None:
        """
        Handle incoming POST requests.
        
        :return: None
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        assistant_id: str = self.server.assistant_id
        client_openai: openai.OpenAI = self.server.client
        thread = client_openai.beta.threads.create()
        thread_id: str = thread.id
        
        if self.path == '/whatsapp':
            post_data = parse_qs(post_data.decode('utf-8'))
            print(post_data)
            
            incoming_msg: str = post_data.get('Body', [''])[0]
            sender_name: str = post_data.get('ProfileName', [''])[0]
            sender_number: str = post_data.get('From', [''])[0].replace('whatsapp:', '')
            
            # Get GenAI response
            incoming_msg = incoming_msg + " From: " + sender_name
            response: str = self.process_user_message(client_openai, thread_id, assistant_id, incoming_msg)
            
            if response is None:
                response = "Failed to process incoming message."

            # Send Whatsapp Message
            self.send_whatsapp_message(sender_number, response)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = json.dumps({'response': response})
            self.wfile.write(response_data.encode('utf-8'))

        else:
            self.send_error(404)

    def send_whatsapp_message(self, recipient_number: str, message_body: str) -> None:
        """
        Send a WhatsApp message to the specified recipient.
        
        :param recipient_number: The recipient's WhatsApp number.
        :param message_body: The message to be sent.
        :return: None
        """
        print("RECIPIENT NUMBER:" + str(recipient_number))
        message = client_twilio.messages.create(
            body=message_body,
            from_=twilio_whatsapp_number,
            to=f'whatsapp:{recipient_number}'
        )
        print(f"Sent WhatsApp message to {recipient_number}: {message_body}")

    def process_user_message(self, client: openai.OpenAI, thread_id: str, assistant_id: str, user_message: str) -> str:
        """
        Process the user's message and get a response from the GenAI model.
        
        :param client: The OpenAI client instance.
        :param thread_id: The thread ID for the conversation.
        :param assistant_id: The assistant ID for the conversation.
        :param user_message: The user's message.
        :return: The response from the GenAI model.
        """
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )

        run_id: str = run.id
        run_status: str = run.status

        while run_status not in ["completed", "failed", "requires_action"]:
            time.sleep(3)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            run_status = run.status

        if run_status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            output: str = messages.data[0].content[0].text.value
            return output
        elif run_status == "failed":
            print("Run failed.")
            return None

class MyHTTPServer(HTTPServer):
    """
    Custom HTTP server for handling incoming WhatsApp messages.
    """
    
    def __init__(self, server_address: tuple, RequestHandlerClass: type, assistant_id: str, client: openai.OpenAI):
        """
        Initialize the HTTP server.
        
        :param server_address: The server address.
        :param RequestHandlerClass: The request handler class.
        :param assistant_id: The assistant ID.
        :param client: The OpenAI client instance.
        """
        self.assistant_id = assistant_id
        self.client = client
        super().__init__(server_address, RequestHandlerClass)

def run_server() -> None:
    """
    Run the HTTP server.
    
    :return: None
    """
    client: openai.OpenAI = openai.OpenAI(api_key=openai_key)

    port: int = 8080  # Changed port to 8080
    server_address: tuple = ('', port)
    httpd: MyHTTPServer = MyHTTPServer(server_address, MyHTTPRequestHandler, openai_assistant_id, client)
    print(f"Server running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()