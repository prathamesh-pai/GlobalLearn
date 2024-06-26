"""
Django settings for dubbing project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from dotenv import load_dotenv
from pathlib import Path

import boto3
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG') == 'True'

BACKEND_URL = os.getenv('BACKEND_URL')
ALLOWED_HOSTS = [BACKEND_URL, 'localhost', ]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "dub",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dubbing.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dubbing.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


#################################################################################################
############################## SETTING UP MONGODB DATABASE ######################################
#################################################################################################
# Get the MongoDB connection string from the environment variable
db_url = os.getenv('DB_URL')


# Create a new client and connect to the server
client = MongoClient(db_url)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    mongoDB = client['GlobalLearn']
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

#################################################################################################
################################## AWS AUTHORIZATION #########################################
#################################################################################################
AWS_SESSION = None
def aws_auth():
  global AWS_SESSION
  AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
  AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
  AWS_REGION = 'ap-south-1'
  AWS_SESSION = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
  )
  return AWS_SESSION

aws_auth()



# Google Authentication Modules
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
# from google.cloud import translate_v2

from dub.Scripts.shared_imports import *

# Other Modules
import os
import sys
import traceback
from json import JSONDecodeError
import configparser
import deepl


# Google Cloud Globals
GOOGLE_TTS_API = None
GOOGLE_TRANSLATE_API = None

# deepl Globals
DEEPL_API = None


#################################################################################################
################################## GOOGLE AUTHORIZATION #########################################
#################################################################################################

# Authorize the request and store authorization credentials.
def get_authenticated_service():
  global GOOGLE_TTS_API
  global GOOGLE_TRANSLATE_API
  # SERVICE_ACCOUNT_FILE = 'service_secrets.json'
  GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/cloud-translation']

  # TTS API Info
  GOOGLE_TTS_API_SERVICE_NAME = 'texttospeech'
  GOOGLE_TTS_API_VERSION = 'v1'
  TTS_DISCOVERY_SERVICE_URL = "https://texttospeech.googleapis.com/$discovery/rest?version=v1"

  # Translate API Info
  # https://translate.googleapis.com/$discovery/rest?version=v3 # v3 or beta v3beta1
  GOOGLE_TRANSLATE_API_SERVICE_NAME = 'translate'
  GOOGLE_TRANSLATE_API_VERSION = 'v3beta1' # V2, V3, or V3beta1
  TRANSLATE_DISCOVERY_SERVICE_URL = "https://translate.googleapis.com/$discovery/rest?version=v3beta1" # Don't forget to set the version number here too


  # Set proper variables based on which API is being used

  API_SCOPES = GOOGLE_API_SCOPES

  # secrets_file = SERVICE_ACCOUNT_FILE

  # # Check if client_secrets.json file exists, if not give error
  # if not os.path.exists(secrets_file):
  #   # In case people don't have file extension viewing enabled, they may add a redundant json extension
  #   if os.path.exists(f"{secrets_file}.json"):

  #     secrets_file = secrets_file + ".json"
  #   else:
  #     print(f"\n         ----- [!] Error: client_secrets.json file not found -----")
  #     print(f" ----- Did you create a Google Cloud Platform Project to access the API? ----- ")
  #     input("\nPress Enter to Exit...")
  #     sys.exit()

  creds = None
  SERVICE_ACCOUNT_CREDENTIALS = {
    'type': os.getenv('TYPE'),
    'project_id': os.getenv('PROJECT_ID'),
    'private_key_id': os.getenv('PRIVATE_KEY_ID'),
    'private_key': os.getenv('PRIVATE_KEY').replace('\\n', '\n'),
    'client_email': os.getenv('CLIENT_EMAIL'),
    'client_id': os.getenv('CLIENT_ID'),
    'auth_uri': os.getenv('AUTH_URI'),
    'token_uri': os.getenv('TOKEN_URI'),
    'auth_provider_x509_cert_url': os.getenv('AUTH_PROVIDER_X509_CERT_URL'),
    'client_x509_cert_url': os.getenv('CLIENT_X509_CERT_URL'),
    "universe_domain": "googleapis.com"
  }
  # Load the service account credentials
  creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_CREDENTIALS,  scopes=API_SCOPES)
  # Build tts and translate API objects
  GOOGLE_TTS_API = build(GOOGLE_TTS_API_SERVICE_NAME, GOOGLE_TTS_API_VERSION, credentials=creds, discoveryServiceUrl=TTS_DISCOVERY_SERVICE_URL)
  GOOGLE_TRANSLATE_API = build(GOOGLE_TRANSLATE_API_SERVICE_NAME, GOOGLE_TRANSLATE_API_VERSION, credentials=creds, discoveryServiceUrl=TRANSLATE_DISCOVERY_SERVICE_URL)
  # GOOGLE_TRANSLATE_V2_API = translate_v2.Client(credentials=creds)

  return GOOGLE_TTS_API, GOOGLE_TRANSLATE_API


def first_authentication():
  global GOOGLE_TTS_API, GOOGLE_TRANSLATE_API
  try:
    GOOGLE_TTS_API, GOOGLE_TRANSLATE_API = get_authenticated_service() # Create authentication object
  except JSONDecodeError as jx:
    print(f" [!!!] Error: " + str(jx))
    print(f"\nDid you make the yt_client_secrets.json file yourself by copying and pasting into it, instead of downloading it?")
    print(f"You need to download the json file directly from the Google Cloud dashboard, by creating credentials.")
    input("Press Enter to Exit...")
    sys.exit()
  except Exception as e:
    if "invalid_grant" in str(e):
      GOOGLE_TTS_API, GOOGLE_TRANSLATE_API = get_authenticated_service()
    else:
      print('\n')
      traceback.print_exc() # Prints traceback
      print("----------------")
      print(f"[!!!] Error: " + str(e))
      sys.exit()
  return GOOGLE_TTS_API, GOOGLE_TRANSLATE_API


################################################################################################
################################## DEEPL AUTHORIZATION #########################################
################################################################################################

def deepl_auth():
  # Deepl API Key
  deepl_auth_object = deepl.Translator(os.getenv('DEEPL_API_KEY'))
  return deepl_auth_object

if cloudConfig['translate_service'] == 'deepl':
  DEEPL_API = deepl_auth()


#################################################################################################
################################## GOOGLE AUTHORIZATION #########################################
#################################################################################################

if cloudConfig['tts_service'] == "google" or (config['skip_translation'] == False and (cloudConfig['translate_service'] == "google" or cloudConfig['use_fallback_google_translate'])):
  GOOGLE_TTS_API, GOOGLE_TRANSLATE_API = first_authentication()



VDOCIPHER_API_SECRET = os.getenv('VDOCIPHER_API_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')