from django.contrib import admin
from django.urls import include, path
from todos import views # Importiamo views per la pagina di signup

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('todos.urls')),
    
    # --- QUESTE SONO LE DUE RIGHE NUOVE ---
    path('accounts/', include('django.contrib.auth.urls')), # Gestisce login/logout
    path('signup/', views.signup, name='signup'), # Gestisce la registrazione
]
