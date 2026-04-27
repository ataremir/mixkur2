from django.db import transaction
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderFlow, User
from .serializers import OrderSerializer
from .permissions import IsShop, IsCourier, IsOrderOwner

class OrderViewSet(viewsets.ModelViewSet):
    """
    Sipariş yönetimi için merkezi ViewSet.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsShop()]
        if self.action in ['claim', 'list_ready']:
            return [IsCourier()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOrderOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.SHOP:
            # Dükkanlar sadece kendi siparişlerini görür
            return Order.objects.filter(shop=user)
        elif user.role == User.Role.COURIER:
            # Kuryeler tüm 'Hazır' siparişleri veya kendilerine atanmış olanları görür
            return Order.objects.filter(status__in=[Order.Status.READY, Order.Status.CLAIMED, Order.Status.ON_THE_WAY])
        return super().get_queryset()

    @action(detail=False, methods=['get'], url_path='ready')
    def list_ready(self, request):
        """
        Kuryelerin havuzdaki (Ready) siparişleri listeleyebileceği endpoint.
        """
        ready_orders = Order.objects.filter(status=Order.Status.READY)
        serializer = self.get_serializer(ready_orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='claim')
    def claim(self, request, pk=None):
        """
        Kuryenin siparişi havuzdan üstlenmesi (Claim).
        Race Condition Koruması: transaction.atomic ve select_for_update kullanılmıştır.
        """
        try:
            with transaction.atomic():
                # select_for_update() ilgili satırı DB seviyesinde kilitler (FOR UPDATE).
                # Bu sayede aynı anda istek atan diğer kuryeler bu satırın serbest kalmasını bekler.
                order = Order.objects.select_for_update().get(pk=pk)

                # Mantıksal kontrol: Sadece 'READY' durumundaki sipariş alınabilir.
                if order.status != Order.Status.READY:
                    return Response(
                        {"error": "Bu sipariş zaten başka bir kurye tarafından alınmış veya müsait değil."},
                        status=status.HTTP_409_CONFLICT
                    )

                # Siparişi kuryeye ata ve durumunu güncelle
                order.courier = request.user
                order.status = Order.Status.CLAIMED
                order.save()

                # Geçmiş kaydı (Audit Log)
                OrderFlow.objects.create(
                    order=order,
                    status=Order.Status.CLAIMED,
                    actor=request.user
                )

                return Response(OrderSerializer(order).data)

        except Order.DoesNotExist:
            return Response({"error": "Sipariş bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='set-ready')
    def set_ready(self, request, pk=None):
        """
        Dükkanın siparişi 'Hazır' (Havuza düşme) durumuna getirmesi.
        """
        order = self.get_object()
        if order.status != Order.Status.PREPARING:
            return Response({"error": "Sipariş hazır durumuna getirilemez."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.READY
        order.save()
        
        OrderFlow.objects.create(order=order, status=Order.Status.READY, actor=request.user)
        return Response(OrderSerializer(order).data)
