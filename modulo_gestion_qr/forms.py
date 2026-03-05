import os
import re

from functools import lru_cache
from fnmatch import fnmatch

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory

from .models import Cliente, Entrega, Producto, Serial, Solicitud, TemplateCliente, Ubicacion





class SerialForm(forms.Form):
    numero_seriales = forms.IntegerField(label='Número de seriales', min_value=1)
    cliente = forms.ModelChoiceField(queryset=Cliente.objects.all(), label='Cliente')
    producto = forms.ModelChoiceField(queryset=Producto.objects.none(), label='Producto')

    def __init__(self, *args, **kwargs):
        cliente_id = kwargs.pop('cliente_id', None)  # Recibe el cliente seleccionado si está disponible
        super().__init__(*args, **kwargs)
        if cliente_id:
            self.fields['producto'].queryset = Producto.objects.filter(cliente_id=cliente_id)




class ProductoForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=TemplateCliente.objects.none(),  # Inicialmente vacío
        label='Template',
        required=False
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'codigo_producto', 'descripcion_producto', 'cliente', 'template']

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all()

        # Si el producto ya existe, filtrar templates por el cliente asociado
        if self.instance and self.instance.pk:
            cliente = self.instance.cliente
            if cliente:
                self.fields['template'].queryset = TemplateCliente.objects.filter(cliente=cliente)




class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))




class AsociarSerialesForm(forms.Form):
    desde = forms.CharField(label='Serial inicial', max_length=100)
    hasta = forms.CharField(label='Serial final', max_length=100)
    solicitud = forms.ModelChoiceField(
        queryset=Solicitud.objects.all(),
        label='Solicitud',
        required=True,  
        widget=forms.Select(attrs={
            'class': 'block w-full p-2.5 text-sm rounded-lg border border-gray-300 focus:ring-green-500 focus:border-green-500',
        })
    )
    campo1 = forms.CharField(label='Campo 1', widget=forms.Textarea, required=False)
    campo2 = forms.CharField(label='Campo 2', widget=forms.Textarea, required=False)
    campo3 = forms.CharField(label='Campo 3', widget=forms.Textarea, required=False)
    campo4 = forms.CharField(label='Campo 4', widget=forms.Textarea, required=False)
    campo5 = forms.CharField(label='Campo 5', widget=forms.Textarea, required=False)
    
    estado = forms.ChoiceField(
        label='Estado',
        choices=Serial.ESTADO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'block w-full p-2.5 text-sm rounded-lg border border-gray-300 focus:ring-green-500 focus:border-green-500',
        })
    )



    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get("desde")
        hasta = cleaned_data.get("hasta")
        solicitud = cleaned_data.get("solicitud")

        if desde and hasta:
            # Validar que los seriales sean válidos
            try:
                # Convertir a enteros para comparar el rango
                desde_int = int(desde.lstrip('0') or '0')
                hasta_int = int(hasta.lstrip('0') or '0')
                if hasta_int < desde_int:
                    raise forms.ValidationError({
                        'hasta': "El valor 'Hasta' debe ser mayor o igual que 'Desde'."
                    })
            except ValueError:
                raise forms.ValidationError("Los seriales deben ser valores numéricos válidos.")

            # Calcular el número de seriales en el rango
            total_seriales_en_rango = (hasta_int - desde_int) + 1
            seriales_encontrados = Serial.objects.filter(
                serial__gte=desde, serial__lte=hasta
            ).count()

            if seriales_encontrados != total_seriales_en_rango:
                raise forms.ValidationError(
                    f"El rango especificado ({desde} - {hasta}) no es válido o contiene {seriales_encontrados} seriales en lugar de los {total_seriales_en_rango} esperados."
                )

        return cleaned_data



class ProductoUpdateForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'codigo_producto',
            'descripcion_producto',
            'cliente',
            'nombre_campo1',
            'nombre_campo2',
            'nombre_campo3',
            'nombre_campo4',
            'nombre_campo5',
        ]
        widgets = {
            'descripcion_producto': forms.Textarea(attrs={'rows': 3}),
        }



class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'codigo_producto', 'descripcion_producto', 
                  'cliente', 'nombre_campo1', 'nombre_campo2', 'nombre_campo3', 
                  'nombre_campo4', 'nombre_campo5']


class BuscarSerialesForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(), label="Cliente", empty_label="Seleccione un cliente"
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(), label="Producto", empty_label="Seleccione un producto"
    )

    def __init__(self, *args, **kwargs):
        # Capturar cliente_id si está disponible
        cliente_id = kwargs.pop('cliente_id', None)
        super().__init__(*args, **kwargs)

        # Inicializar productos si se ha seleccionado un cliente
        if cliente_id:
            self.fields['producto'].queryset = Producto.objects.filter(cliente_id=cliente_id)




# --- Descubrir .html recursivamente + filtrar por allowlist/blacklist ---
@lru_cache(maxsize=1)
def discover_templates_html_filtered():
    """
    Busca .html en:
      - settings.TEMPLATES[0]['DIRS'] (todas las subcarpetas)
      - templates/ de TU app (ajusta app_name)
    Aplica allowlist (LANDING_TEMPLATE_PATTERNS) y blacklist (LANDING_TEMPLATE_EXCLUDE).
    Devuelve rutas relativas tipo "landing.html" o "subcarpeta/landing.html".
    """
    encontrados = set()

    # 1) Directorios declarados en settings
    for base in settings.TEMPLATES[0].get('DIRS', []):
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for fname in files:
                    if fname.lower().endswith('.html'):
                        rel = os.path.relpath(os.path.join(root, fname), start=base)
                        rel = rel.replace(os.sep, '/')
                        encontrados.add(rel)

    # 2) templates/ de TU app
    app_name = 'modulo_gestion_qr'  # <-- cambia si tu app se llama distinto
    app_config = apps.get_app_config(app_name)
    tdir = os.path.join(app_config.path, 'templates')
    if os.path.isdir(tdir):
        for root, _, files in os.walk(tdir):
            for fname in files:
                if fname.lower().endswith('.html'):
                    rel = os.path.relpath(os.path.join(root, fname), start=tdir)
                    rel = rel.replace(os.sep, '/')
                    encontrados.add(rel)

    # --- Filtros ---
    allow_patterns = getattr(settings, 'LANDING_TEMPLATE_PATTERNS', None)
    exclude_names = set(getattr(settings, 'LANDING_TEMPLATE_EXCLUDE', []))

    def permitido(path_relativo: str) -> bool:
        base = path_relativo.split('/')[-1]  # nombre de archivo
        if base in exclude_names:
            return False
        if allow_patterns:
            # requiere que algún patrón de allowlist coincida con base o con la ruta relativa
            return any(fnmatch(base, pat) or fnmatch(path_relativo, pat) for pat in allow_patterns)
        # si no hay allowlist configurada, acepta todos los .html (menos excluidos)
        return True

    filtrados = sorted(p for p in encontrados if permitido(p))
    return filtrados


class TemplateClienteForm(forms.ModelForm):
    # nombre ahora es ChoiceField (select) con opciones dinámicas
    nombre = forms.ChoiceField(
        choices=[],
        label='Nombre del Template',
        help_text='Selecciona un template existente (archivo .html).'
    )

    class Meta:
        model = TemplateCliente
        fields = ['nombre', 'cliente']
        labels = {'cliente': 'Cliente Asociado'}
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'block w-full p-2.5 text-sm rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        templates = discover_templates_html_filtered()
        self.fields['nombre'].choices = [('', '— Selecciona un template —')] + [(t, t) for t in templates]
        self.fields['nombre'].widget.attrs.update({
            'class': 'block w-full p-2.5 text-sm rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500'
        })

    def clean_nombre(self):
        nombre = (self.cleaned_data.get('nombre') or '').strip()
        if not nombre:
            raise forms.ValidationError("Debes seleccionar un template.")
        # Permitimos subcarpetas y separadores
        if not re.fullmatch(r'^[a-zA-Z0-9_.\-/]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras, números, '/', '.', '_' y '-'.")
        if ".." in nombre or nombre.startswith(".") or nombre.endswith("."):
            raise forms.ValidationError("El nombre no puede contener múltiples puntos consecutivos ni empezar o terminar con un punto.")
        if not nombre.endswith(".html"):
            raise forms.ValidationError("El template debe terminar en '.html'.")
        return nombre


class SolicitudForm(forms.ModelForm):

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')

        if not celular:
            return celular

        numero = re.sub(r'\D', '', celular)

        if numero.startswith('57'):
            numero = numero[2:]

        if len(numero) != 10:
            raise forms.ValidationError(
                "El celular debe tener 10 dígitos (ej: 3001234567)"
            )

        return f'+57{numero}'


    def clean_nit(self):
        nit = self.cleaned_data.get("nit")

        if not nit:
            return nit

        nit = nit.strip()

        # Si tiene guión, tomar solo la parte izquierda
        if "-" in nit:
            nit = nit.split("-")[0]

        # Validar que sea numérico
        if not nit.isdigit():
            raise forms.ValidationError(
                "El NIT solo debe contener números."
            )

        return nit


    def clean_acepta_tratamiento_datos(self):
        value = self.cleaned_data.get("acepta_tratamiento_datos")
        if not value:
            raise forms.ValidationError(
                "Debes aceptar la política de tratamiento de datos."
            )
        return value
        
    class Meta:
        model = Solicitud
        fields = [
            'codigo', 'logo', 'sobre_nosotros', 'razon_social', 'nit',
            'correo', 'pagina_web', 'link_adicional', 'celular',
            'mostrar_boton_entrega',
            'acepta_tratamiento_datos', 
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'readonly': 'readonly'}),
            'sobre_nosotros': forms.Textarea(attrs={'rows': 7}),
        }


class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['direccion', 'telefono', 'ciudad']

    def clean(self):
        cleaned_data = super().clean()
        direccion = cleaned_data.get("direccion")
        telefono = cleaned_data.get("telefono")
        ciudad = cleaned_data.get("ciudad")

        # Solo valida si tiene AL MENOS un campo con dato
        if not any([direccion, telefono, ciudad]):
            # Marca el form como sin cambios para que Django lo ignore
            self.cleaned_data = {}
            raise forms.ValidationError("Fila vacía ignorada")

        return cleaned_data


UbicacionFormSet = inlineformset_factory(
    Solicitud,
    Ubicacion,
    form=UbicacionForm,
    extra=1,
    can_delete=True,
)
class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['nombre', 'correo', 'telefono', 'foto', 'firma']
        widgets = {
            'foto': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'firma': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
