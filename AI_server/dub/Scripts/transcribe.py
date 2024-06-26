import boto3

import json
import requests
import time
import os
import sys
import traceback
import configparser
import re
import regex

import dub.Scripts.shared_imports as shared_imports
shared_imports.set_up_config()

import dubbing.settings as settings


def upload_file_to_s3(file_path, bucket_name, session):

    s3 = session.client('s3')
    file_name = os.path.basename(file_path)

    try:
        response = s3.upload_file(file_path, bucket_name, file_name)
        s3_uri = f"s3://{bucket_name}/{file_name}"
        return s3_uri
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def download_file_from_s3(file_uri, file_path, session):
    s3 = session.client('s3')
    bucket_name = file_uri.split('/')[2]
    key = file_uri.split('/')[3]

    try:
        response = s3.download_file(bucket_name, key, file_path)
        return True
    except Exception as e:
        print(f"Error downloading file from S3: {e}")
        traceback.print_exc()
        return False

def download_transcript(transcript_file_uri,session,file_name, generate_srt_file = True ):
    s3 = session.client('s3')


    if(generate_srt_file):
        response = s3.get_object(Bucket=transcript_file_uri[0].split('/')[3], Key=transcript_file_uri[0].split('/')[4])
        transcript_srt = response['Body'].read().decode('utf-8')
        file_path = os.path.join(shared_imports.DOWNLOAD_FOLDER , f'{shared_imports.ORIGINAL_VIDEO_NAME}.srt')
    else:
        response = s3.get_object(Bucket=transcript_file_uri.split('/')[3], Key=transcript_file_uri.split('/')[4])
        transcript_srt = response['Body'].read().decode('utf-8')
        file_path = os.path.join(shared_imports.DOWNLOAD_FOLDER , f'{shared_imports.ORIGINAL_VIDEO_NAME}.json')
    print(file_path)
    with open(file_path, "w") as f:
        f.write(transcript_srt)
    s3.delete_object(Bucket = 'globallearn',Key = f'{file_name}.srt')
    s3.delete_object(Bucket = 'globallearn',Key = f'{file_name}.json')

def start_transcription_job(transcription_job_name, language_code, media_sample_rate_hertz, media_format, media_file_uri,session,file_name , generate_srt_file = True ):

    transcribe = session.client('transcribe')

    job_params = {
        "TranscriptionJobName": transcription_job_name,
        "LanguageCode": language_code,
        "MediaFormat": media_format,
        "Media": {
            "MediaFileUri": media_file_uri
        },
        "OutputBucketName": "globallearn",
        "Subtitles": {
            "OutputStartIndex" : 1 ,
            "Formats": ["srt"]
        }
    }

    if media_sample_rate_hertz:
        job_params["MediaSampleRateHertz"] = media_sample_rate_hertz

    try:
        response = transcribe.start_transcription_job(**job_params)
        print("Transcription job started successfully.")
        print(f"Job Name: {transcription_job_name}")
        print(f"Job Status: {response['TranscriptionJob']['TranscriptionJobStatus']}")

        job_status = response['TranscriptionJob']['TranscriptionJobStatus']

        while job_status not in ['COMPLETED', 'FAILED']:
            time.sleep(10)  # Wait for 10 seconds
            response = transcribe.get_transcription_job(TranscriptionJobName=transcription_job_name)
            job_status = response['TranscriptionJob']['TranscriptionJobStatus']
        if job_status == 'COMPLETED':
            print("Transcription job completed successfully.")
            try :
                if(generate_srt_file):
                    transcript_file_uri = response['TranscriptionJob']['Subtitles']['SubtitleFileUris']
                    download_transcript(transcript_file_uri,session,file_name, generate_srt_file)
                else :
                    transcribe_json_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    download_transcript(transcribe_json_uri,session,file_name , generate_srt_file)
            except Exception as e:
                print(f"Error downloading transcript file: {e}")
            finally:
                transcribe.delete_transcription_job(TranscriptionJobName=transcription_job_name)
        elif job_status == 'FAILED':
            print("Transcription job failed.")

    except Exception as e:
        print(f"Error starting transcription job: {e}")



def transcribe(audio_path,videoToProcess , generate_srt_file = True):
    print("===============================================Transcribing audio file...===========================================")

    session = settings.AWS_SESSION

    file_path = audio_path
    bucket_name = "globallearn"
    s3_uri = upload_file_to_s3(file_path, bucket_name,session)

    file_name = os.path.splitext(os.path.basename(videoToProcess))[0]

    if s3_uri:
        transcription_job_name = file_name
        language_code = "en-US"
        media_sample_rate_hertz = 44100
        media_format = "mp3"
        start_transcription_job(transcription_job_name, language_code, media_sample_rate_hertz, media_format, s3_uri,session,file_name , generate_srt_file)

    else:
        print("File upload failed.")

