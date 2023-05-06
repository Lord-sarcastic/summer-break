import io
from datetime import date

from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from .models import MemoType, Transaction
from .serializers import CreateTransactionsSerializer


class TransactionModelTestCase(TestCase):
    def setUp(self):
        self.transaction_data = {
            "date": date.today(),
            "entry_type": Transaction.TransactionType.INCOME,
            "amount": 1000,
            "memo": "Memo",
        }

    def test_create_transaction(self):
        # Ensure that a new Transaction can be created with valid input data
        transaction = Transaction.objects.create(**self.transaction_data)
        self.assertIsNotNone(transaction.uuid)
        self.assertEqual(transaction.date, self.transaction_data["date"])
        self.assertEqual(transaction.entry_type, self.transaction_data["entry_type"])
        self.assertEqual(transaction.amount, self.transaction_data["amount"])
        self.assertEqual(transaction.memo, self.transaction_data["memo"])

    def test_amount_in_dollar(self):
        transaction = Transaction.objects.create(**self.transaction_data)
        self.assertEqual(transaction.amount_in_dollar, 10.0)

    def test_memo_type_will_identify_correct_type(self):
        transaction = Transaction.objects.create(**self.transaction_data)
        self.assertEqual(transaction.memo_type(), MemoType.EXPENSE_CATEGORY.value)
        transaction.memo = "123 Maple Dr"
        self.assertEqual(transaction.memo_type(), MemoType.JOB_ADDRESS.value)

    def test_memo_type_expense_category(self):
        transaction = Transaction(
            date=timezone.now().date(),
            entry_type=Transaction.TransactionType.EXPENSE,
            amount=50,
            memo="Office supplies",
        )
        self.assertEqual(transaction.memo_type(), MemoType.EXPENSE_CATEGORY.value)

    def test_get_report_will_generate_correct_reports(self):
        Transaction.objects.create(
            date=timezone.now().date(),
            entry_type=Transaction.TransactionType.INCOME,
            amount=1000,
            memo="123 Main St",
        )
        Transaction.objects.create(
            date=timezone.now().date(),
            entry_type=Transaction.TransactionType.INCOME,
            amount=2000,
            memo="456 Elm St",
        )
        Transaction.objects.create(
            date=timezone.now().date(),
            entry_type=Transaction.TransactionType.EXPENSE,
            amount=500,
            memo="Office supplies",
        )
        report = Transaction.get_report()
        self.assertEqual(report["expenses"], 5.0)
        self.assertEqual(report["gross-revenue"], 30.0)
        self.assertEqual(report["net-revenue"], 25.0)


class TransactionAPITestCase(APITestCase):
    def setUp(self):
        self.valid_csv_content = b"""
        2022-03-31,income,1000.0,Salary
        2022-03-31,expense,200.0,Transportation
        2022-03-31,income,500.0,Freelance"""
        self.invalid_csv_content = b"""
        2022-03-31,income,not_a_number,Salary
        2022-03-31,invalid_type,200.0,Transportation"""
        self.valid_csv_file = SimpleUploadedFile(
            "transactions.csv", self.valid_csv_content, content_type="text/csv"
        )
        self.invalid_csv_file = SimpleUploadedFile(
            "transactions.csv", self.invalid_csv_content, content_type="text/csv"
        )

    def test_parse_date_will_parse_date_correctly(self):
        self.assertEqual(
            CreateTransactionsSerializer.parse_date("2022-04-01"), date(2022, 4, 1)
        )
        self.assertIsNone(CreateTransactionsSerializer.parse_date("not_a_date"))

    def test_parse_type_will_work(self):
        self.assertEqual(CreateTransactionsSerializer.parse_type("income"), "income")
        self.assertEqual(CreateTransactionsSerializer.parse_type("Expense"), "expense")
        self.assertIsNone(CreateTransactionsSerializer.parse_type("invalid_type"))

    def test_parse_amount_will_work(self):
        self.assertEqual(CreateTransactionsSerializer.parse_amount("1000.0"), 100000)
        self.assertIsNone(CreateTransactionsSerializer.parse_amount("not_a_number"))

    def test_transaction_can_be_created_from_valid_csv_row(self):
        # Valid transaction row
        row = ["2022-03-31", "income", "1000.0", "Carpenter"]
        trx: Transaction = CreateTransactionsSerializer.create_transaction(row)
        self.assertEqual(trx.date, date(2022, 3, 31))
        self.assertEqual(trx.entry_type, "income")
        self.assertEqual(trx.amount, 100000)
        self.assertEqual(trx.memo, "Carpenter")

    def test_valid_csv_file_will_create_transactions(self):
        response = self.client.post(
            reverse("tax_report:transactions"),
            {"transactions": self.valid_csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 3)

    def test_transactions_will_not_be_created_from_invalid_csv(self):
        response = self.client.post(
            reverse("tax_report:transactions"),
            {"transactions": self.invalid_csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 0)

    def transactions_will_not_be_created_from_invalid_file_type(self):
        invalid_file = SimpleUploadedFile(
            "transactions.txt", b"some text", content_type="text/plain"
        )
        response = self.client.post(
            reverse("tax_report:transactions"),
            {"transactions": invalid_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["transactions"][0], "CSV file is corrupt")
        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 0)

    def transactions_will_not_be_created_from_large_file(self):
        large_csv = b"2022-03-28,income,123.45,Some memo\n" * 100000
        large_file = SimpleUploadedFile(
            "transactions.csv", large_csv, content_type="text/csv"
        )
        response = self.client.post(
            reverse("tax_report:transactions"),
            {"transactions": large_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["transactions"][0], "CSV file is larger than 2.5 MB"
        )

        transactions = Transaction.objects.all()
        self.assertEqual(transactions.count(), 0)
