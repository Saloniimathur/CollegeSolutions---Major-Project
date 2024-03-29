import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, PTMeeting  # Assuming you have a model named Student and PTMeeting
import json

from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject
from itertools import zip_longest
from datetime import datetime
# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')

def homepage(request):
    print("Running")
    return render(request, 'index.html')

def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # #Google recaptcha
        # captcha_token = request.POST.get('g-recaptcha-response')
        # 
        # data = {
        #     'secret': captcha_key,
        #     'response': captcha_token
        # }
        # # Make request
        # try:
        #     captcha_server = requests.post(url=captcha_url, data=data)
        #     response = json.loads(captcha_server.text)
        #     if response['success'] == False:
        #         messages.error(request, 'Invalid Captcha. Try Again')
        #         return redirect('/')
        # except:
        #     messages.error(request, 'Captcha could not be verified. Try Again')
        #     return redirect('/')
        
        #Authenticate
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")




@csrf_exempt  # This is to exempt the view from CSRF protection for demonstration. In production, use proper CSRF handling.
def save_pt_meeting(request):
    if request.method == 'POST':
        try:
            student_ids = request.POST.getlist('studentId')
            queries = request.POST.getlist('query')
            actions = request.POST.getlist('action')
            dates = request.POST.getlist('date')
            print(dates)
            photos = request.FILES.getlist('photo')
            for student_id, query, action, date, photo in zip_longest(student_ids, queries, actions, dates, photos):
                try:
                    student = Student.objects.get(id=student_id)
                except Student.DoesNotExist:
                    return JsonResponse({'status': 'Error', 'message': 'Invalid student ID'})
                print(date)
                date = datetime.strptime(date, '%Y-%m-%d').date()
                pt_meeting = PTMeeting(student=student, query=query, action=action, date=date)
                if photo:
                    pt_meeting.photo = photo
                else:
                    return JsonResponse({'status': 'Error', 'message': 'Photo is required'})
                
                pt_meeting.save()

            return JsonResponse({'status': 'OK'})

                
                
        except Exception as e:
            print(e)
            return JsonResponse({'status': 'Error', 'message': str(e)})

    return JsonResponse({'status': 'Error', 'message': 'Invalid request method'})

@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')
