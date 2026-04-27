from rest_framework import serializers
from .models import User, Order, OrderFlow

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone_number']
        read_only_fields = ['role']

class OrderFlowSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = OrderFlow
        fields = ['id', 'status', 'actor_name', 'timestamp']

class OrderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.username', read_only=True)
    courier_name = serializers.CharField(source='courier.username', read_only=True)
    logs = OrderFlowSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shop', 'shop_name', 'courier', 'courier_name',
            'delivery_address', 'latitude', 'longitude', 'fee', 'status',
            'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = ['shop', 'courier', 'status', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Siparişi oluşturan dükkanı otomatik ata
        request = self.context.get('request')
        validated_data['shop'] = request.user
        order = super().create(validated_data)
        
        # İlk log kaydını oluştur
        OrderFlow.objects.create(
            order=order,
            status=order.status,
            actor=request.user
        )
        return order
