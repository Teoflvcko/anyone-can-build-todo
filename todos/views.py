from django.shortcuts import render, redirect, get_object_or_404
from .models import Todo
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def todo_list(request):
    todos = Todo.objects.all()
    return render(request, 'todos/todo_list.html', {'todos': todos})

def todo_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        # ECCO LA MAGIA: ora prende la categoria e la salva!
        category = request.POST.get('category', '')
        if title:
            Todo.objects.create(title=title, category=category)
    return redirect('/')

def todo_toggle(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk)
        todo.done = not todo.done
        todo.save()
    return redirect('/')

def todo_delete(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk)
        todo.delete()
    return redirect('/')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
