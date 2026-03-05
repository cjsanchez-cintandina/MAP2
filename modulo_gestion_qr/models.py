import uuid
import re

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify





class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    codigo_cliente = models.CharField(max_length=20, unique=True, default="")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super(Cliente, self).save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_producto = models.CharField(max_length=20, unique=True, null=True, blank=True)
    descripcion_producto = models.TextField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)

    # Relación con TemplateCliente
    template = models.ForeignKey("TemplateCliente", on_delete=models.SET_NULL, null=True, blank=True)  # ← Evita import circular

    # Nombres de los campos adicionales
    nombre_campo1 = models.CharField(max_length=100, blank=True, null=True)
    nombre_campo2 = models.CharField(max_length=100, blank=True, null=True)
    nombre_campo3 = models.CharField(max_length=100, blank=True, null=True)
    nombre_campo4 = models.CharField(max_length=100, blank=True, null=True)
    nombre_campo5 = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo_producto})"

# models.py
class Serial(models.Model):
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_proceso', 'En Proceso'),
        ('despachado', 'Despachado - listo para distribución'),
        ('distribucion', 'Distribución'),
        ('cancelado', 'Cancelado'),
    ]

    serial = models.CharField(max_length=100, unique=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    url = models.URLField(max_length=500, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programado')

    # Campos extra
    campo1 = models.TextField(blank=True, null=True)
    campo2 = models.TextField(blank=True, null=True)
    campo3 = models.TextField(blank=True, null=True)
    campo4 = models.TextField(blank=True, null=True)
    campo5 = models.TextField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    solicitud = models.ForeignKey('Solicitud', on_delete=models.SET_NULL, null=True, blank=True, related_name='seriales_qr')

    # ⬇️ Nuevo: límite por serial (override, independiente de Solicitud)
    max_entregas = models.PositiveIntegerField(default=544)  # arranca en 50

    def __str__(self):
        return self.serial



class TemplateCliente(models.Model):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="templates"
    )
    nombre = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_.-]+$',
                message="El nombre solo puede contener letras, números, puntos (.), guiones bajos (_) y guiones (-).",
                code='invalid_nombre'
            )
        ],
        help_text="Ejemplo: producto_template1.html"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, help_text="Indica si este template está en uso")

    class Meta:
        ordering = ['-fecha_creacion']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'nombre'],
                name='uniq_template_por_cliente_y_nombre'
            )
        ]

    def __str__(self):
        return f"{self.nombre} (Cliente: {self.cliente.nombre})"


# En modulo_gestion_qr/models.py
class Solicitud(models.Model):
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    logo = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)
    sobre_nosotros = models.TextField(blank=True)
    razon_social = models.CharField(max_length=255)
    nit = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    celular = models.CharField(max_length=50, blank=True)
    correo = models.EmailField()
    pagina_web = models.URLField(blank=True)
    link_adicional = models.URLField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # ← nuevo
    mostrar_boton_entrega = models.BooleanField(
        default=False,
        verbose_name="Mostrar botón de confirmar entrega")
    acepta_tratamiento_datos = models.BooleanField(
        default=False,
        verbose_name="Acepta tratamiento de datos")

    
    def save(self, *args, **kwargs):
        if not self.codigo:
            import uuid
            self.codigo = f"CI{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Solicitud {self.codigo}"

    @property
    def logo_url(self):
        if self.logo:
            return self.logo.url
        return f"{settings.STATIC_URL}images/default.png"
    
    def celular_internacional(self): #SE AGREGA ESTE BLOQUE PARA  FORZAR EL FORMATO DE WHATS APP +57
        if not self.celular:
            return None

        # Solo números
        numero = re.sub(r'\D', '', self.celular)

        # Quitar 57 si ya viene
        if numero.startswith('57'):
            numero = numero[2:]

        # Validar longitud Colombia
        if len(numero) == 10:
            return f'+57{numero}'

        return None  # número inválido



# models.py
class Entrega(models.Model):
    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name='entregas')

    serial = models.ForeignKey(
        "Serial",
        on_delete=models.CASCADE,
        related_name='entregas',
        null=True,
        blank=True
    )

    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    foto = models.ImageField(upload_to='entregas/fotos/')
    firma = models.ImageField(upload_to='entregas/firmas/')
    fecha_entrega = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.serial:
            return f'Entrega {self.serial.serial} - {self.nombre}'
        return f'Entrega sin Serial - {self.nombre}'



class Ubicacion(models.Model):
    solicitud = models.ForeignKey(
        'Solicitud',
        on_delete=models.CASCADE,
        related_name='ubicaciones'
    )
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.direccion} - {self.ciudad}"
    

# Modelo de roles
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

# Modelo de usuario personalizado
class User(AbstractUser):
    roles = models.ManyToManyField(Rol, blank=True, related_name="usuarios")

    groups = models.ManyToManyField(
        Group,
        related_name="modulo_gestion_qr_users",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="modulo_gestion_qr_users_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def has_rol(self, rol_name):
        """Verifica si el usuario tiene un rol específico."""
        return self.roles.filter(nombre=rol_name).exists()

    def is_admin(self):
        """Verifica si el usuario es administrador."""
        return self.is_superuser or self.has_rol('Administrador')


