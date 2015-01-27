
from django.shortcuts import render_to_response, redirect, render
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
from django.http import HttpResponse
from django.contrib.auth.models import User

from rest_framework import mixins, generics, permissions, parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from social.apps.django_app.utils import strategy
from social.apps.django_app.utils import psa

from .models import Snippet
from .serializers import SnippetSerializer, UserSerializer
from .permissions import IsOwnerOrReadOnly


def login(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password'])
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect(
                    request.GET['next'] if request.GET.get(
                        'next', None) else '/'
                )
            else:
                return HttpResponse('disabled account')
        else:
            return HttpResponse('invalid login')
    else:
        context = RequestContext(request, {
            'request': request, 'user': request.user})
    return render_to_response('login.html', context_instance=context)


@login_required(login_url='/')
def home(request):
    return render_to_response('home.html')


def logout(request):
    auth_logout(request)
    return redirect('/')


class SnippetList(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):

    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SnippetDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):

    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (
        parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    model = Token

    # Accept backend as a parameter and 'auth' for a login / pass
    def post(self, request, backend):
        serializer = self.serializer_class(data=request.DATA)

        if backend == 'auth':
            if serializer.is_valid():
                token, created = Token.objects.get_or_create(
                    user=serializer.validated_data['user'])
                return Response({'token': token.key})
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Here we call PSA to authenticate like we would if we used PSA on
            # server side.
            user = register_by_access_token(request, backend)

            # If user is active we get or create the REST token and send it
            # back with user data
            if user and user.is_active:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'id': user.id,
                    'name': user.username,
                    'userRole': 'user',
                    'token': token.key})


@psa('social:complete')
def register_by_access_token(request, backend):
    backend = request.backend
    # Split by spaces and get the array
    token = request.META['HTTP_AUTHORIZATION']
    # auth = get_authorization_header(request).split()

    # if not auth or auth[0].lower() != b'token':
    #     msg = 'No token header provided.'
    #     return msg

    # if len(auth) == 1:
    #     msg = 'Invalid token header. No credentials provided.'
    #     return msg

    # access_token = auth[1]
    # Real authentication takes place here
    user = backend.do_auth(token)

    return user
