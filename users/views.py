from django.dispatch.dispatcher import receiver
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import conf
from django.db.models import Q
from .models import Profile, Message, Skill
from .forms import CustomUserCreationForm, ProfileForm, SkillForm, MessageForm
from .utils import recommendation, searchProfiles, paginateProfiles, get_dataset
import pandas as pd
from projects.models import Project

def loginUser(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('profiles')

    if request.method == 'POST':
        username = request.POST['username'].lower()
        password = request.POST['password']

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'Username does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET['next'] if 'next' in request.GET else 'account')

        else:
            messages.error(request, 'Username OR password is incorrect')

    return render(request, 'users/login_register.html')


def logoutUser(request):
    logout(request)
    messages.info(request, 'User was logged out!')
    return redirect('login')


def registerUser(request):
    page = 'register'
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()

            messages.success(request, 'User account was created!')

            login(request, user)
            return redirect('edit-account')

        else:
            messages.success(
                request, 'An error has occurred during registration')

    context = {'page': page, 'form': form}
    return render(request, 'users/login_register.html', context)


def profiles(request):
    profiles, search_query = searchProfiles(request)
    # print(profiles)
    custom_range, profiles = paginateProfiles(request, profiles, 6)
    try:
        current_user = Profile.objects.get(user_id = request.user.id)
    except:
        current_user = None
    context = {'profiles': profiles, 'search_query': search_query,
               'custom_range': custom_range , 'current_user': current_user}
    

    # print(request.user.id)
    # print(Profile.objects.get(user_id = request.user.id))
    
    return render(request, 'users/profiles.html', context)

def recommend(request,pk):
    dataset = get_dataset(request)
    print("The dataset is:", dataset)
    current_userr = {}
    curr_user_profile = Profile.objects.get(id = pk)
    curr_skills = Skill.objects.filter(owner = pk)
    current_userr['Name'] = [curr_user_profile.name]
    user_skillset = []
    for skilll in curr_skills:
        user_skillset.append(skilll.name)
    print(user_skillset)
    final_skillset = ", ".join(user_skillset)
    # current_userr['Skills'] = [final_skillset]

    bio = curr_user_profile.bio
    short_intro = curr_user_profile.short_intro
    description = bio + " " + short_intro
    current_userr['Description'] = [description]
    current_userr['Skills'] = [final_skillset]
    current_userr['Location'] = [curr_user_profile.location]

    myproj = Project.objects.filter(owner = pk)
    curr_user_projects = []
    for proj in myproj:
        curr_user_projects.append(proj.title)
    curr_user_proj = ", ".join(curr_user_projects)
    current_userr['Projects'] = [curr_user_proj]

    print("*****************************************")
    print(current_userr)

    current_user_data = {'Name': ['Syed Khundmir Azmi'],
             'Description': ['A motivated individual looking for an opportunity in Data Science with full end to end development practical knowledge'],
              'Skills': ['Python, Java'],
              'Projects': ['Customer Churn Prediction, SMS Spam Prediction'],
              'Location': ['Hyderabad, India']
             }
    
    # print(pd.DataFrame(recommendation(current_user_data, dataset)))
    df =  pd.DataFrame(recommendation(current_userr, dataset))
    print("DataFrame Is:")
    print(df)
    myprofiles = recommendation(current_userr, dataset)
    # print(myprofiles)
    query = []
    current_user = Profile.objects.get(user_id = request.user.id)
    for unique_id in myprofiles:
        
        myquery = Profile.objects.get(id = unique_id)
        if myquery.id != current_user.id:
            query.append(myquery.id)
        
    my_profiles = Profile.objects.filter(id__in = query)
           

    custom_range, profiles = paginateProfiles(request, my_profiles, 3)

    
    print(my_profiles)
    return render(request, 'users/recommendations.html', context={"profiles": profiles})

def userProfile(request, pk):
    profile = Profile.objects.get(id=pk)

    topSkills = profile.skill_set.exclude(description__exact="")
    otherSkills = profile.skill_set.filter(description="")

    context = {'profile': profile, 'topSkills': topSkills,
               "otherSkills": otherSkills}
    return render(request, 'users/user-profile.html', context)


@login_required(login_url='login')
def userAccount(request):
    profile = request.user.profile

    skills = profile.skill_set.all()
    projects = profile.project_set.all()

    context = {'profile': profile, 'skills': skills, 'projects': projects}
    return render(request, 'users/account.html', context)


@login_required(login_url='login')
def editAccount(request):
    profile = request.user.profile
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()

            return redirect('account')

    context = {'form': form}
    return render(request, 'users/profile_form.html', context)


@login_required(login_url='login')
def createSkill(request):
    profile = request.user.profile
    form = SkillForm()

    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.owner = profile
            skill.save()
            messages.success(request, 'Skill was added successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def updateSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    form = SkillForm(instance=skill)

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill was updated successfully!')
            return redirect('account')

    context = {'form': form}
    return render(request, 'users/skill_form.html', context)


@login_required(login_url='login')
def deleteSkill(request, pk):
    profile = request.user.profile
    skill = profile.skill_set.get(id=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, 'Skill was deleted successfully!')
        return redirect('account')

    context = {'object': skill}
    return render(request, 'delete_template.html', context)


@login_required(login_url='login')
def inbox(request):
    profile = request.user.profile
    messageRequests = profile.messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    context = {'messageRequests': messageRequests, 'unreadCount': unreadCount}
    return render(request, 'users/inbox.html', context)


@login_required(login_url='login')
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read == False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'users/message.html', context)


def createMessage(request, pk):
    recipient = Profile.objects.get(id=pk)
    form = MessageForm()

    try:
        sender = request.user.profile
    except:
        sender = None

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = sender
            message.recipient = recipient

            if sender:
                message.name = sender.name
                message.email = sender.email
            message.save()

            messages.success(request, 'Your message was successfully sent!')
            return redirect('user-profile', pk=recipient.id)

    context = {'recipient': recipient, 'form': form}
    return render(request, 'users/message_form.html', context)
