from django.urls import path

from . import api
from . import server


urlpatterns = [
    path('createRoom/<slug:name>/', api.createRoom),
    path('joinRoom/<slug:name>/', api.joinRoom),
    path('completeRoom/<slug:name>/', api.completeRoom),
    path('workflow/<slug:name>/', api.workflow),
    path('getToken/<slug:room>/', api.getToken),
    path('socket/', server.handler),
]