from django.urls import path

from . import views

app_name = "tax_report"

urlpatterns = [
    path(
        "transactions/", views.CreateTransactionsAPIView.as_view(), name="transactions"
    ),
    path("report/", views.ReportsAPIView.as_view(), name="reports"),
]
