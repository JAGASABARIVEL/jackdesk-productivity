# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # or IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django.db import transaction
from .models import DeviceLogin


@api_view(['POST'])
@permission_classes([AllowAny])  # or IsAuthenticated based on your app flow
def register_device(request):
    email = request.data.get("email")
    token = request.data.get("token")
    hostname = request.data.get("hostname")
    if not all([email, token, hostname]):
        return Response({"error": "Missing required fields."}, status=400)
    with transaction.atomic():
        # Remove previous device login by the same user (if any)
        DeviceLogin.objects.filter(email=email).exclude(hostname=hostname).delete()
        device, created = DeviceLogin.objects.update_or_create(
            hostname=hostname,
            defaults={"email": email, "token": token}
        )
        return Response({
            "status": "registered",
            "created": created,
            "device": {
                "hostname": device.hostname,
                "email": device.email,
                "token": device.token
            }
        })


@api_view(['DELETE'])
@permission_classes([AllowAny])  # or IsAuthenticated based on your app flow
def unregister_device(request):
    email = request.data.get("email")
    token = request.data.get("token")
    hostname = request.data.get("hostname")
    if not all([email, token, hostname]):
        return Response({"error": "Missing required fields."}, status=400)
    with transaction.atomic():
        # Remove previous device login by the same user (if any)
        DeviceLogin.objects.filter(email=email,hostname=hostname).delete()
        return Response({
            "status": "unregistered"
        }, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_device_credentials(request):
    hostname = request.query_params.get("hostname")

    if not hostname:
        return Response({"error": "Missing hostname."}, status=400)

    try:
        device = DeviceLogin.objects.get(hostname=hostname)
        return Response({
            "email": device.email,
            "token": device.token
        })
    except DeviceLogin.DoesNotExist:
        return Response({"error": "Device not registered."}, status=404)
