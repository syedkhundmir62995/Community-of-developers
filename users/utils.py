from django.db.models import Q
from .models import Profile, Skill
from projects.models import Project
import pandas as pd

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginateProfiles(request, profiles, results):
    page = request.GET.get('page')
    paginator = Paginator(profiles, results)

    try:
        profiles = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        profiles = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        profiles = paginator.page(page)

    leftIndex = (int(page) - 4)

    if leftIndex < 1:
        leftIndex = 1

    rightIndex = (int(page) + 5)

    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages + 1

    custom_range = range(leftIndex, rightIndex)

    return custom_range, profiles


def searchProfiles(request):
    search_query = ''

    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')
        print("seacrch query is: ",search_query)
    skills = Skill.objects.filter(name__icontains=search_query)

    profiles = Profile.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(short_intro__icontains=search_query) |
        Q(skill__in=skills)
    )

    return profiles, search_query

# Write logic for extracting recommended profiles from the database
def get_dataset(request):
    
    profile_data = Profile.objects.all()
    u_id = []
    name = []
    description = []
    location = []
    skills  = []
    projects = []
    
    for profile in profile_data:
        u_id.append(profile.id)
        name.append(profile.name)
        bio = profile.bio
        short_intro = profile.short_intro

        descrip = short_intro + " " + bio
        
        description.append(descrip)
        location.append(profile.location)

        project_data = Project.objects.filter(id = profile.id)
        
        project_list = []
        for project in project_data:
            project_list.append(project)
        
        project_names = ", ".join(project_list)

        projects.append(project_names)

        skills_data = Skill.objects.filter(owner_id = profile.id)

        skills_list = []
        for skill in skills_data:
            skills_list.append(skill.name)
        
        if skills_list:
            # print('Hello', skills_list)
            skillset = ", ".join(skills_list)

        skills.append(skillset)

        

        data = {"Uid": u_id,"Name": name, "Description": description, "Skills": skills, "Projects": projects, "Location":location}
    
    df = pd.DataFrame(data)
    # print(df)
    return df


def extract_skills(skills):
    words = skills.split(" ")
    processed_words = []
    for word in words:
        if word not in [',', '(', ')', '-', '.']:
            processed_words.append(word)
    return processed_words

def extract_projects(projects):
    L = []
    getting_project = ""
    for project in projects:
        if ord(project) == 32: #this is for space
            getting_project+=project
            continue
        if ord(project) == 44:  #this is for coma
            
            L.append(getting_project.lower().strip())
            getting_project = ""
        else:
            getting_project+=project
    else:
        L.append(getting_project.lower().strip())
    
    return L

# Now we will work on Location column
def extract_location(locations):
    L = []
    getting_location = ""
    for location in locations:
        if ord(location) == 32: #this is for space
            getting_location+=location
            continue
        if ord(location) == 44:  #this is for coma
            getting_location = getting_location.replace(" ", "")
            L.append(getting_location.lower().strip())
            getting_location = ""
        else:
            getting_location+=location
    else:
        getting_location = getting_location.replace(" ", "")
        L.append(getting_location.lower().strip())
    
    return L
    
def extract_description(description):
    words = description.split(" ")
    processed_words = []
    for word in words:
        if word not in ['(', ')', ',', '.',':',' ']:
            word = word.lower()
            
            processed_words.append(word)
    return processed_words       

def recommendation(json_data, dataframe):
    
    data = pd.DataFrame(data = json_data)
    print("Hellooo", data)
    ref_df = pd.concat([dataframe, data], axis = 0)
    data_df = pd.concat([dataframe, data], axis = 0)
    data_df['Skills'] = data_df['Skills'].apply(extract_skills)
    data_df['Projects'] = data_df['Projects'].apply(extract_projects)
    data_df['Location'] = data_df['Location'].apply(extract_location)
    data_df['Description'] = data_df['Description'].apply(extract_description)
    data_df['tags'] = data_df['Description'] + data_df['Skills'] + data_df['Projects'] + data_df['Location']
    data_df['tags'] = data_df['tags'].apply(lambda x: " ".join(x))
    
    # print(data_df)
    #Applying Bag of Words
    from sklearn.feature_extraction.text import CountVectorizer
    cv1 = CountVectorizer(max_features = 1000)
    vector = cv1.fit_transform(data_df['tags']).toarray()
    vector = pd.DataFrame(data = vector, columns=cv1.get_feature_names())
    
    # print(data_df['tags'])

    # Applying Cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity

    intended_record = data_df.shape[0] -1
    # print(intended_record)
    similarity = pd.DataFrame(cosine_similarity(vector))
    similar_records = similarity.iloc[intended_record].sort_values(ascending = False)[2:8]
    print("SImilar records are: ",similar_records)
    u_id = []
    Names = []
    Description = []
    Skills = []
    Projects = []
    Location = []

    final_dict = {}
    for index in similar_records.index:
      
        d = ref_df.iloc[index].to_dict()
        u_id.append(d['Uid'])
        
        Names.append(d['Name'].title())
        Description.append(d['Description'].title())
        Skills.append(d['Skills'].title())
        Projects.append(d['Projects'].title())
        Location.append(d['Location'].title())
        similar_records_dict = {"Uid":u_id,"Name": Names, "Description": Description, "Skills": Skills, "Projects": Projects, "Location": Location}
        final_dict.update(similar_records_dict)
    return u_id
    



    
