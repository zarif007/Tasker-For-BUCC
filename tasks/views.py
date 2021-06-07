import random
import string

from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

from .forms import CustomUserCreationForm, TaskApplyModelForm, TaskModelForm
from .models import Task, User


def home_page(request):
    return render(request, 'home_page.html')


@login_required(login_url='/signin')
def task_listings(request):
    
    task = Task.objects.all().order_by('last_date').filter(assign_status=1)
    av_task = Task.objects.all().order_by('last_date').filter(assign_status=0)
    paginator = Paginator(task, 6)
    page = request.GET.get('page')
    paged_listings = paginator.get_page(page)
    users = User.objects.all()

    context = {
        'users' : users,
        'tasks' : paged_listings,
        'av_tasks' : av_task
    }

    return render(request, 'task_listings.html', context)


def task_detail(request, pk):

    task = Task.objects.get(id=pk)

    context = {
        'task' : task
    }

    return render(request, 'task_details.html', context)


def task_history(request):

    task = Task.objects.all().order_by('last_date')
    users = User.objects.all()
    paginator = Paginator(task, 10)
    page = request.GET.get('page')
    paged_listings = paginator.get_page(page)

    context = {
        'users' : users,
        'tasks' : paged_listings,
    }

    return render(request, 'task_history.html', context)


def generate_unique_code():
    length = 6

    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if Task.objects.filter(code=code).count() == 0:
            break

    return code


def task_creation(request):
    
    users = User.objects.all()
    form = TaskModelForm()
    code = generate_unique_code()

    if request.method == 'POST':
        form = TaskModelForm(request.POST)
        
        if form.is_valid():
            form.save()

            if form.cleaned_data['assign_status']:
                user_name = form.cleaned_data['member']
                user = User.objects.get(in_club_name=user_name)
                user.hr_points = user.hr_points + 50
                user.save()
                domain = get_current_site(request).domain
                code = form.cleaned_data['code']
                task_id = Task.objects.get(code=code).id
                task_url = f'http://{domain + "/task/" + str(task_id) }'

                if(user.email != '' or form.cleaned_data['assign_status']):
                    send_mail(
                        subject='TaskManager: You have been assinged to a new task',
                        message=f'You have assinged to {form.cleaned_data["task_name"]}, click {task_url} to view',
                        from_email='djtester321@gmail.com', 
                        recipient_list=[user.email, 'zarifhuq007@gmail.com']
                    )
            
            
            
            return redirect('task_listings')
          
    context = {
        'forms': TaskModelForm(),
        'users': users,
        'code': code
    }

    return render(request, 'task_creation.html', context)


def task_update(request, pk):

    task = Task.objects.get(id=pk)

    users = User.objects.all()

    form = TaskModelForm(instance=task)

    prev_task_member = task.member
    
    if request.method == 'POST':
        form = TaskModelForm(request.POST, instance=task)

        if form.is_valid():
            form.save()

            user_name = form.cleaned_data['member']
            if form.cleaned_data['assign_status'] or prev_task_member != user_name:
                
                user = User.objects.get(in_club_name=user_name)
                user.hr_points = user.hr_points + 50
                user.save()
                print(user.hr_points)
                domain = get_current_site(request).domain
                task_id = Task.objects.get(code=task.code).id
                task_url = f'http://{domain + "/task/" + str(task_id) }'

                if(user.email != '' or prev_task_member != user_name):
                    send_mail(
                        subject='TaskManager: You have been assinged to a new task',
                        message=f'You have assinged to {form.cleaned_data["task_name"]}, click {task_url} to view',
                        from_email='djtester321@gmail.com', 
                        recipient_list=[user.email, 'zarifhuq007@gmail.com']
                    )
                
            return redirect('task_detail', task.id)

    context = {
        'task' : task,
        'form' : form,
        'users' : users,
    }

    return render(request, 'task_update.html', context)


def task_delete(request, pk):
    task = Task.objects.get(id=pk)
    task.delete()

    return redirect('task_listings')


def task_apply(request, pk):

    task = Task.objects.get(id=pk)

    users = User.objects.all()

    form = TaskApplyModelForm(instance=task)

    
    if request.method == 'POST':
        form = TaskApplyModelForm(request.POST, instance=task)
        
        if form.is_valid():
            form.save()

            if form.cleaned_data['assign_status']:
                user_name = form.cleaned_data['member']
                user = User.objects.get(in_club_name=user_name)

                domain = get_current_site(request).domain
                task_id = Task.objects.get(code=task.code).id
                task_url = f'http://{domain + "/task/" + str(task_id) }'
                print(task_id)
                if(user.email != ''):
                    send_mail(
                        subject='TaskManager: You have been assinged to a new task',
                        message=f'You have applied for {task.task_name}, click {task_url} to view',
                        from_email='djtester321@gmail.com', 
                        recipient_list=[user.email, 'zarifhuq007@gmail.com']
                    )
 
            return redirect('task_detail', task.id)

    context = {
        'users': users,
        'form': form,
        'task': task,
    }

    return render(request, 'task_apply.html', context)


class SignUpView(generic.CreateView):
    template_name = 'registration/signup.html'
    form_class = CustomUserCreationForm

    def get_success_url(self):
        return reverse('task_listings')


def user_profile(request, pk):

    user = User.objects.get(id=pk)

    task = Task.objects.filter(member=pk)

    context = {
        'user'  : user,
        'tasks' : task,
        'len_of_task' : len(task),
    }
    return render(request, 'user/user_profile.html', context)