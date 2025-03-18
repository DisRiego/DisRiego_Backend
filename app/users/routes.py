from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.users import schemas
from app.users.models import ChangeUserStatusRequest
from app.users.services import UserService
from app.auth.services import admin_required, get_current_user
from app.users.schemas import UpdateUserRequest, UserResponse, UserCreateRequest, ChangePasswordRequest, UserUpdateInfo, AdminUserCreateRequest, AdminUserCreateResponse
from typing import Optional, List

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/first-login-register", response_model=dict)
async def register_after_first_login(
    user_id: int = Form(...),
    country: str = Form(...),
    department: str = Form(...),
    municipality: int = Form(...),
    address: str = Form(...),
    phone: str = Form(...),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Completa el registro de usuario después del primer inicio de sesión.
    Se suben los datos de perfil básicos: país, departamento, municipio, 
    dirección, teléfono y opcionalmente una foto de perfil.
    """
    try:
        user_service = UserService(db)
        
        # Si se sube una foto de perfil, guardarla
        profile_picture_path = None
        if profile_picture:
            profile_picture_path = await user_service.save_profile_picture(profile_picture)
            
        # Actualizar el perfil del usuario
        result = await user_service.complete_first_login_registration(
            user_id=user_id,
            country=country,
            department=department,
            municipality=municipality,
            address=address,
            phone=phone,
            profile_picture=profile_picture_path
        )
        
        return result
    except HTTPException as e:
        raise e  # Re-lanzar excepciones HTTP ya manejadas
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al completar el registro del usuario: {str(e)}"
        )

@router.get("/profile/completion-status/{user_id}")
def check_profile_completion(user_id: int, db: Session = Depends(get_db)):
    """
    Verifica si el usuario ya ha completado su perfil después del primer login.
    util para decidir si mostrar el formulario de registro completo.
    """
    try:
        user_service = UserService(db)
        return user_service.check_profile_completion(user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar el estado del perfil: {str(e)}"
        )

@router.post("/update", response_model=dict)
def update_user(update: UpdateUserRequest, db: Session = Depends(get_db)):
    """
    Actualizar los detalles de un usuario.
    :param update: Datos del usuario a actualizar
    :param db: Dependencia de la base de datos
    :return: Mensaje de éxito o error
    """
    try:
        user_service = UserService(db)
        result = user_service.update_user(
            update.user_id,
            address=update.new_address,
            profile_picture=update.new_profile_picture,
            phone=update.new_phone,
            country=update.country,
            department=update.department,
            municipality=update.municipality
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"success": True, "message": "Usuario actualizado correctamente"}
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el usuario: {str(e)}")

@router.get("/{user_id}")
def list_user(user_id: int, db: Session = Depends(get_db)):
    """obtener informacion de un usuario"""
    try:
        user_service = UserService(db)
        return user_service.list_user(user_id)
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar el usuario: {str(e)}")
    
@router.get("/")
def list_users(db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.list_users()  
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar los usuarios: {str(e)}")
    
@router.get("/type-document/", tags=['type-document'])
def list_types_document(db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.get_type_documents()
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar los tipos de documentos: {str(e)}")
    
@router.post("/change-user-status/")
def change_user_status(request: ChangeUserStatusRequest, db: Session = Depends(get_db)):
    """Cambiar el estado de un usuario"""
    try:
        user_service = UserService(db)
        return user_service.change_user_status(request.user_id, request.new_status)
    except HTTPException as e:
        raise e  # Re-raise HTTPException for known errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el cambio de estado del usuario: {str(e)}")


@router.post("/create-user/")
def create_user(request: UserCreateRequest , db: Session = Depends(get_db)):
    try:
        user_service = UserService(db)
        return user_service.create_user(request)
    except Exception as e:
        raise HTTPException(status_code=500 , detail=f"Error al crear el usuario: {e}")
    
@router.post("/{user_id}/change-password", response_model=dict)
def change_password(user_id: int, request: ChangePasswordRequest, db: Session = Depends(get_db)):
    """
    Actualiza la contraseña del usuario verificando la contraseña actual.
    """
    try:
        user_service = UserService(db)
        return user_service.change_user_password(user_id, request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cambiar la contraseña: {str(e)}")
    
@router.put("/edit/{user_id}", summary="Editar información del usuario")
def edit_user(
    user_id: int,
    update_data: UserUpdateInfo,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Edita ciertos campos del usuario:
      - name, first_last_name, second_last_name,
      - type_document_id, document_number y date_issuance_document.
    
    Se permite solo si el usuario actual (extraído del token) tiene el permiso "editar_usuario".
    """
    required_permission = "editar_usuario"

    roles = current_user.get("rol", [])
    
    all_permissions = []
    for role in roles:
        permisos = role.get("permisos", [])
        all_permissions.extend(permisos)
    
    if not any(perm.get("name") == required_permission for perm in all_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para editar usuarios."
        )
    
    user_service = UserService(db)
    result = user_service.update_user(
        user_id,
        name=update_data.name,
        first_last_name=update_data.first_last_name,
        second_last_name=update_data.second_last_name,
        type_document_id=update_data.type_document_id,
        document_number=update_data.document_number,
        date_issuance_document=update_data.date_issuance_document,
        email=update_data.email
    )
    return result

@router.put("/location/{user_id}", summary="Editar información de ubicación del usuario")
def edit_user_location(
    user_id: int,
    update_data: UserUpdateInfo,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Edita la información de ubicación del usuario:
    - País
    - Departamento
    - Municipio
    - Dirección
    - Teléfono
    
    Requiere estar autenticado.
    """
    user_service = UserService(db)
    result = user_service.update_user_location(user_id, update_data)
    return result

@router.put("/edit-profile/{user_id}", response_model=dict)
async def edit_profile(
    user_id: int,
    country: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    municipality: Optional[int] = Form(None),
    address: Optional[str] = Form(None), 
    phone: Optional[str] = Form(None),
    profile_picture: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Editar información básica del perfil de usuario.
    Solo permite editar país, departamento, municipio, dirección, teléfono y foto de perfil.
    """
    try:
        user_service = UserService(db)
        
        # Validar el municipio si se proporciona
        if municipality is not None and (municipality < 1 or municipality > 37):
            raise HTTPException(
                status_code=400, 
                detail="El codigo de municipio debe estar entre 1 y 37"
            )
            
        # Procesar la imagen de perfil si se proporciona
        profile_picture_path = None
        if profile_picture:
            profile_picture_path = await user_service.save_profile_picture(profile_picture)
        
        # Actualizar solo los campos permitidos
        result = await user_service.update_basic_profile(
            user_id=user_id,
            country=country,
            department=department,
            municipality=municipality,
            address=address,
            phone=phone,
            profile_picture=profile_picture_path
        )
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el perfil: {str(e)}"
        )

@router.post("/admin/create", response_model=AdminUserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_data: AdminUserCreateRequest, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un nuevo usuario en el sistema.
    Solo accesible por administradores.
    
    Los campos requeridos son:
    - name: Nombres
    - first_last_name: Primer apellido
    - second_last_name: Segundo apellido
    - type_document_id: Tipo de documento
    - document_number: Número de documento
    - date_issuance_document: Fecha de expedición
    - birthday: Fecha de nacimiento
    - gender_id: Género
    - roles: Lista de roles asignados
    """
    # Verificar si el usuario actual tiene permisos de administrador
    admin_required(current_user)
    
    try:
        user_service = UserService(db)
        result = user_service.create_user_by_admin(
            name=user_data.name,
            first_last_name=user_data.first_last_name,
            second_last_name=user_data.second_last_name,
            type_document_id=user_data.type_document_id,
            document_number=user_data.document_number,
            date_issuance_document=user_data.date_issuance_document,
            birthday=user_data.birthday,
            gender_id=user_data.gender_id,
            roles=user_data.roles
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario: {str(e)}"
        )
        
@router.get("/admin/type-documents", tags=["Admin"])
def get_document_types(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtener todos los tipos de documentos disponibles"""
    # Verificar si el usuario actual tiene permisos de administrador
    admin_required(current_user)
    
    try:
        user_service = UserService(db)
        return user_service.get_type_documents()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los tipos de documentos: {str(e)}"
        )

@router.get("/admin/genders", tags=["Admin"])
def get_genders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Obtener todos los géneros disponibles"""
    # Verificar si el usuario actual tiene permisos de administrador
    admin_required(current_user)
    
    try:
        user_service = UserService(db)
        return user_service.get_genders()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener los géneros: {str(e)}"
        )
