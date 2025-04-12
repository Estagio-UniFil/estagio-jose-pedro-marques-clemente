from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    @property
    def estoque_total(self):
        """Retorna a soma de todos os itens, mesmo com quantidade zero"""
        return sum(item.quantidade for item in self.item_set.all())
    
    @property
    def estoque_disponivel(self):
        """Retorna apenas itens com quantidade positiva"""
        return sum(item.quantidade for item in self.item_set.filter(quantidade__gt=0))

    def __str__(self):
        return f"{self.nome} (Estoque: {self.estoque_disponivel})"

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

class Item(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    lote = models.CharField(max_length=50)
    data_validade = models.DateField(blank=True, null=True)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def clean(self):
        """Validação para quantidade não negativa"""
        if self.quantidade < 0:
            raise ValidationError("Quantidade não pode ser negativa")

    def __str__(self):
        return f"{self.produto.nome} - Lote: {self.lote} (Qtd: {self.quantidade})"

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        constraints = [
            models.UniqueConstraint(
                fields=['produto', 'lote'],
                name='unique_produto_lote'
            )
        ]

class TipoTransacao(models.Model):
    nome = models.CharField(max_length=50)
    descricao = models.TextField(blank=True, null=True)
    entrada = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = 'Tipo de Transação'
        verbose_name_plural = 'Tipos de Transação'


class Transacao(models.Model):
    data = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    tipo = models.ForeignKey(TipoTransacao, on_delete=models.PROTECT)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transação #{self.id} - {self.tipo.nome} - {self.data.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-data']

class ItemTransacao(models.Model):
    transacao = models.ForeignKey(Transacao, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)

    def clean(self):
        """
        Validações:
        1. Não permite saída maior que o estoque disponível
        2. Garante que quantidade seja positiva
        """
        if self.quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        
        if not self.transacao.tipo.entrada and self.quantidade > self.item.quantidade:
            raise ValidationError(f"Quantidade indisponível em estoque (Disponível: {self.item.quantidade})")

    def save(self, *args, **kwargs):
        """
        Atualiza o estoque do item quando uma transação é salva
        """
        if not self.pk:  # Nova instância
            self.clean()  # Executa as validações
            
            if self.transacao.tipo.entrada:
                self.item.quantidade += self.quantidade
            else:
                self.item.quantidade -= self.quantidade
            
            self.item.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantidade} x {self.item.produto.nome}"

    class Meta:
        verbose_name = 'Item de Transação'
        verbose_name_plural = 'Itens de Transação'