import logging

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import (
    Cliente,
    Entrega,
    Producto,
    Rol,
    Serial,
    Solicitud,
    TemplateCliente,
    Ubicacion,
    User,
)

logger = logging.getLogger("storages")



# Registrar roles
admin.site.register(Rol)

# Admin personalizado para el modelo User
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'is_staff', 'is_active', 'is_superuser', 'get_roles')
    fieldsets = UserAdmin.fieldsets + (
        ('Roles', {'fields': ('roles',)}),
    )
    filter_horizontal = ('roles', 'groups', 'user_permissions')

    def get_roles(self, obj):
        """Devuelve una lista de roles asignados al usuario."""
        return ", ".join([r.nombre for r in obj.roles.all()])
    get_roles.short_description = 'Roles'

# Registrar el modelo User con CustomUserAdmin
admin.site.register(User, CustomUserAdmin)

# Clientes
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

# Productos
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

# Seriales
@admin.register(Serial)
class SerialAdmin(admin.ModelAdmin):
    list_display = ('serial', 'cliente', 'producto', 'url')
    search_fields = ('serial',)
    list_filter = ('cliente', 'producto')


@admin.register(TemplateCliente)
class TemplateClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cliente', 'fecha_creacion', 'activo')  # Columnas en la lista
    list_filter = ('activo', 'fecha_creacion')  # Filtros en la barra lateral
    search_fields = ('nombre', 'cliente__nombre')  # Búsqueda por nombre y cliente
    ordering = ('-fecha_creacion',)  # Ordenación por fecha de creación
    list_editable = ('activo',)  # Permite editar el campo activo desde la lista
    date_hierarchy = 'fecha_creacion'  # Navegación por fechas en la parte superior



# Solicitudes
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'razon_social', 'nit', 'correo', 'fecha_creacion')
    search_fields = ('codigo', 'razon_social', 'nit', 'correo')
    list_filter = ('fecha_creacion',)
    fields = ('codigo', 'logo', 'razon_social', 'nit', 'correo',
    'pagina_web', 'link_adicional', 'sobre_nosotros',
    'mostrar_boton_entrega',
    'acepta_tratamiento_datos',)

    def save_model(self, request, obj, form, change):
        try:
            logger.debug(f"Guardando solicitud desde admin: {obj.codigo}, Archivo: {form.cleaned_data.get('logo')}")
            super().save_model(request, obj, form, change)
            logger.debug(f"Solicitud guardada: {obj.codigo}, Logo URL: {obj.logo.url if obj.logo else 'No logo'}")
        except Exception as e:
            logger.error(f"Error al guardar solicitud en admin: {e}")
            messages.error(request, f"Error al guardar la solicitud: {e}")
            raise



@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('direccion', 'ciudad', 'telefono', 'solicitud')
    list_filter = ('ciudad'),
    search_fields = ('direccion', 'ciudad', 'telefono', 'solicitud__id')
    ordering = ('ciudad',)


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('get_serial', 'nombre', 'correo', 'telefono', 'fecha_entrega')
    list_filter = ('fecha_entrega',)
    search_fields = ('serial__serial', 'nombre', 'correo', 'telefono')
    readonly_fields = ('foto', 'firma', 'fecha_entrega')

    def get_serial(self, obj):
        return obj.serial.serial if obj.serial else "Sin serial"
    get_serial.short_description = 'Serial'



