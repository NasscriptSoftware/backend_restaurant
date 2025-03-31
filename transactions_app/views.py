from rest_framework import viewsets,status
from django.db import transaction 
from django.db.models import Sum, Q
from datetime import datetime
from django.db.models import F, Min

from .models import (
    CashCountSheet,
    NatureGroup,
    MainGroup, 
    Ledger, 
    Transaction,
    ShareUsers
    )
from .serializers import (
     CashCountSheetSerializer,
     NatureGroupSerializer, 
     MainGroupSerializer, 
     LedgerSerializer, 
     TransactionSerializer,
     ShareUserManagementSerializer,
     ProfitLossShareTransaction,
     ProfitLossShareTransactionSerializer
     )
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.dateparse import parse_date
from rest_framework.exceptions import NotFound

class NatureGroupViewSet(viewsets.ModelViewSet):
    queryset = NatureGroup.objects.all()
    serializer_class = NatureGroupSerializer

class MainGroupViewSet(viewsets.ModelViewSet):
    queryset = MainGroup.objects.all()
    serializer_class = MainGroupSerializer

class LedgerViewSet(viewsets.ModelViewSet):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        transaction1_data = request.data.get('transaction1')
        transaction2_data = request.data.get('transaction2')

        if not transaction1_data or not transaction2_data:
            return Response({"error": "Both transaction1 and transaction2 are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate the next voucher number
        last_transaction = Transaction.objects.order_by('-voucher_no').first()
        next_voucher_no = (last_transaction.voucher_no + 1) if last_transaction else 1

        # Assign the generated voucher number to both transactions
        transaction1_data['voucher_no'] = next_voucher_no
        transaction2_data['voucher_no'] = next_voucher_no

        serializer1 = self.get_serializer(data=transaction1_data)
        serializer1.is_valid(raise_exception=True)
        self.perform_create(serializer1)

        serializer2 = self.get_serializer(data=transaction2_data)
        serializer2.is_valid(raise_exception=True)
        self.perform_create(serializer2)

        return Response(serializer1.data, status=status.HTTP_201_CREATED) 

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        
        self.perform_update(serializer)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def filter_by_voucher_no(self, request):
        voucher_no = request.query_params.get('voucher_no', None)
        if voucher_no is not None:
            transactions = self.queryset.filter(voucher_no=voucher_no)
            serializer = self.get_serializer(transactions, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "voucher_no parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=False, methods=['get'])
    def filter_transaction_by_transaction_type(self, request):
        transaction_type = request.query_params.get('transaction_type', None)
        
        if transaction_type:
            transactions = self.queryset.filter(transaction_type=transaction_type)
        else:
            transactions = self.queryset


        filtered_transactions = transactions.filter(
            id__in=transactions.values('voucher_no')
                              .annotate(min_id=Min('id'))
                              .values('min_id')
        )

        serializer = self.get_serializer(filtered_transactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def ledger_report(self, request):
        ledger_param = request.query_params.get('ledger', None)
        from_date = request.query_params.get('from_date', None)
        to_date = request.query_params.get('to_date', None)

        if not ledger_param:
            return Response([])

        # Determine if the parameter is a name or ID
        try:
            ledger_id = int(ledger_param)
            # If it converts to an integer, assume it's an ID
        except ValueError:
            # Otherwise, treat it as a name and fetch the ID
            ledger = Ledger.objects.filter(name=ledger_param).first()
            ledger_id = ledger.id if ledger else None

        if not ledger_id:
            return Response([])

        queryset = self.queryset.filter(ledger__id=ledger_id)

        if from_date:
            from_date = parse_date(from_date)
        if to_date:
            to_date = parse_date(to_date)

        if from_date and to_date:
            queryset = queryset.filter(date__range=(from_date, to_date))
        elif from_date:
            queryset = queryset.filter(date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(date__lte=to_date)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='filter-by-nature-group')
    def filter_by_nature_group(self, request):
        nature_group_name = request.query_params.get('nature_group_name', None)
        from_date = request.query_params.get('from_date', None)
        to_date = request.query_params.get('to_date', None)

        # Create a filter condition for nature_group_name
        filters = Q()
        if nature_group_name:
            filters &= Q(ledger__group__nature_group__name__iexact=nature_group_name)

        # Parse and apply the date range filter
        if from_date and to_date:
            from_date_parsed = parse_date(from_date)
            to_date_parsed = parse_date(to_date)

            if from_date_parsed and to_date_parsed:
                filters &= Q(date__range=(from_date_parsed, to_date_parsed))
            else:
                return Response([])  # Return empty response if dates are invalid
        else:
            return Response([])  # Return empty response if both dates are not provided

        # Fetch filtered transactions
        transactions = Transaction.objects.filter(filters)

        # Return empty if no transactions found
        if not transactions.exists():
            return Response([])

        # Serialize and return the filtered data
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='profit-and-loss')
    def profit_and_loss(self, request):
        from_date = request.query_params.get('from_date', None)
        to_date = request.query_params.get('to_date', None)

        # Date filters
        filters = Q()
        if from_date and to_date:
            from_date_parsed = parse_date(from_date)
            to_date_parsed = parse_date(to_date)

            if from_date_parsed and to_date_parsed:
                filters &= Q(date__range=(from_date_parsed, to_date_parsed))
            else:
                return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Both from_date and to_date are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Filter transactions for 'Expense' and 'Income'
        expense_transactions = Transaction.objects.filter(
            filters & Q(ledger__group__nature_group__name__iexact='Expense')
        )
        income_transactions = Transaction.objects.filter(
            filters & Q(ledger__group__nature_group__name__iexact='Income')
        )

        # Sum the debit_amount for 'Expense' transactions
        total_expense = expense_transactions.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0

        # Sum the credit_amount for 'Income' transactions
        total_income = income_transactions.aggregate(total_credit=Sum('credit_amount'))['total_credit'] or 0

        # Calculate net profit and loss
        net_profit = total_income - total_expense if total_income > total_expense else 0
        net_loss = total_expense - total_income if total_expense > total_income else 0

        return Response({
            'total_expense': total_expense,
            'total_income': total_income,
            'net_profit': net_profit,
            'net_loss': net_loss,
        })



#ShareManagement Section
class ShareUserManagementViewSet(viewsets.ModelViewSet):
    queryset = ShareUsers.objects.all()
    serializer_class = ShareUserManagementSerializer

class ProfitLossShareTransactionViewSet(viewsets.ModelViewSet):
    queryset = ProfitLossShareTransaction.objects.all()
    serializer_class = ProfitLossShareTransactionSerializer
    def get_queryset(self):
        queryset = ProfitLossShareTransaction.objects.all()
        transaction_no = self.request.query_params.get('transaction_no', None)
        if transaction_no:
            queryset = queryset.filter(transaction_no=transaction_no)
            if not queryset.exists():
                raise NotFound("Transaction not found")
        return queryset
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=201, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

class CashCountSheetViewSet(viewsets.ModelViewSet):
    serializer_class = CashCountSheetSerializer
    def get_queryset(self):
        queryset = CashCountSheet.objects.all()

        # Get the from_date and to_date parameters
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        if from_date and to_date:
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
                queryset = queryset.filter(
                    created_date__range=(from_date, to_date)
                )
            except ValueError:
                # Handle the case where the date format is incorrect
                return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        return queryset
    def create(self, request, *args, **kwargs):
        entries = request.data.get('entries', [])
        
        # Validate if entries is a list
        if not isinstance(entries, list):
            return Response({"error": "Invalid data format"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a list of serializers with the incoming data
        serializer = CashCountSheetSerializer(data=entries, many=True)
        
        # Validate the data
        if serializer.is_valid():
            # Save the data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)