import csv
import logging
from datetime import datetime
from io import TextIOWrapper
from typing import Any, Dict

# from django.core.files.storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

from .models import Transaction


class CreateTransactionsSerializer(serializers.Serializer):
    transactions = serializers.FileField()

    def validate_transactions(self, value: InMemoryUploadedFile):
        extension = value.name.split(".")[-1]
        if extension != "csv":
            raise serializers.ValidationError(
                "Expected csv file with extension: '.csv', found file type of '.%s'"
                % extension
            )

        if value.multiple_chunks():
            raise serializers.ValidationError("CSV file is larger than 2.5 MB")

        try:
            # with default_storage.open(value.name) as file:
            file = TextIOWrapper(value, encoding="utf-8", newline="")
        except Exception as e:
            logging.error(e)
            raise serializers.ValidationError("CSV file is corrupt")

        return file

    @staticmethod
    def parse_date(date_str: str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

        return date_obj.date()

    @staticmethod
    def parse_type(trx_type: str):
        if trx_type.lower() not in ["income", "expense"]:
            return None

        return trx_type.lower()

    @staticmethod
    def parse_amount(amount: str):
        try:
            value = int(float(amount) * 100)
        except ValueError:
            return None
        return value

    @classmethod
    def create_transaction(cls, trx_row):
        if len(trx_row) < 4:
            return

        date = cls.parse_date(trx_row[0].strip())
        trx_type = cls.parse_type(trx_row[1].strip())
        amount = cls.parse_amount(trx_row[2].strip())
        memo = trx_row[3].strip()
        if not all((date, trx_type, amount, memo)):
            return None

        return Transaction(date=date, entry_type=trx_type, memo=memo, amount=amount)

    def save(self, **kwargs):
        transactions_file: list = self.validated_data["transactions"]
        csv_reader = csv.reader(transactions_file, delimiter=",")
        transactions_instances = []
        for transactions in csv_reader:
            trx = self.create_transaction(transactions)
            if trx:
                transactions_instances.append(trx)

        transactions = Transaction.objects.bulk_create(transactions_instances)
        logging.info("%s transactions created from uploaded file" % len(transactions))
        return transactions


class TransactionSerializer(serializers.ModelSerializer):
    memo_type = serializers.CharField()
    amount = serializers.FloatField(source="amount_in_dollar")

    class Meta:
        model = Transaction
        fields = "__all__"
