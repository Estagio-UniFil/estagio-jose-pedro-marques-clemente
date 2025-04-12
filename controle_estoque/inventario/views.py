from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from .forms import CadastroUsuarioForm, CategoriaForm, ProdutoForm
from .models import Produto, Categoria

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('/produtos/')  # Change this to your desired logged-in page
    else:
        return redirect('/login/')

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('listar_produtos')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {username}!')
                next_url = request.GET.get('next', 'listar_produtos')
                return redirect(next_url)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm()

    return render(request, 'usuario/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('login')

@require_http_methods(["GET", "POST"])
def cadastro_usuario_view(request):
    if request.user.is_authenticated:
        return redirect('listar_produtos')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada com sucesso para {username}!')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = CadastroUsuarioForm()

    return render(request, 'usuario/cadastro.html', {'form': form})

def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(email=data)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Redefinição de Senha - Atec Estoque"
                    email_template_name = "usuario/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': request.get_host(),
                        'site_name': 'Inventário',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'https' if request.is_secure() else 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(
                            subject,
                            email,
                            os.getenv('EMAIL_HOST_USER'),  # Usa o email do .env
                            [user.email],
                            fail_silently=False
                        )
                        messages.success(request, 'Email enviado com sucesso! Verifique sua caixa de entrada.')
                        return redirect('password_reset_done')
                    except Exception as e:
                        messages.error(request, f"""Erro no envio: {str(e)}. Verifique:
                            1. Configurações no .env
                            2. Senha de App no Google
                            3. Conexão com internet""")
                        return redirect('password_reset')
            else:
                messages.error(request, 'Este email não está cadastrado.')
    else:
        password_reset_form = PasswordResetForm()
    
    return render(
        request=request, 
        template_name="usuario/password_reset.html",
        context={"password_reset_form": password_reset_form}
    )


def listar_categorias(request):
    categorias = Categoria.objects.all()
    
    busca = request.GET.get('busca')
    if busca:
        categorias = categorias.filter(nome__icontains=busca)
    
    context = {
        'categorias': categorias,
    }
    return render(request, 'categoria/listar.html', context)

def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
            return redirect('listar_categorias')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = CategoriaForm()
    
    context = {'form': form}
    return render(request, 'categoria/form.html', context)

def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(categoria).pk,
                object_id=categoria.id,
                object_repr=str(categoria),
                action_flag=ADDITION,
                change_message='Categoria criada'
            )
            categoria = form.save()
            messages.success(request, f'Categoria "{categoria.nome}" atualizada com sucesso!')
            return redirect('listar_categorias')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = CategoriaForm(instance=categoria)
    
    context = {
        'form': form,
        'categoria': categoria,
    }
    return render(request, 'categoria/form.html', context)

def excluir_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    produtos_vinculados = categoria.produto_set.exists()
    
    if produtos_vinculados:
        messages.error(request, f'Não é possível excluir a categoria "{categoria.nome}" porque existem produtos vinculados a ela.')
        return redirect('listar_categorias')
    
    if request.method == 'POST':
        nome_categoria = categoria.nome
        categoria.delete()
        messages.success(request, f'Categoria "{nome_categoria}" excluída com sucesso!')
        return redirect('listar_categorias')
    
    context = {'categoria': categoria}
    return render(request, 'categoria/confirmar_exclusao.html', context)

@login_required
def listar_produtos(request):
    produtos = Produto.objects.all().select_related('categoria')
    
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)
    
    busca = request.GET.get('busca')
    if busca:
        produtos = produtos.filter(nome__icontains=busca)
    
    paginator = Paginator(produtos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
                                  
    context = {
        'produtos': produtos,
        'categorias': Categoria.objects.all,
        'page_obj': page_obj,
    }
    return render(request, 'produto/listar.html', context)

@login_required
def criar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" criado com sucesso!')
            return redirect('listar_produtos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ProdutoForm()
    
    context = {'form': form}
    return render(request, 'produto/form.html', context)

@login_required
def editar_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(produto).pk,
                object_id=produto.id,
                object_repr=str(produto),
                action_flag=ADDITION,
                change_message='Produto criado'
            )
            produto = form.save()
            messages.success(request, f'Produto "{produto.nome}" atualizado com sucesso!')
            return redirect('listar_produtos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ProdutoForm(instance=produto)
    
    context = {
        'form': form,
        'produto': produto,
    }
    return render(request, 'produto/form.html', context)

@login_required
def excluir_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        nome_produto = produto.nome
        produto.delete()
        messages.success(request, f'Produto "{nome_produto}" excluído com sucesso!')
        return redirect('listar_produtos')
    
    context = {'produto': produto}
    return render(request, 'produto/confirmar_exclusao.html', context)