"""URL generali del progetto: admin, app rentals, login, logout e registrazione."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from rentals import views


# URL principali del progetto: admin tecnico, app rentals e pagine auth.
urlpatterns = [
    # Django Admin rimane separato dal pannello gestore realizzato nell'app.
    path("admin/", admin.site.urls),
    # Le pagine principali del noleggio sono definite nell'app rentals.
    path("", include("rentals.urls")),
    path("registrazione/", views.registrazione, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    # In sviluppo Django serve direttamente le immagini caricate.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
