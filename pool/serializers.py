from rest_framework import serializers
from .models import User, Order, OrderFlow, ShopProfile, CourierProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone_number', 'telegram_chat_id']
        read_only_fields = ['role']


class ShopProfileSerializer(serializers.ModelSerializer):
    telegram_chat_id = serializers.IntegerField(source='user.telegram_chat_id', read_only=True)

    class Meta:
        model = ShopProfile
        fields = ['id', 'shop_name', 'latitude', 'longitude', 'telegram_chat_id', 'created_at']


class CourierProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    telegram_chat_id = serializers.IntegerField(source='user.telegram_chat_id', read_only=True)

    class Meta:
        model = CourierProfile
        fields = [
            'id', 'username', 'telegram_chat_id',
            'is_online', 'live_latitude', 'live_longitude', 'location_updated_at'
        ]


class OrderFlowSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = OrderFlow
        fields = ['id', 'status', 'actor_name', 'timestamp']


class OrderSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source='shop.username', read_only=True)
    courier_name = serializers.CharField(source='courier.username', read_only=True)
    logs = OrderFlowSerializer(many=True, read_only=True)
    google_maps_link = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shop', 'shop_name', 'courier', 'courier_name',
            'delivery_address', 'latitude', 'longitude',
            'fee', 'package_amount', 'status',
            'telegram_group_message_id',
            'batch_parent', 'batch_offered_to', 'batch_offered_at',
            'google_maps_link',
            'created_at', 'updated_at', 'logs'
        ]
        read_only_fields = [
            'shop', 'courier', 'status',
            'telegram_group_message_id',
            'batch_parent', 'batch_offered_to', 'batch_offered_at',
            'created_at', 'updated_at'
        ]

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

        # ──────────────────────────────────────────────────
        # Yeni siparişi kurye havuzuna ve batch kontrolüne gönder
        # ──────────────────────────────────────────────────
        from pool.tasks import process_new_order
        # Sipariş 'READY' durumundaysa havuz algoritmasını başlat
        if order.status == Order.Status.READY:
            process_new_order.delay(order.id)
            
        return order

