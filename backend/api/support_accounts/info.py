from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from rest_framework_simplejwt.tokens import RefreshToken
from dispatcher.models import User, DualFactorRequest, Payments, Notify, Activity, TransferRequest
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Sum
from dispatcher.permission import ProfiatDefaultUser, permissions
from rest_framework.decorators import api_view, permission_classes
import logging



@api_view(['POST'])
@permission_classes([ProfiatDefaultUser])
def get_account_info(request):

    user = request.user

    payments = Payments.objects.filter(user=user).order_by('-date_created')[:5]

    recent_activities = Activity.objects.filter(user=user).order_by('-date_created')[:5]

    payments_mas = []
    recent_activities_mas = []

    for payment in payments:
        payments_mas.append({
            'id': payment.id,
            'amount': int(payment.amount),
            'status': payment.status,
            'detail': payment.card_number,
            'paymethod': payment.paymethod.paymethod_description,
            'date_created': payment.date_created.timestamp(),
            'date_closed': payment.date_closed.timestamp() if payment.date_closed else None,
        })

    for recent_activity in recent_activities:
        recent_activities_mas.append({
            'date_created' : recent_activity.date_created.timestamp() if recent_activity.date_created else '-',
            'type' : recent_activity.type,
            'text' : recent_activity.text
        })

    graph_monthly_data = []
    graph_weekly_data = []

    delta = timedelta(days=30)

    graph = Payments.objects.filter(date_created__gte=datetime.now().date() - delta, user=user)

    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    for single_date in daterange(datetime.now().date() - delta, datetime.now().date()):
        data = graph.filter(date_created__gte=single_date, date_created__lte=single_date + timedelta(days=1))
        graph_monthly_data.append({
            'date' : single_date.strftime("%d-%m-%Y"),
            'Сумма выплат' : int(data.aggregate(Sum('amount'))['amount__sum']) if data.count() else 0,
            'Количество выплат' : data.count()
        })

    for single_date in daterange(datetime.now().date() - timedelta(days=7), datetime.now().date()):
        data = graph.filter(date_created__gte=single_date, date_created__lte=single_date + timedelta(days=1))
        graph_weekly_data.append({
            'date' : single_date.strftime("%d-%m-%Y"),
            'Сумма выплат' : int(data.aggregate(Sum('amount'))['amount__sum']) if data.count() else 0,
            'Количество выплат' : data.count()
        })

    active_transfers = TransferRequest.objects.filter(user=request.user, status__in=['in_progress', 'created', 'wait_auth'])
    active_payments = Payments.objects.filter(user=request.user, status__in=['created', 'in_progress'])

    frozen_balance = 0
    if active_transfers.exists():
        frozen_balance += active_transfers.aggregate(amount=Sum('amount'))['amount']

    if active_payments.exists():
        frozen_payments = active_payments.aggregate(amount=Sum('amount'), fee_amount=Sum('fee_amount'))
        frozen_balance += frozen_payments['amount'] + frozen_payments['fee_amount']


    data={
        'account' : {
            # 'balance' : '{:.2f}'.format(float(frozen_transfers + frozen_payments)),
            'balance': {
                'total' : float(request.user.balance),
                'available' : float(request.user.balance) - float(frozen_balance),
                'frozen' : float(frozen_balance) 
            },
            'currency' : 'RUB',
            'username' : request.user.username,
            'avatar' : 'https://google.com',
            'email' : request.user.my_email
        },
        'payments' : payments_mas,  
        'recent_activities' : recent_activities_mas,

        'graph' : {
            'weekly' : graph_weekly_data,
            'monthly' : graph_monthly_data
        }
    }

    return Response(status=status.HTTP_200_OK, data=data)
