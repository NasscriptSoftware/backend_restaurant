from rest_framework import serializers
from .models import (
    NatureGroup,
    MainGroup,
    Ledger, 
    Transaction,
    ShareUsers,
    ShareUserTransaction,
    ProfitLossShareTransaction,
    CashCountSheet,

    )

class NatureGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NatureGroup
        fields = '__all__'

class MainGroupSerializer(serializers.ModelSerializer):
    nature_group = NatureGroupSerializer(read_only=True)  
    class Meta:
        model = MainGroup
        fields = '__all__'

class LedgerSerializer(serializers.ModelSerializer):
    group = MainGroupSerializer(read_only=True)  
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=MainGroup.objects.all(), write_only=True, source='group'
    )

    class Meta:
        model = Ledger
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    ledger_id = serializers.PrimaryKeyRelatedField(queryset=Ledger.objects.all(), source='ledger', write_only=True)
    ledger = LedgerSerializer(read_only=True)
    particulars_id = serializers.PrimaryKeyRelatedField(queryset=Ledger.objects.all(), source='particulars', write_only=True)
    particulars =  LedgerSerializer(read_only=True)
    class Meta:
        model = Transaction
        fields = '__all__'

#ShareManagement
class ShareUserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareUsers
        fields = ['id', 'name', 'mobile_no', 'category', 'profitlose_share', 'address']

def get_next_transaction_no():
    # Get the last transaction and increment the number
    last_transaction = ProfitLossShareTransaction.objects.order_by('-created_date').first()
    if last_transaction:
        last_transaction_no = last_transaction.transaction_no
        next_transaction_no = str(int(last_transaction_no) + 1)
    else:
        # If there are no transactions yet, start with 1
        next_transaction_no = '1'
    return next_transaction_no

class ShareUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareUsers
        fields = ['id', 'name', 'category']

class ShareUserTransactionSerializer(serializers.ModelSerializer):
    share_user = serializers.PrimaryKeyRelatedField(queryset=ShareUsers.objects.all()) 
    share_user_data = ShareUserSerializer(source='share_user', read_only=True)
    class Meta:
        model = ShareUserTransaction
        fields = ['share_user', 'share_user_data','profit_lose', 'percentage', 'amount']

class ProfitLossShareTransactionSerializer(serializers.ModelSerializer):
    share_user_transactions = ShareUserTransactionSerializer(many=True)

    class Meta:
        model = ProfitLossShareTransaction
        fields = [
            'transaction_no',
            'created_date',
            'period_from',
            'period_to',
            'status',
            'profit_amount',
            'loss_amount',
            'total_amount',
            'total_percentage',
            'share_user_transactions'
        ]
        read_only_fields = ('transaction_no',)  # Make transaction_no read-only

    def create(self, validated_data):
        # Generate the next transaction number
        transaction_no = get_next_transaction_no()
        validated_data['transaction_no'] = transaction_no
        
        share_users_data = validated_data.pop('share_user_transactions')
        transaction = ProfitLossShareTransaction.objects.create(**validated_data)
        
        # Calculate total_amount and total_percentage
        total_amount = sum(user_data['amount'] for user_data in share_users_data)
        total_percentage = sum(user_data['percentage'] for user_data in share_users_data)
        
        transaction.total_amount = total_amount
        transaction.total_percentage = total_percentage
        transaction.save()

        for share_user_data in share_users_data:
            ShareUserTransaction.objects.create(transaction=transaction, **share_user_data)
        
        return transaction

class CashCountSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashCountSheet
        fields = ['id', 'created_date', 'currency', 'nos', 'amount']


