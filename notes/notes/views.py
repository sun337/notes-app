from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.views.generic import ListView
from .models import Folder
from .forms import NoteForm

import os
import json
import requests
from oauth2client.client import AccessTokenCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class Note(View):

    def add(request):
        user = request.user
        if not user.is_authenticated:
            return None
        drive = build_drive(user)
        folder = Folder.objects.get(user=user)
        file_metadata = {
            'name': 'Untitled',
            'parents': [folder.drive_id],
            'mimeType': 'application/vnd.google-apps.document'
        }
        req = drive.files().create(body=file_metadata, fields='id')
        response = req.execute()
        return redirect('../edit/'+str(response['id']))

    def get(request, noteId):
        user = request.user
        if not user.is_authenticated:
            return None
        drive = build_drive(user)
        req_get = drive.files().get(fileId=noteId)
        req_export = drive.files().export_media(fileId=noteId, mimeType='text/html')
        try:
            template_name = "notes/edit.html"
            response_export = req_export.execute()
            response_get = req_get.execute()
            form = NoteForm( initial={'title':response_get['name'], 'note':response_export} )
            return render(request, template_name, {'form': form})
        except Exception as e:
            print (e)
            logout(request)
            return redirect('/')

    @csrf_exempt
    def update(request, noteId):
        user = request.user
        if not user.is_authenticated:
            return None
        name = request.POST.get('name')
        file_metadata = {
            'name': name,
            'Content-Type': 'application/json; charset=UTF-8'
        }
        file1 = open(str(name)+".html","w")
        file1.write('<html>\n'+request.POST.get('data')+'\n</html>')
        file1.close()
        media = MediaFileUpload(str(name)+".html", mimetype='text/html')
        drive = build_drive(user)
        file = drive.files().update(fileId=noteId, body=file_metadata, media_body=media, fields='id').execute()
        os.remove(str(name)+".html")
        return HttpResponse('Success')


class NotesList(ListView):
    template_name = "notes/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return None
        self.template_name = "notes/list_notes.html"
        drive = build_drive(user)
        try:
            folder = Folder.objects.get(user=user)
            drive_id = folder.drive_id
        except Exception as e:
            try:
                file_metadata = {
                    'name': 'av_notes',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                req = drive.files().create(body=file_metadata, fields='id')
                response = req.execute()
                drive_id = response['id']
                Folder.objects.create(user=user, drive_id=drive_id)
                print (json.dumps(response, sort_keys=True, indent=4) )
            except Exception as e:
                print(e)
        
        req = drive.files().list(q="'"+str(drive_id)+"' in parents", fields='files(id, name, modifiedTime)')
        return make_call(req, self.request)
        

def logout_view(request):
    logout(request)
    return redirect('../')

def build_drive(user):
    social = user.social_auth.get(provider='google-oauth2')
    access_token = social.extra_data['access_token']
    credentials = AccessTokenCredentials(access_token, 'my-user-agent/1.0')
    drive = build('drive', 'v3', credentials=credentials)
    return drive

def make_call(req, request):
    try:
        response = req.execute()
        return response['files']
    except Exception as e:
        print (e)
        logout(request)
        return redirect('../')