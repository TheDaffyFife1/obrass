from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from .roles import ADMIN_ROLE, RH_ROLE, USER_ROLE
from .models import UserProfile,Obra,Empleado,Puesto,Asistencia
from django.contrib.auth.decorators import login_required
from .RegistrationForm import RegistrationForm
from django.contrib.auth import login
from django.db import IntegrityError
from django.http import HttpResponseForbidden, HttpResponseRedirect,JsonResponse
from .RegistrationObra import ObraForm
from django.urls import reverse
from .FormAsignarObra import AsignarObraForm
from .FormEmpleado import EmpleadoForm
from django.core.serializers import serialize
import json
from django import forms
from django.views.decorators.http import require_POST
from datetime import datetime
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count


@login_required
def accesos(request):
    # Asumiendo que los roles son variables globales o están importados correctamente
    role = request.user.userprofile.role
    if role == ADMIN_ROLE:
        return redirect('admin_dashboard')
    elif role == RH_ROLE:
        return redirect('rh_dashboard')
    
    elif role == USER_ROLE:
        return redirect('user_asistencia')
    else:
        # Puedes redirigir a una página de error o a la página de inicio, etc.
        return redirect('default_page')

#Funciones para administrador  
@login_required
def admin_dashboard(request):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    return render(request, 'admin/admin_dashboard.html')

@login_required
def register(request):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Intenta crear el usuario y su perfil de usuario correspondiente
                user = form.save()  # Guarda la información del usuario
                user.refresh_from_db()  # Carga la instancia del usuario recién creada

                # Establece los atributos adicionales del usuario aquí si es necesario
                # user.profile.some_attribute = 'some_value'
                
                user.save()  # Guarda los cambios en el objeto de usuario

                # Verifica si ya existe un UserProfile para el usuario
                if not UserProfile.objects.filter(user=user).exists():
                    role = form.cleaned_data.get('role')
                    UserProfile.objects.create(user=user, role=role)  # Crea el perfil de usuario con el rol

                    login(request, user)  # Inicia sesión del usuario
                    return redirect('accesos')  # Redirecciona según el rol del usuario
                else:
                    # Si el UserProfile ya existe, podrías redireccionar al usuario a una página de error o de inicio
                    # O mostrar un mensaje de error en la misma página de registro
                    form.add_error(None, 'El usuario ya tiene un perfil asignado.')
            except IntegrityError as e:
                # Añade un mensaje de error al formulario si hay un error de integridad (por ejemplo, un duplicado)
                form.add_error(None, f'Ocurrió un error de integridad: {e}')
            
    else:
        form = RegistrationForm()
    
    return render(request, 'admin/registro.html', {'form': form})

@login_required
def crear_obra(request):
    """
    Vista para crear una nueva obra. Maneja solicitudes GET para mostrar el formulario y POST para procesar el formulario.
    """
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            form.save()
            # Reemplaza 'lista_obras' con el nombre de la ruta de la vista a la que deseas redirigir
            return redirect('lista_obras')
    else:
        form = ObraForm()  # Inicializa un formulario en blanco para solicitudes GET

    # Renderiza el template con el formulario, sea nuevo o con errores
    return render(request, 'admin/registro_obra.html', {'form': form})

@login_required
def lista_obras(request):
    """
    Vista para listar todas las obras registradas en la base de datos.
    """
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    obras = Obra.objects.all()  # Recupera todas las obras
    return render(request, 'admin/lista_obras.html', {'obras': obras})

@login_required
def cambiar_estado_obra(request, obra_id):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    obra = Obra.objects.get(id=obra_id)
    obra.activa = not obra.activa
    obra.save()
    return HttpResponseRedirect(reverse('lista_obras'))

@login_required
@require_POST  # Asegura que esta vista solo acepte solicitudes POST
def eliminar_obra(request, obra_id):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")

    obra = get_object_or_404(Obra, id=obra_id)
    obra.delete()
    
    # Reemplaza request.is_ajax() con la comprobación del encabezado HTTP_X_REQUESTED_WITH
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Obra eliminada correctamente'})
    else:
        return HttpResponseRedirect(reverse('lista_obras'))

    
@login_required
def editar_obra(request, obra_id):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    obra = get_object_or_404(Obra, id=obra_id)
    if request.method == 'POST':
        form = ObraForm(request.POST, instance=obra)
        if form.is_valid():
            form.save()
            return redirect('lista_obras')
    else:
        form = ObraForm(instance=obra)
    return render(request, 'admin/editar_obra.html', {'form': form, 'obra': obra})

@login_required
def asignar_obra_a_usuario(request, user_profile_id):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    user_profile = get_object_or_404(UserProfile, pk=user_profile_id)
    if request.method == 'POST':
        form = AsignarObraForm(request.POST, instance=user_profile)
        if form.is_valid():
            # Asegúrate de que el usuario es RH o User antes de guardar
            if user_profile.role in [RH_ROLE, USER_ROLE]:
                form.save()
                return redirect('lista_user_profiles')
            else:
                # Manejar el caso en que el rol no es permitido para la asignación
                pass  # Puedes redirigir o mostrar un mensaje de error
    else:
        form = AsignarObraForm(instance=user_profile)

    return render(request, 'admin/asignar_obra.html', {'form': form, 'user_profile': user_profile})

@login_required
def lista_user_profiles(request):
    if request.user.userprofile.role != ADMIN_ROLE:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")
    # Si deseas filtrar por roles específicos, puedes hacerlo aquí
    user_profiles = UserProfile.objects.filter(role__in=[RH_ROLE, USER_ROLE])
    return render(request, 'admin/lista_user_profiles.html', {'user_profiles': user_profiles})


#Funciones para RH
@login_required
def rh_dashboard(request):
    user_profile = request.user.userprofile
    if user_profile.role == RH_ROLE:
        # Asumiendo que 'obra_id' es un campo en el modelo de UserProfile para el ID de la obra.
        obra_id = user_profile.obra_id
        if obra_id:
            obra = get_object_or_404(Obra, id=obra_id)
            # Puedes pasar 'obra' al contexto si la plantilla necesita mostrar información sobre la obra
            return render(request, 'rh/rh_dashboard.html', {'obra': obra})
        else:
            # Manejar el caso de que no haya un ID de obra asociado
            return HttpResponseForbidden("Este usuario de RH no tiene una obra asignada.")
    else:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

@login_required
def lista_empleados(request):
    user_profile = request.user.userprofile
    if user_profile.role == RH_ROLE:
        # Asumiendo que 'obra_id' es un campo en el modelo de UserProfile para el ID de la obra.
        obra_id = user_profile.obra_id
        if obra_id:
            obra = get_object_or_404(Obra, id=obra_id)
            # Puedes pasar 'obra' al contexto si la plantilla necesita mostrar información sobre la obra
            empleados = Empleado.objects.filter(obra_id=obra)
            return render(request, 'rh/lista_empleados.html', {'empleados': empleados, 'obra': obra})
        else:
            # Manejar el caso de que no haya un ID de obra asociado
            return HttpResponseForbidden("Este usuario de RH no tiene una obra asignada.")
    else:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

@login_required
def crear_empleado(request):
    user_profile = request.user.userprofile
    if user_profile.role == RH_ROLE:
        obra_id = user_profile.obra_id
        if obra_id:
            if request.method == 'POST':
                form = EmpleadoForm(request.POST, request.FILES)
                if form.is_valid():
                    empleado = form.save(commit=False)
                    # Establece la obra al empleado antes de guardar
                    empleado.obra_id = obra_id
                    empleado.save()
                    return redirect('lista_empleados')
            else:
                # Inicializa el formulario con la obra del usuario RH
                form = EmpleadoForm(initial={'obra': obra_id})
                # Oculta el campo 'obra' ya que no queremos que sea editable
                form.fields['obra'].widget = forms.HiddenInput()
            
            sueldos_base = {str(puesto.id): str(puesto.sueldo_base) for puesto in Puesto.objects.all()}
            sueldos_base_json = json.dumps(sueldos_base)
            
            return render(request, 'rh/registro_empleados.html', {
                'form': form,
                'sueldos_base': sueldos_base_json,  # Pass 'sueldos_base' as JSON to the template
            })
        else:
            return HttpResponseForbidden("Este usuario de RH no tiene una obra asignada.")
    else:
        return HttpResponseForbidden("No tienes permiso para ver esta página.") 
    
@login_required
def editar_empleado(request, empleado_id):

    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('lista_empleados')  # Asume que tienes esta vista y URL definidas
    else:
        form = EmpleadoForm(instance=empleado)
    
    return render(request, 'rh/editar_empleado.html', {'form': form, 'empleado': empleado})

def reporte_asistencia(request):
    # Obtener todos los registros de asistencia
    asistencias = Asistencia.objects.all()
    
    # Número fijo de días trabajados a la semana, ajusta esto según tu necesidad
    dias_trabajados_por_semana = 6
    
    # Agregar el sueldo diario a cada registro de asistencia
    for asistencia in asistencias:
        # Suponiendo que 'sueldo' es un campo en el modelo 'Empleado'
        # y que todos los empleados trabajan la misma cantidad de días.
        asistencia.sueldo_diario = asistencia.empleado.sueldo / dias_trabajados_por_semana

    # Pasar los registros de asistencia al contexto, incluyendo el sueldo diario
    context = {'asistencias': asistencias}
    
    # Renderizar la plantilla HTML con los datos proporcionados
    return render(request, 'rh/reporte_asistencia.html', context)

#Funciones para Supervisor
@login_required
def user_asistencia(request):
    user_profile = request.user.userprofile
    if user_profile.role == USER_ROLE:
        obra_id = user_profile.obra_id
        if obra_id:
            obra = get_object_or_404(Obra, id=obra_id)
            # La lógica para mostrar la asistencia del usuario en la obra
            return render(request,'supervisor/user_asistencia.html', {'obra': obra})
        else:
            # Manejar el caso de que no haya un ID de obra asociado
            return HttpResponseForbidden("Este usuario no tiene una obra asignada.")
    else:
        return HttpResponseForbidden("No tienes permiso para ver esta página.")

@login_required
def progreso_obras(request):
    objetos = Obra.objects.all()
    hoy = now()
    labels = []
    data = []

    for objeto in objetos:
        tiempo_total = (objeto.fecha_fin - objeto.fecha_inicio).days
        tiempo_transcurrido = (hoy.date() - objeto.fecha_inicio).days 
        
        porcentaje_transcurrido = (tiempo_transcurrido / tiempo_total) * 100 if tiempo_total else 0
        porcentaje_transcurrido

        labels.append(objeto.nombre)  # Agrega el nombre de la obra a la lista de etiquetas
        data.append(abs(int(porcentaje_transcurrido))) # Agrega el porcentaje de progreso a la lista de datos

    return JsonResponse({'labels': labels, 'data': data})

@login_required
def asistencia_obras(request):
    # Asumiendo que tienes un campo que identifica cada día único de asistencia, por ejemplo 'fecha'
    obras_con_asistencias = Obra.objects.annotate(
        total_asistencias=Count('empleado__asistencia', distinct=True),
        total_empleados=Count('empleado', distinct=True)
    )

    # Calcular el porcentaje de asistencias por obra
    obras_data = []
    for obra in obras_con_asistencias:
        # Asumiendo que cada empleado debería haber asistido cada día
        dias_laborales = obra.total_asistencias / obra.total_empleados if obra.total_empleados else 0
        porcentaje = (obra.total_asistencias / (obra.total_empleados * dias_laborales) * 100) if dias_laborales else 0
        obras_data.append({
            'obra_nombre': obra.nombre,
            'porcentaje_asistencia': porcentaje
        })

    # Retorna la información en formato JSON
    return JsonResponse({'obras': obras_data})

@login_required
def obras_con_empleados(request):
    # Suponiendo que tienes un modelo 'Obra' y un modelo 'Empleado' con una FK a 'Obra'
    todas_las_obras = Obra.objects.prefetch_related('empleado_set').all()

    # Construye un diccionario para cada obra con su lista de empleados
    data = [
        {
            'obra_id': obra.id,
            'obra_nombre': obra.nombre,
            'empleados': [
                {
                    'empleado_id': empleado.id,
                    'empleado_nombre': empleado.nombre,
                    'empleado_puesto_id': empleado.puesto.id,
                }
                for empleado in obra.empleado_set.all()
            ]
        }
        for obra in todas_las_obras
    ]

    return JsonResponse({'obras': data})

@login_required
def progreso_obras_indivual(request):
    objetos = Obra.objects.all()
    hoy = now()
    labels = []
    data = []
    resto = []

    for objeto in objetos:
        tiempo_total = (objeto.fecha_fin - objeto.fecha_inicio).days
        tiempo_transcurrido = (hoy.date() - objeto.fecha_inicio).days 
        
        porcentaje_transcurrido = (tiempo_transcurrido / tiempo_total) * 100 if tiempo_total else 0
        restante = 100 - abs(porcentaje_transcurrido) 
        
        labels.append(objeto.nombre)  # Agrega el nombre de la obra a la lista de etiquetas
        data.append(abs(int(porcentaje_transcurrido))) # Agrega el porcentaje de progreso a la lista de datos
        resto.append(int(restante))


    return JsonResponse({'labels': labels, 'data': data, 'resto': resto})