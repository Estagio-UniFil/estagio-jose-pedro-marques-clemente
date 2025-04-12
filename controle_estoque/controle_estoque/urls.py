from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from inventario.views import (
    cadastro_usuario_view, 
    criar_categoria, 
    criar_produto, 
    editar_categoria, 
    editar_produto, 
    excluir_categoria, 
    excluir_produto, 
    listar_categorias, 
    listar_produtos, 
    login_view, 
    logout_view,
    password_reset_request,
    root_redirect
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_redirect, name='root-redirect'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('cadastro/', cadastro_usuario_view, name='cadastro'),
    path('produtos/', listar_produtos, name='listar_produtos'),
    path('produtos/novo/', criar_produto, name='criar_produto'),
    path('produtos/editar/<int:pk>/', editar_produto, name='editar_produto'),
    path('produtos/excluir/<int:pk>/', excluir_produto, name='excluir_produto'),
    path('categorias/', listar_categorias, name='listar_categorias'),
    path('categorias/novo/', criar_categoria, name='criar_categoria'),
    path('categorias/editar/<int:pk>/', editar_categoria, name='editar_categoria'),
    path('categorias/excluir/<int:pk>/', excluir_categoria, name='excluir_categoria'),
    
    # URLs para recuperação de senha (adicionadas aqui)
    path('password_reset/', password_reset_request, name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='usuario/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='usuario/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='usuario/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]