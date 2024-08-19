import os
import requests
from io import BytesIO
from twilio.rest import Client
from google.cloud import speech
from google.cloud import vision
from PIL import Image
from pytesseract import image_to_string
from dotenv import load_dotenv




load_dotenv()

class TwilioMessageHandler:
    def __init__(self):
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.google_cloud_speech_credentials = os.getenv('GOOGLE_CLOUD_SPEECH_CREDENTIALS')
        self.google_cloud_vision_credentials = os.getenv('GOOGLE_CLOUD_VISION_CREDENTIALS')

        self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        self.google_cloud_speech_client = speech.SpeechClient(credentials=self.google_cloud_speech_credentials)
        self.google_cloud_vision_client = vision.ImageAnnotatorClient(credentials=self.google_cloud_vision_credentials)

    def handle_message(self, message):
        print("Received message:", message)
        if message.media:
            if message.media[0].content_type.startswith('audio/'):
                return self.handle_audio(message.media[0].url)
            elif message.media[0].content_type.startswith('image/'):
                return self.handle_image(message.media[0].url)
        elif message.body:
            return message.body

    def handle_audio(self, audio_url):
        try:
            audio_data = requests.get(audio_url).content
            speech_config = speech.types.RecognitionConfig(
                encoding=speech.types.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code='en-US'
            )
            speech_audio = speech.types.RecognitionAudio(content=audio_data)
            response = self.google_cloud_speech_client.recognize(speech_config, speech_audio)
            if response.results:
                return response.results[0].alternatives[0].transcript
            else:
                return self.send_error_message('Sorry, unable to hear it. Please try again with a clearer audio.')
        except Exception as e:
            print(e)
            return self.send_error_message('Sorry, unable to process audio. Please try again.')

    def handle_image(self, image_url):
        try:
            image_data = requests.get(image_url).content
            image = Image.open(BytesIO(image_data))
            text = image_to_string(image)
            return text.strip()
        except Exception as e:
            print(e)
            return self.send_error_message('Sorry, unable to read image. Please try again with a clearer photo.')

    def send_error_message(self, message):
        return message

# Usage:
handler = TwilioMessageHandler()

# Call the handle_message function when a message is received
def receive_message(message):
    return handler.handle_message(message)